# SCORE
SCORE (Synthesis od COnsists as Rolling Energy micro-grids) is a web-based application that enables the exploration and trade-offs that exist in complex system of consists, routes, and powering policies used by the Class 1 railroad system.

## Background
SCORE is a comprehensive set of open source tools tailored to the modeling oenergy trades that can be provided to industry and organizations developing advanced energy solutions, to evaluate their efficacy in teh context of a *transportation system*. Yet open source software tools do not exist to eplore and evaluate advanced energy and powering technologies that can reduce environmental impacts at an acceptabel cost. Current data for rail lines, locomotives, and rail cars is industry owned and controlled, hindering access to historical costs, emissions, and traffic. Existing Longitudinal Train Dynamics (LTD) models are not open source, and are not tailored for energy analysis. SCORE provides an Energy Longitudinal Train Dynamics (E-LTD) model that treats the train or consist as a rolling micro-grid, capable of managing energy flows from the complex network of sources and sinks.

## Installation
The source code for the SCORE tools are stored in the Github repository. It includes a default database with a number of routes and consists already included in it.

SCORE is a web-based application. A web browser provides access to the backend server. The details for setting up a local server are given below.

* Install docker-desktop. Goto to https://www.docker.com/products/docker-desktop/ and follow the instructions for your platform. docker-desktop is available for Mac, Windows, and Linux. If installing on a Windows machine, you will also want(need?) to install and configure WSL2. See https://docs.docker.com/desktop/install/windows-install/ for details.

* Clone the repository. From the command prompt on your desired system (WSL2 Ubuntu prompt on windows), clone the repository. Git is already part of Mac, Linux and WSL2 Ubuntu.

* Build and start the development containers. Change directory to "score". It should have the docker-compose.yml file in it. In this directory enter "docker compose up -d --build". The first time you execute this command it will take a few minutes to load all of the images onto your computer. This will build the images and then start them. It will also populate the database with soem initial route and consist data.

* There is a "production" version of the docker-compose file included. This file adds gunicorn to execute the Django code NGINX to route requests to static reousrces and to gunicorn for the dyanmic sources. These containers are built using "docker compose -f docker-compose.prod.yml build". They can then be started with "docker compose -f docker-compose.prod.yml up -d" The "-d" option makes the processes start in the background. 

* Access the server with a web browser. It this point you should be able to go to the login page by simply entering the URL "localhost:8000" into you web browser. Most of our testing has used Chrome.

* Shutdown the server. From the command prompt that started docker-compose you can enter "docker-compose down -v". This will gracefully shut things down and remove any changes that were made or added to the database. If you would like the database to persist, do not include the "-v" option while shutting it down.


### Notes:
If no changes are made to the docker-compose.yml or corresponding Dockerfile for each of the containers, there is no need to include the "--build" option for subsequent start-ups.

If you want to save your database to share with others or for backup, from the command line in the directory that has the docker-compose.yml file enter "docker-compose exec db pg_dump locomotives > db.sql" then replace the existing db.sql file with this new one by moving it to db/docker-entrypoint-initdb.d/data

If you want to see more about what is going on with the docker containers enter "docker-compose logs -f". This will display the logs from all of the containers as they are running - the output to each of their stdout.

### Limitations:
The web server used in this implementation is for development use only. It is the one provided by Django (the python-based web application server used). If you are viewing the logs, you will see each request get logged. This is because it is running in "debug" mode. 
Since the server is running in debug mode, it is possible to make changes to the python code and have them immediately take effect without restarting. Once the file is saved, the server will automatically restart.

## REST API
The web-server portion of the application takes advantage of a REST API that was created using the Django Rest Framework. There are 2 files located in score/utility that give examples of how to connect to the REST api usign either Python or Matlab. One of the key elements of both examples is the need to get an Authorization Token first by passing a userid and password. The Python example is in "notebook" format for use in an interactive session for data analysis such as with Pandas, but it can easily be modified as needed.

## Acknowledgements
This research was supported by Dr. Robert Ledoux from ARPA-E as part of the LOCOMOTIVES research program.