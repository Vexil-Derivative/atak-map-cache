import requests
import json
import utils
import hashlib
import os
import zipfile
from datetime import datetime
from html import unescape
from pathlib import Path
from pykml.factory import KML_ElementMaker as KML
from pykml import parser
from lxml import etree, objectify
from classes import CotDP

def traffic_cams():
    export = requests.get('https://511wi.gov/api/v2/get/cameras?key=043964c85d7640f29133e6a48c0fd449').content
    dp = CotDP('WI_511_Cameras')

    for cam in json.loads(export):
        cam_id = hashlib.md5(cam["Id"].encode()).hexdigest()
        cot = dp.make_cot(cam_id, 'b-m-p-s-p-loc', cam['Name'], cam['Latitude'], cam['Longitude'])
        dp.add_to_manifest(cam_id)
        dp.add_video_sensor(cot, cam['VideoUrl'])
        dp.write_cot(cot, f'cache/cot/{dp.man_name}/cot/{cam_id}.cot')

    dp.write_manifest(f'cache/cot/{dp.man_name}/MANIFEST/mainfest.xml')
    dp.zip()

def message_signs(name, url):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    export = requests.get(url).content
    tld = KML.kml(KML.Document(
        KML.name(name),
        KML.description("Test"),
        KML.Style(
            KML.IconStyle(
                KML.Icon(KML.href('https://quickmap.dot.ca.gov/img/cms32x32.png')),
                KML.hotSpot(x='0.5', y='0.5', xunits='fraction', yunits='fraction')
            ),
            KML.LabelStyle(
                KML.scale(0)
            ),
            id="ms"
        )
    ))

    tlf = KML.Folder(KML.name("Message Signs"), KML.description("Description")) 
    for sign in json.loads(export):
        msg = sign["Messages"][0].replace('\n', '<br>').replace('\t', '&#9;')
        tld.Document.append(KML.Placemark(
            KML.name(sign['Name']),
            KML.description(r"""
<![CDATA[
    <style>
        @font-face{font-family:'Scoreboard';src:url(https://quickmap.dot.ca.gov/ca511dfp/scoreboard.ttf) format('truetype')}
        .cms{min-width:306px;width:fit-content;min-height:105px;height:fit-content;margin:.1em;background-color:#000;text-align:center;white-space:pre}
        .cms1{color:orange;font-family:Scoreboard,Courier New;font-size:35px;line-height:35px}
        .cms2{color:orange;font-family:Scoreboard,Courier New;font-size:35px;line-height:35px}
    </style>                

    <div class='cms_container'>
        <div class='cms cms1'>%s</div>
        <div style='display: none;' class='cms cms2'><br><br></div>
    </div>
    <p class="update-stamp">Last updated: %s</p>
    ]]>
                            """ % (msg, timestamp)),
            KML.styleUrl("#ms"),
            KML.Point(
                KML.coordinates(str(sign['Longitude']) + ',' + str(sign['Latitude'])))
            )
        )
    #tld.Document.append(tlf)
    objectify.deannotate(tld, xsi_nil=True)
    etree.cleanup_namespaces(tld)

    parser.Schema("ogckml22.xsd").assertValid(tld)
    assert(parser.Schema("kml22gx.xsd").validate(tld))
    final_kml_text = etree.tostring(tld, pretty_print=True )
    output = Path('/opt/map-cache/cache/temp/messagesigns/doc.kml')
    output.write_bytes(final_kml_text)
    with open('/opt/map-cache/cache/temp/messagesigns/doc.kml', 'w', encoding='utf-8') as outputfile:
        outputfile.write(unescape(final_kml_text.decode()))
    with zipfile.ZipFile('/opt/map-cache/cache/kmz/WI_511_MessageSigns.kmz',
                         'w', zipfile.ZIP_DEFLATED) as zip:
        os.chdir('/opt/map-cache/cache/temp/messagesigns/')
        zip.write('doc.kml')

if __name__ == '__main__':
    traffic_cams()
    message_signs("WI_511_Messagesigns", "https://511wi.gov/api/v2/get/messagesigns?key=043964c85d7640f29133e6a48c0fd449")
