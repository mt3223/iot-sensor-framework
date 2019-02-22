# RFID Data Collection & Visualization Software

This software suite contains scripts to collect and visualize RFID tag
information using an Impinj Speedway RFID reader.

*Note: These instructions assume that the web server, interrogation and
visualizer will be run on the same machine (IP addresses in all shell scripts
have been set to `localhost`).

### Requirements
The following software packages need to be installed before running RFID
data collection. You will have to use the same install method (such as
`pip install` or `easy_install`) listed here. Also, alternatives to using
`sudo` for `pip install` are  `sudo -H pip install <package-name>` or
`pip install --user <package-name>`.

MySQL:
```
sudo apt-get install mysql-server-5.5
sudo mysql_secure_installation
sudo mysql_install_db
```

Other packages:
```
sudo apt-get install libmysqlclient-dev
sudo apt-get install python-dev
sudo pip install flask
sudo pip install MySQL-python
sudo apt-get install libcurl4-openssl-dev
sudo apt-get install libssl-dev
sudo apt-get install libffi-dev
export PYCURL_SSL_LIBRARY=openssl
sudo pip install pycurl --global-option="--with-openssl"
sudo pip install pycrypto
sudo pip install python-dateutil
sudo pip install httplib2
sudo pip install twisted
sudo pip install service_identity
sudo apt-get install python-matplotlib
sudo apt-get install libblas-dev liblapack-dev libatlas-base-dev gfortran
pip install scipy

# for client packages
sudo pip install pandas
sudo easy_install pykalman
sudo easy_install filterpy
sudo pip install statsmodels
sudo pip install scikit-learn
sudo apt-get install libfreetype6-dev libpng3
sudo pip install --upgrade pip
sudo pip install --upgrade filterpy # this upgrades numpy / scipy stack
sudo pip install git+https://github.com/ajmendez/PyMix.git
```

### Instructions (Running framework on localhost for testing/development)
Start the following components in the order presented below.
Note that some scripts may be in a scripts/ subdirectory.

#### Set up
Use a separate command window or tab for each of the following:

###### Start MySQLd
MySQL v5.7:
```
mysqld
```
MySQL v5.5 (Raspberry Pi):
```
sudo service mysql start
```
###### Web Server
Navigate to `rssi_db/`:
* Run `./server_mysql.sh` (for use with the interrogator and MySQL) or
`./server.sh` (for a SQLite instance when running processing modules)

###### RFID Interrogator
Navigate to `interrogator/` and run either of the following:
* `client_r1000.sh` to use the Impinj Speedway R1000 RFID Reader
* `client_r420.sh` to use Impinj Speedway R420 RFID Reader

#### Shutdown
1. In the command window running the visualizer, type 'q' and press enter.
1. Type 'q' and press enter to terminate the web server.
1. Type 'q' and press enter to terminate the interrogator.
1. Run `killall mysqld` to terminate MySQL.

#### Export to .db file
Before running the following, make sure MySQL and webserver are running.
* Navigate to `rssi_db/`
* Run `./export_mysql_to_sqlite.sh`
* This will create a database file named 'out.db1' in the current working
directory with data from the MySQL database.

#### Convert .db file to .csv
* Rename the output db file to `database.db`
```
mv out.db1 database.db
```
* Run: `./retrieve_wholedb_json.sh`
* This will create a file named `out.csv`. This file contains the collected RFID
tag data.

#### Remove collected data from MySQL database and re-initialize database
* Run: `./destroy_mysql.sh`. When prompted for a password, press enter.
* Run: `./initialize_mysql.sh`.

#### Run a processing module
* Change into the `fusionframework_v1` directory (or `fusionframework_v2` or
other processing unit as appropriate)
* Run `./simulate.sh sensor_test.TestSensor` (replace with
`sensor_your.YourSensor` for a YourSensor class written into the sensor_your.py
file)

## Data Export Instructions
Following instructions below to export the collected data. Ensure shutdown steps
listed above have been completed before proceeding to export data:
1. Export MySQL database to SQL database: `./export_mysql_to_sqlite.sh`.
2. You will now have a file named `out.db1` in your working directory. If you
would like to export db files, proceed to step 6.
3. Rename db file: `mv out.db1 database.db`
4. Convert db file to csv: `./retrieve_wholedb_json.sh`.
5. You will now have a csv file named `out.csv` in your working directory.
6. Copy your desired file (either `out.db1` or `out.csv`) from the server
Raspberry Pi to the Bellyband laptop by running the following on the Bellyband
Laptop:
    1. Open a terminal window.
    2. Navigate to your desired directory. For example, a folder on the Desktop:
    `cd ~/Desktop/data_dir`.
    3. Run:
    ```
    scp pi@192.168.0.105:/home/pi/rssi_db/<desired_file> .
    ```
    Where `<desired_file>` is either `out.db1` or `out.csv`.
7. Rename your data file, for example: `mv out.csv breathing_30.csv`
8. Copy the file to a USB drive to export to your personal computer.

You have now completed data collection and export.
If you are done with data collection, close all terminal windows on the
Bellyband laptop by typing `exit` and pressing enter (for Raspberry Pi
terminals, you will need to do this twice for terminal window to close).
Shutdown the laptop by clicking the gear icon on the top right and selecting
shutdown. Finally, power down all devices at the RFID setup.

## Troubleshooting
* **Interrogator script hangs**: If the interrogator script hangs after quitting
or during data collection, do the following to kill the interrogator process:
    1. Press CTRL+Z
    1. Find the interrogator process ID: `ps -a`. The process ID will be listed
    next to `./client_r420.py` or something similar.
    1. Once you have obtained the process ID, kill it using
    `kill -9 <process_id>` (where `<process_id>` is the process ID you
    determined in the previous step without the angular brackets).

----

## Containerization
*TODO*: This section should be considered WIP. Add updates to this section until
the full software stack is capable or independently running containerized.

### Software Requirements
1. [Docker](https://www.docker.com/products/docker-engine)
2. [Docker Compose](https://docs.docker.com/compose/)

### Using the Containers
#### Container Build & Startup
```
$ docker-compose build
$ docker-compose up
```

#### Container Shutdown
```
$ docker-compose down
```

## Development Guidelines
### Formatting Python
Install the `autopep8` code formatting tool.
```
pip install autopep8
```
Run the following command from within the root directory of the repository.
```
autopep8 --in-place --recursive .
```
In the future we may want to use the `--aggressive` option to make
non-whitespace style changes.

## License
Copyright <YEAR> Bill Mongan

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to 
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies 
of the Software, and to permit persons to whom the Software is furnished to do 
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all 
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR 
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER 
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN 
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.