# atak-map-cache

**NOTE**: This repository is in very early development stages. There is no documentation and the code is not production ready. Use at your own peril. If you are a **public safety** worker and you'd like to use the data found here, please open an issue and list the data you're hoping to use. I can likely create a customized KMZ for you that includes the same data and doesn't require ongoing use of this tool to get updates.

The purpose of this repo is to provide tools that pull GIS data from government GIS servers and cache them locally for use in ATAK. Many feature overlays available from GIS servers have a limit on the number of items that can be pulled at once, so they require using multiple links to get all the data. Since KMZ exports don't properly support paging, splitting the data by ID or bounding box is required.

Eventually, this repo will be used to build a release of files and network links for adding to ATAK. At this time, it only includes the tools required to build the files yourself.

## Purpose

Many of the most popular paid mapping apps use freely available GIS data for the majority of the maps they provide. Some of these sources can be directly integrated with ATAK, but there is little support for organization and styling the maps. Additionally, some of these data sources have poor uptimes, meaning they may not be available when you need them. AMC provides a method for pulling the data, organizing it into a small number of top level files, and styling the data for consistency and ease of use.

## Roadmap

- [x] Sorting by state and/or layer
- [x] Add multiple links to a single KMZ file
- [x] Vector KMZ export support
- [] Raster KMZ export support
- [] geoJSON export support
- [] Feature server + Image server link downloads
- [] Set update frequency per-datasource
- [] Add custom styling adjustments per source
- [] "Network link" mode for critical applications
- 
## Use

The `links.json` file contains all of the data sources that will be converted by the script. They are organized into `files`, `links`, and `layers`. Each `file` entry represents a single KMZ file in the export, which contains folders for each `link`. Each `link` can contain multiple `layers`, which will each get their own subfolder if `sort_by_layer` is set to true. The `sort_by_state` option will further divide the data into individual US States, helpful for datasets with large numbers of objects.

Different ArcGIS server implementations support different methods of data export. For vector data, KMZ export is the most tested/reliable method, but initial support for geoJSON exports is being developed. Raster data support is on the way, but you may be better served by simply using the WMS/WMTS/XYZ services offered by the source. 

## Credits

Special thanks to Joseph Elfelt for his work finding and organizing government GIS servers and methodologies for exporting data from them. Many of the data sources were found on his list of public GIS servers, and as such can not be used for commercial use without written permission. You can find his work at [https://mappingsupport.com](https://mappingsupport.com)
