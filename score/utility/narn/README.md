Included in this directory is a Dockerfile and docker-copose.yml file to create a Jupyter lab
instance with Geopandas tools for manipulating and analyzing data from the NARN database.

The *.geojson file is not included with the git repository because it is so large (added *.geojson to the .igtgnore file). It can be retrieved by accessing the Bureau of Transportation Statistics website at:
https://geodata.bts.gov/datasets/usdot::north-american-rail-network-lines/about and downloading the geojson file format. This file gets updated multiple times a day. opy the file into the notebooks directory.

To build the container simply use a "docker compose build" and to run it "docker compose up".
Normally, I would recommend usign the '-d' option but in this case we want to see the output. When the container starts up, it will list a url to provide access to the Jupyter interface. Simply click on this url to open it up in your preferred browser. When you are done, you can hit "crtl-c" a few times as needed to stop the process. youc an also stop the container from the Docker desktop interface.