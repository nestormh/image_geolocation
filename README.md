# image_geolocation
Given a set of images and your Google locations history, it approximately geolocates your images by modifying the EXIF.

# Pre-requisites
* [Gexiv2] (https://github.com/GNOME/gexiv2/blob/master/INSTALLING)

# Usage
```
$> image_geolocation.py [-h] locations input_folder output_folder
```

* positional arguments:
..* locations --> .json file with the locations, as extracted from Google locations.
..* input_folder --> Folder with the original images.
..* output_folder --> Folder where destination images will be stored.

* optional arguments:
..* -h, --help     show this help message and exit

# How to get the Google locations history
1. Go to [Google Timeline] (https://www.google.com/maps/timeline)
..* Check that your ubications history is enabled. 
..* If not, you will just be able to use the script in this repository in the future images you take since now.



2. Go to [Google Takeout] (https://takeout.google.com/settings/takeout)
..a Unselect all
..b Select "Locations history" (or similar, mine is in Spanish so I don't know the exact words used, sorry :) )
..c Between json or kml, select *json*
..d Click *Next*

3. Select your preferred options and click on *Create file*
4. Once downloaded, uncompress the file and look for the obtained .json file.
..* The location of the file will be one of the parameters used by the script

