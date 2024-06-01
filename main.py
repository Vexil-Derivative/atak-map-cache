import requests
import csv
import json
import utils
import zipfile
import os
from pathlib import Path
from shapely.geometry import shape
from fastkml import kml
from geopy.geocoders import Nominatim
from coord_lookup import Lookup

lookup = Lookup()


geolocator = Nominatim(user_agent="geoapiExcercises")

def get_links(link,actualCount,maxCount, index=0, links=[]):
  """
  Turns a single link into a list of links based on the number of objects it contains versus
  the number of objects that can be returned by the API. Only used if more than 1 link is required,
  so we multiply by 4 just to be account for uneven distrobution of locations. 

  Returns: A list of links to download
  """
  req_divisions = round(actualCount / maxCount, 0)
  # Distribution of points is rarely even across the country, so might as well aim high
  divisions = int(req_divisions * 3)


  # Roughly 54 lon degrees between east and west ends of continental US
  offset = round(54 / divisions, 1)

  lon = -125
  top_lat = 49.35
  bot_lat = 24.39
  for i in range(0, divisions):
    lst_geom = [str(lon), str(bot_lat), str(lon+offset), str(top_lat)]
    geom = ','.join(lst_geom)
    links.append(link + f'/query?&where=1=1&geometryType=esriGeometryEnvelope&inSR=4326&geometry={geom}&spatialRel=esriSpatialRelEnvelopeIntersects&outFields=*&f=kmz')
    lon = lon + offset

  utils.debug('Number of links generated: ' + str(len(links)))
  return links
 
  
def download(links, name, layer, download_enabled=False):
    """
    Downloads a single or list of links and names appropriately. 

    Return: A list of file paths created

    download arg is just for dev/troubleshooting, setting it to false will skip redownloading the
    files. Script will fail if they do not already exist.
    """
    paths = []
    if isinstance(links, str):
        url = links + '/' + str(layer) + '/query?where=1=1&outFields=*&f=kmz'
        path = 'cache/temp/' + name + '/' + name + '_layer' + str(layer) + '.kmz'
        paths.append(path)
        if download_enabled:
            with open('cache/temp/' + name + '/' + name + '_layer' + str(layer) + '.kmz', 'wb') as output:
                r = requests.get(url)
                output.write(r.content)
    elif type(links) == list:
        i = 1

        for link in links:
            r = 0
            path = 'cache/temp/' + name + '/' + name + '_layer' + str(layer) + '_part_' + str(i) + '.kmz'
            paths.append(path)
            if download_enabled:
                with open(path, 'wb') as output:
                    utils.debug('Downloading part ' + str(i) + ' of ' + str(len(links)))
                    r = requests.get(link)
                    output.write(r.content)

        i = i + 1

    return paths

def print_child_features(element):
    """ Prints the name of every child node of the given element, recursively """
    if not getattr(element, 'features', None):
        return
    for feature in element.features():
        print(feature.name)
        print_child_features(feature)

def merge(paths, layers):
    """
    Merges multiple KMZ files into 1 file based on a list of paths.
    """
    name_set = set()
    lst_styles = []
    dct_features = {}
    feature_count = 0
    if len(paths) == 1:
       # TODO: We should skip the merge process if we only have 1 path
       pass
    
    os.system('rm -r ' + 'cache/temp/' + name + '/final')
    os.system('mkdir ' + 'cache/temp/' + name + '/final')

    i = 0
    for path in paths:
        folder_path = path.split('.')[0]
    
        with zipfile.ZipFile(path, 'r') as zip_ref:
            zip_ref.extractall(folder_path)

        os.system('cp ' + folder_path + '/*.png ' + 'cache/temp/' + name + '/final/ 2>/dev/null')
        os.system('cp ' + folder_path + '/*.xsl ' + 'cache/temp/' + name + '/final/ 2>/dev/null')

        with open(folder_path + '/doc.kml', 'r') as kml_file:
            kml_text = kml_file.read().encode('utf-8')

        k = kml.KML()
        k.from_string(kml_text)

        k_doc = list(k.features())[0]
        k_styles = list(k_doc.styles())
        for style in k_styles:
           style.id = style.id + 'pt' + str(i)
           lst_styles.append(style)

        if link_obj["sort_by_layer"]:
            utils.debug("Appending layer " + str(i) + " to dct_features")
            dct_features = append_to_layers(dct_features, k_doc, layers[i], feature_count, i)

        if link_obj["sort_by_state"]:
            try:
                for feature in list(list(k_doc.features())[0].features()):
                    lon = feature.geometry.x
                    lat = feature.geometry.y
                    state = lookup.state(lat, lon)
                    feature.styleUrl = feature.styleUrl + 'pt' + str(i)
                    # Can't get the API to stop returning duplicates, so we check manually
                    if feature.name not in name_set:
                        try:
                            dct_features[state].append(feature)
                            feature_count = feature_count + 1
                            name_set.add(feature.name)
                        except KeyError:
                            dct_features[state] = []
                            dct_features[state].append(feature)
                            feature_count = feature_count + 1
                            name_set.add(feature.name)

                    if (feature_count % 100 == 0):
                        print(str(feature_count) + ' features processed')

            except AttributeError:
                for feature in list(list(k_doc.features())[0].features()):
                    if feature.geometry.geom_type == 'LineString':
                        # Grab the first point in the line for categorization
                        lon = feature.geometry.coords[0][0]
                        lat = feature.geometry.coords[0][1]
                    elif feature.geometry.geom_type == 'MultiLineString':
                        # Grab the lower left corner of the bounding box since it's 
                        # easier than parsing out the lines
                        lon = feature.geometry.bounds[1]
                        lon = feature.geometry.bounds[0]
                    try:
                        state = lookup.state(lat, lon)
                    except UnboundLocalError:
                        # Some KML maps don't need to be split by state, i.e. they don't have POIS, just shapes (weather)
                        pass
                    feature.styleUrl = feature.styleUrl + 'pt' + str(i)
                    # Can't get the API to stop returning duplicates, so we check manually

                    if feature.name not in name_set:
                        try:
                            dct_features[state].append(feature)
                            feature_count = feature_count + 1
                            name_set.add(feature.name)
                        except KeyError:
                            dct_features[state] = []
                            dct_features[state].append(feature)
                            feature_count = feature_count + 1
                            name_set.add(feature.name)
        

                if (feature_count % 100 == 0):
                    print(str(feature_count) + ' features processed')
            except TypeError:
                pass

        i = i + 1
    if link_obj["sort_by_state"]:    
        utils.debug("Combining States")
        kml_doc = combine_states(dct_features, k_doc, lst_styles)
    
    elif link_obj["sort_by_layer"]:
        utils.debug("Combining layers")
        kml_doc = combine_layers(dct_features, k_doc, link_obj, lst_styles, layers)

    final_kml_text = kml_doc.to_string(prettyprint=True)
    output = Path('cache/temp/' + name + "/final/doc.kml")
    output.write_bytes(final_kml_text.encode('utf-8'))
    zip_kml(name)


def append_to_layers(dct_features, k_doc, layer, feature_count, i):
    """ Adds a list of features to a 'layer' object in dct_features. """
    for feature in list(list(k_doc.features())[0].features()):
        feature.styleUrl = feature.styleUrl + 'pt' + str(i)
        try:
            dct_features[layer].append(feature)
            feature_count = feature_count + 1

        except KeyError:
            dct_features[layer] = []
            dct_features[layer].append(feature)
            feature_count = feature_count + 1
    return(dct_features)


def combine_states(features, k_doc, lst_styles):
    """ Turns a dictionary of multiple states into 1 KML object with separate folders for each state. """
    a = kml.KML()
    ns = '{http://www.opengis.net/kml/2.2}'
    # We use the ID, Name, Description from the last KML file. 
    # Since they should always be the same, there's no need to
    # merge them
    parent_doc = kml.Document(ns, k_doc.id, name, k_doc.description, lst_styles)
    a.append(parent_doc)
    for state in features:
        state_folder = kml.Folder(ns, k_doc.id, state, k_doc.description, lst_styles)
        for mark in features[state]:
            state_folder.append(mark)
            #print(list(state_folder.features()))
        parent_doc.append(state_folder)


def combine_layers(features, k_doc, link_obj, lst_styles, layers):
    """ Turns a dictionary of multiple layers into 1 kml object with 1 folder per layer """
    a = kml.KML()
    ns = '{http://www.opengis.net/kml/2.2}'
    # We use the ID, Name, Description from the last KML file. 
    # Since they should always be the same, there's no need to
    # merge them
    parent_doc = kml.Document(ns, k_doc.id, name, k_doc.description, lst_styles)
    a.append(parent_doc)
    i = 0
    for layer_obj in features:
        layer_folder = kml.Folder(ns, k_doc.id, name + link_obj["layer_names"][str(layers[i])], k_doc.description, lst_styles)
        for mark in features[layer_obj]:
            layer_folder.append(mark)
            #print(list(state_folder.features()))
        parent_doc.append(layer_folder)
        i = i + 1
    return a

def make_top_level_doc(folders, folder_cfg, name, description, lst_styles):
    tld = kml.KML()
    ns = '{http://www.opengis.net/kml/2.2}'
    parent_doc = kml.Document(ns, name, name, description, lst_styles)
    tld.append(parent_doc)
    i = 0
    for folder in folders:
        top_level_folder = kml.Folder(ns, folder_cfg[i]["name"], folder_cfg[i]["name"], folder_cfg[i]["description"], lst_styles)
        for obj in folders[folder]:
            top_level_folder.append(obj)
        parent_doc.append(layer_folder)
        i = i + 1
    return a


def zip_kml(name):
    """
    Takes the name of a folder and zips the contents into a .kmz
    """
    with zipfile.ZipFile('cache/temp/' + name + '.kmz', 'w', zipfile.ZIP_DEFLATED) as zip:
        os.chdir('cache/temp/' + name + '/final')
        for filename in os.listdir('.'):
            zip.write(filename)
        os.chdir('../../../..')
        os.system('mv cache/temp/' + name + '.kmz' + ' cache/kmz/')
        #os.system('rm -r cache/temp/' + name + '*')

    


if __name__ == "__main__":

    with open('links.json', 'r') as linksfile:
        for ind_file in json.load(linksfile)["files"]:
            lst_link = ind_file["links"]
            parent_kmz = ind_file["name"]

            for link_obj in lst_link:
                link = link_obj["link"]
                layers = link_obj["layers"]
                name = link_obj["name"]
                try:
                    layer_names = link_obj["layer_suffix"]
                except KeyError:
                    pass
                paths = []

                os.system('mkdir -p ' + 'cache/temp/' + name)
                if link_obj["enabled"]:
                    for layer in layers:
                        # Get max count to compare to actual count
                        max_count_url = link + '?f=pjson'
                        r = requests.get(max_count_url)
                        max_count = json.loads(str(r.content, 'utf-8'))['maxRecordCount']
                        utils.debug('Max Count for ' + name + ' = ' + str(max_count))

                        url = link + '/' + str(layer) + '/query?where=1=1&outFields=*&returnCountOnly=true&f=json'
                        r = requests.get(url)
                        actual_count = json.loads(str(r.content, 'utf-8'))['count']
                        utils.debug('Actual Count for ' + name + ' = ' + str(actual_count))
                        if actual_count > max_count:
                            links = get_links(link + '/' + layer,actual_count,max_count)
                            paths.extend(download(links, name, layer))
                        else:
                            paths.extend(download(link, name, layer))
                        

                    if len(paths) > 0:
                        merge(paths, layers)


            

