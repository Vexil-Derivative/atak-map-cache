import requests
import csv
import json
import utils
import zipfile
import os
from pathlib import Path
from shapely.geometry import shape
from fastkml import kml

def get_links(link,actualCount,maxCount, index=0, links=[]):
  """
  Turns a single link into a list of links based on the number of objects it contains versus
  the number of objects that can be returned by the API. Only used if more than 1 link is required,
  so we multiply by 4 just to be account for uneven distrobution of locations. 

  Returns: A list of links to download
  """
  req_divisions = round(actualCount / maxCount, 0)
  # Distribution of points is rarely even across the country, so might as well aim high
  divisions = int(req_divisions * 8)

  # Roughly 33 lon degrees between 
  offset = 54 / divisions
  lon = -125
  top_lat = 49.35
  bot_lat = 24.39
  for i in range(0, divisions):
    lst_geom = [str(lon), str(bot_lat), str(lon+offset), str(top_lat)]
    geom = ','.join(lst_geom)
    print(geom)
    links.append(link + f'/query?&where=1=1&geometryType=esriGeometryEnvelope&geometry={geom}&inSR=4326&spatialRel=esriSpatialRelContains&outFields=*&f=kmz')
    lon = lon + offset
  utils.debug('Appending link - index: ' + str(index))
  
  utils.debug('Links: ' + str(links))
  utils.debug('Number of Links: ' + str(len(links)))
  return links

  
def download(links, name, layer, download_enabled=False):
  """
  Downloads a single or list of links and names appropriately. 

  Return: A list of file paths created

  download arg is just for dev/troubleshooting, setting it to false will skip redownloading the
  files. Script will fail if they do not already exist.
  """
  if type(links) == str:
      url = link+'/query?where=1=1&outFields=*&f=kmz'
      if download_enabled:
        with open('cache/kmz/' + name + '.kmz', 'wb') as output:
          r = requests.get(url)
          output.write(r.content)
  elif type(links) == list:
    i = 1
    paths = []
    for link in links:
      path = 'cache/temp/' + name + '_layer' + str(layer) + '_part_' + str(i) + '.kmz'
      paths.append(path)
      if download_enabled:
        with open(path, 'wb') as output:
          r = requests.get(link)
          output.write(r.content)
      i = i + 1
    print('Paths = ' + str(paths))
    return paths

def print_child_features(element):
    """ Prints the name of every child node of the given element, recursively """
    if not getattr(element, 'features', None):
        return
    for feature in element.features():
        print(feature.name)
        print_child_features(feature)

def merge(paths):
    """
    Merges multiple KML files into 1 file based on a list of paths.
    """
    lst_children = []
    lst_styles = []
    if len(paths) == 1:
       # We should skip the merge process if we only have 1 path
       pass
    
    os.system('rm -r ' + 'cache/temp/' + name)
    os.system('mkdir ' + 'cache/temp/' + name)

    i = 0
    for path in paths:
        folder_path = path.split('.')[0]

        os.system('cp ' + folder_path + '/*.png ' + 'cache/temp/' + name)
        os.system('cp ' + folder_path + '/*.xsl ' + 'cache/temp/' + name)
    
        with zipfile.ZipFile(path, 'r') as zip_ref:
            zip_ref.extractall(folder_path)
        with open(folder_path + '/doc.kml', 'r') as kml_file:
            kml_text = kml_file.read().encode('utf-8')

        k = kml.KML()
        k.from_string(kml_text)

        k_doc = list(k.features())[0]
        k_styles = list(k_doc.styles())
        for style in k_styles:
           style.id = style.id + 'pt' + str(i)
           lst_styles.append(style)

        try:
            for features in list(k_doc.features()):
                for feature in list(features.features()):
                  feature.styleUrl = feature.styleUrl + 'pt' + str(i)
        except TypeError:
           pass
        for doc_child in list(k_doc.features()):
            lst_children.append(doc_child)
        i = i + 1
        
    k = kml.KML()
    ns = '{http://www.opengis.net/kml/2.2}'
    # We use the ID, Name, Description from the last KML file. 
    # Since they should always be the same, there's no need to
    # merge them
    document = kml.Document(ns, k_doc.id, k_doc.name, k_doc.description, lst_styles)
    for child in lst_children:
        document.append(child)
    k.append(document)


    final_kml_text = k.to_string(prettyprint=True)
    output = Path('cache/temp/' + name + "/doc.kml")
    #output.write_text(final_kml_text)
    output.write_bytes(final_kml_text.encode('utf-8'))
    zip_kml(name)

def zip_kml(name):
    """
    Takes the name of a folder and zips the contents into a .kmz
    """
    with zipfile.ZipFile('cache/temp/' + name + '.kmz', 'w', zipfile.ZIP_DEFLATED) as zip:
        os.chdir('cache/temp/' + name)
        for filename in os.listdir('.'):
            zip.write(filename)
        os.chdir('../../..')
        os.system('cp cache/temp/' + name + '/' + filename + ' cache/kmz/' + filename)

    



with open('links.csv', newline='') as linksfile:
  reader = csv.reader(linksfile, delimiter=',', quotechar='"')
  for row in reader:
    link = row[0]
    layers = row[1].split()
    name = row[2]
    paths = []

    for layer in layers:
        # Get max count to compare to actual count
        max_count_url = link + '?f=pjson'
        r = requests.get(max_count_url)
        max_count = json.loads(str(r.content, 'utf-8'))['maxRecordCount']
        utils.debug('Max Count for ' + name + ' = ' + str(max_count))

        url = link + '/' + layer + '/query?where=1=1&outFields=*&returnCountOnly=true&f=json'
        r = requests.get(url)
        actual_count = json.loads(str(r.content, 'utf-8'))['count']
        utils.debug('Actual Count for ' + name + ' = ' + str(actual_count))
        if actual_count > max_count:
            links = get_links(link + '/' + layer,actual_count,max_count)
        paths.extend(download(links, name, layer))

    merge(paths)
      

