# atak-map-cache

**NOTE**: This repository is in very early development stages. There is no documentation and the code is not production ready. Use at your own peril.

The purpose of this repo is to provide tools that pull GIS data from government GIS servers and cache them locally for use in ATAK. Many feature overlays available from GIS servers have a limit on the number of items that can be pulled at once, so they require using multiple links to get all the data. Since KMZ exports don't properly support paging, splitting the country into sections with bounding boxes is required. 

Eventually, this repo will be used to build a release of files and network links for adding to ATAK. At this time, it only includes the tools required to build the files yourself. 
