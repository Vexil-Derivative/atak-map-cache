from pykml import parser
from pykml.factory import KML_ElementMaker as KML
from lxml import etree, objectify
import json
import os
from pathlib import Path

def aqi(path, name):
    aqi_sev = {
        "1": "Good",
        "2": "Moderate",
        "3": "Unhealthy for Sensitive Groups",
        "4": "Unhealthy",
        "5": "Very Unhealthy",
        "6": "Hazardous"
    }
    aqi_styles = [
        KML.Style(
            KML.LineStyle(
                KML.color("ffffff00"),
                KML.width(.2)
            ),
            KML.PolyStyle(
                KML.color("aa00E53D"),
                KML.colorMode("normal"),
                KML.fill(1),
                KML.outline(1)
            ),
            id = 'Poly1'
        ),
        KML.Style(
            KML.LineStyle(
                KML.color("ffffff00"),
                KML.width(.2)
            ),
            KML.PolyStyle(
                KML.color("aa45fafd"),
                KML.colorMode("normal"),
                KML.fill(1),
                KML.outline(1)
            ),
            id = 'Poly2'
        ),
        KML.Style(
            KML.LineStyle(
                KML.color("ffffff00"),
                KML.width(.2)
            ),
            KML.PolyStyle(
                KML.color("aa65a4ff"),
                KML.colorMode("normal"),
                KML.fill(1),
                KML.outline(1)
            ),
            id = 'Poly3'
        ),
                KML.Style(
            KML.LineStyle(
                KML.color("ffffff00"),
                KML.width(.2)
            ),
            KML.PolyStyle(
                KML.color("aa594cfe"),
                KML.colorMode("normal"),
                KML.fill(1),
                KML.outline(1)
            ),
            id = 'Poly4'
        ),
                KML.Style(
            KML.LineStyle(
                KML.color("ffffff00"),
                KML.width(.2)
            ),
            KML.PolyStyle(
                KML.color("aa814db7"),
                KML.colorMode("normal"),
                KML.fill(1),
                KML.outline(1)
            ),
            id = 'Poly5'
        ),
                KML.Style(
            KML.LineStyle(
                KML.color("ffffff00"),
                KML.width(.2)
            ),
            KML.PolyStyle(
                KML.color("aa664d81"),
                KML.colorMode("normal"),
                KML.fill(1),
                KML.outline(1)
            ),
            id = 'Poly6'
        )
    ]
    with open(path, 'r') as f:
        data = json.load(f)
    parent_folder = KML.Folder(KML.name(name), KML.description("description"))
    for feature in data['features']:
        geom = feature['geometry']
        status = feature['attributes']['gridcode']
        feature_name = feature['attributes']['Id']
        coord_str = ""
        #for ring in geom['rings']:
        for point in geom['rings'][0]:
            coord_str = coord_str + '\n' + str(point[0]) + ',' + str(point[1])
        poly = KML.Placemark(KML.name(feature_name),
                                KML.description(aqi_sev[str(status)]),
                                KML.styleUrl(f"#Poly{status}"),
                                KML.Polygon(KML.extrude('1'),
                                            KML.altitudeMode('clampToGround'),
                                            KML.outerBoundaryIs(KML.LinearRing(KML.coordinates(coord_str)))))
        parent_folder.append(poly)
    doc = KML.kml(KML.Document(
        KML.name(name)
    ))
    for kmlstyle in aqi_styles:
        doc.Document.append(kmlstyle)
    for x in parent_folder.findall('.//{http://www.opengis.net/kml/2.2}Placemark'):
        doc.Document.append(x)
    return(doc)


def geojson_to_kml(path, name):
    with open(path, 'r') as f:
        data = json.load(f)
    parent_folder = KML.Folder(KML.name(name), KML.description("description"))
    for feature in data['features']:
        geom = feature['geometry']
        geom_type = geom['type']
        if geom_type == 'Polygon':
            #print(geom["coordinates"])
            coord_str = ""
            for point in geom["coordinates"][0]:
                coord_str = coord_str + '\n' + str(point[0]) + ',' + str(point[1])
            try:
                feature_name = feature["properties"]["NAME"]
            except KeyError:
                feature_name = feature["properties"]["Id"]

            try:
                poly = KML.Placemark(KML.name(feature_name),
                                 KML.description(feature['properties']['STATEFP']),
                                KML.styleUrl("#Poly1"),
                                KML.Polygon(KML.extrude('1'),
                                            KML.altitudeMode('clampToGround'),
                                            KML.outerBoundaryIs(KML.LinearRing(KML.coordinates(coord_str)))
                                            ))
            except KeyError:
                poly = KML.Placemark(KML.name(feature_name),
                                    KML.styleUrl("#Poly1"),
                                    KML.Polygon(KML.extrude('1'),
                                                KML.altitudeMode('clampToGround'),
                                                KML.outerBoundaryIs(KML.LinearRing(KML.coordinates(coord_str)))
                                    ))

            parent_folder.append(poly)
        #elif geom_type == 'MultiPolygon':
        #    #print(geom["coordinates"])
        #    coord_str = ""
        #    for point in geom["coordinates"][0]:
        #        coord_str = coord_str + '\n' + str(point[0]) + ',' + str(point[1])
        #    poly = KML.Placemark(KML.name(feature["properties"]["NAME"]),
        #                         KML.description(feature['properties']['STATEFP']),
        #                        KML.styleUrl("#Poly1"),
        #                        KML.MultiPolygon(KML.extrude('1'),
        #                                    KML.altitudeMode('clampToGround'),
        #                                    KML.outerBoundaryIs(KML.LinearRing(KML.coordinates(coord_str)))
        #                                    ))
        #    parent_folder.append(poly)
        elif geom_type == 'LineString':
            pass
            KML.Placemark(KML.name(feature["properties"]["NAME"]), 
                                KML.Polygon(KML.extrude('1'),
                                            KML.altitudeMode('relativeToGround'),
                                            KML.coordinates(geom["coordinates"][0])))
        elif geom_type == 'Point':
            KML.Placemark(KML.name(feature["properties"]["NAME"]),
                        KML.Point(
                        #KML.coordinates(feature["coordinates"][0])))
                        KML.coordinates(geom["coordinates"][0])))
        else:
            print("ERROR: unknown type:", geom_type)
    #write_kml(parent_folder)
    doc = KML.kml(KML.Document(
        KML.name(name),
        KML.Style(
            KML.LineStyle(
                KML.color("ffffffff"),
                KML.width(.2)
            ),
            KML.PolyStyle(
                KML.color("01ffffff"),
                KML.colorMode("normal"),
                KML.fill(1),
                KML.outline(1)
            ),
            id = 'Poly1'
        )
    ))
    for x in parent_folder.findall('.//{http://www.opengis.net/kml/2.2}Placemark'):
        doc.Document.append(x)
    return(doc)

def write_kml(folder):
    kml_doc = KML.Document(
        KML.name("Test"),
        KML.description("Desc")
    )
    kml_doc.append(folder)
    name_escaped = 'US_Counties/US_Counties.kml'
    objectify.deannotate(kml_doc, xsi_nil=True)
    etree.cleanup_namespaces(kml_doc)

    parser.Schema("ogckml22.xsd").assertValid(kml_doc)
    assert(parser.Schema("kml22gx.xsd").validate(kml_doc))
    #final_kml_text = kml_doc.to_string(prettyprint=True)
    final_kml_text = etree.tostring(kml_doc, pretty_print=True)
    output = Path('cache/temp/' + name_escaped)
    output.write_bytes(final_kml_text)


if __name__ == "__main__":
   geojson_to_kml('cache/temp/US_Counties/US_Counties_layer0_part_2.geoJSON', "Test")