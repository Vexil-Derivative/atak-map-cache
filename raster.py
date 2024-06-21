from fastkml import kml
import simplekml
import os

def load_kml():
    with open('snow_depth/doc.kml', 'r') as kml_file:
        kml_text = kml_file.read().encode('utf-8')

        k = simplekml.Kml()
        k.parsetext(kml_text)
        feat = k
        print(k)

if __name__ == "__main__":
    command = """gdallocationinfo 'WMS:http://demo.opengeo.org/geoserver/gwc/service/wms?SERVICE=WMS&VERSION=1.1.1&
                            REQUEST=GetMap&LAYERS=og%3Abugsites&SRS=EPSG:900913&
                            BBOX=-1.15841845090625E7,5479006.186718751,-1.1505912992109375E7,5557277.703671876&
                            FORMAT=png&TILESIZE=256&OVERVIEWCOUNT=25&MINRESOLUTION=0.0046653459640220&TILED=true' \
                           -geoloc -11547071.455 5528616 -xml -b 1"""
    os.system(command)