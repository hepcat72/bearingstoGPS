# bearingstoGPS.py

Robert Leach
4/27/2024

Given a starting GPS coordinate (longitude and lattitude), convert a series of bearings and distances into GPS coordinates.

## About

I wrote this script in order to convert bearings and distances from my grandfather's deed into GPS coordinates that I could paste into a kml (keyhole markup language) file so I could update parcel shapes to a Google MyMaps map and drag it around to identify the official parcel.  See my [stack exchange post](https://gis.stackexchange.com/questions/480402/) on the topic.

## Install

### Clone the repository
```
git clone https://github.com/hepcat72/bearingstoGPS.git
cd bearingstoGPS
```
### Create a virtual environment

Create a virtual environment (from a bash shell) and activate it, for example:
```
python3 -m venv .venv
source .venv/bin/activate
```
### Install dependencies
```
python -m pip install -U pip  # Upgrade pip
python -m pip install -r requirements/dev.txt  # Install requirements
```
## Usage
```
$ python bearingstogps.py -h
usage: bearingstogps [-h] --infile INFILE --lon LON --lat LAT [--distance-units {feet,poles,rods}]

Given a starting GPS coordinate (longitude and lattitude), convert a series of bearings and distances into a line or shape

optional arguments:
  -h, --help            show this help message and exit
  --infile INFILE       File of a series of bearings and distances describing a 'line' or 'shape'.  Required headers: ['bearing', 'distance'].  All distances must be in feet.
                        
                        Example:
                        
                        	# Comment lines begin with "#".  Header line required:
                        	bearing	distance	comment
                        	north 77° 15' 00" east	103.75	case insensitive cardinal directions allowed.  Tip: put landmarks in an extra column.
                        	S 46° 59' 26" E	95	Extra columns are ignored.  Abbreviations are OK.
                        	S 33 10 3 E	50	Non-digit characters in the angle are ignored.  The numbers just have to be in order of degrees(°), minutes('), and seconds(").
                        	N 22.1d E	60	Minutes and seconds are optional, but if seconds are supplied, degrees and minutes must be supplied.
                        	S	5.7	Due south/north/east/west needs no degrees.
                        	340 55 03	5.7	North is assumed if the first value is a number.
                        
  --lon LON             Longitude of the starting coordinate, associated with the source of the first bearing and distance in --infile.
  --lat LAT             Latitude of the starting coordinate, associated with the source of the first bearing and distance in --infile.
  --distance-units {feet,poles,rods}, --units {feet,poles,rods}
                        Distance units that distances in --infile are in, so that they will be converted to the required unit (feet).  [1 pole/rod = 16.5 feet.]
```
