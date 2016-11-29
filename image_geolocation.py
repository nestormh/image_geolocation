# -*- coding: utf-8 -*-

__author__ = 'Néstor Morales Hernández'
__copyright__ = "Copyright 2016"
__license__ = "Apache License, Version 2.0"
__version__ = "0.0.1"
__maintainer__ = "Néstor Morales Hernández"
__email__ = "nestor@isaatc.ull.es"
__status__ = "Production"


# Copyright 2016 Néstor Morales Hernández <nestor@isaatc.ull.es>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# The presented file receives as input a .json with the Google's history of locations (see the README to know how to
# retrieve it), and an input folder with images (in the current version, just .jpg), and modifies their EXIF so they
# are geo-located.
# The method looks into the image timestamp (depends on how well configured is the camera clock). Based on that
# timestamp, it searches along the available locations, selecting that which was closer in the time.
#
# The script has not been fully tested, so we suggest to keep the originals safe and use a copy as input.
#
# If you have questions, problems, inquiries, please contact me at https://github.com/nestormh/image_geolocation.
#
# Usage: image_geolocation.py [-h] locations input_folder output_folder
#
# Add geolocation to your images based on Google History.
#
# positional arguments:
#   locations      .json file with the locations, as extracted from Google
#                  locations.
#   input_folder   Folder with the original images.
#   output_folder  Folder where destination images will be stored.
#
# optional arguments:
#   -h, --help     show this help message and exit

import argparse
import os
import json
import glob
from pykml import parser
from datetime import datetime
from gi.repository import GExiv2
from distutils.dir_util import mkpath
from shutil import copyfile


class ImageLocator:
    """
    Main class which manages the pipeline of the program.
    """

    def __init__(self):
        """
        Initializes the class. Not being used at the moment
        :return: None
        """
        pass

    def open_locations_json(self, filename):
        """
        Opens the json with the locations and stores useful information in memory.
        :param filename: File name of the .json input file
        :return: Nothing, just stores the locations in a variable internal to the class.
        """
        with open(filename, "r") as f:
            json_locations = json.load(f)

        self.locations = {}
        for location in json_locations["locations"]:
            timestamp = int(location["timestampMs"]) / 1000

            latitude = float(location["latitudeE7"]) / 1e7
            longitude = float(location["longitudeE7"]) / 1e7

            self.locations[timestamp] = (latitude, longitude)

    def update_images_info(self, folder, output_folder):
        """
        1) Retrieves all the images available in the input folder
        2) For each image, retrieves the timestamp
        3) From the list of available locations, searches for the closest location in time.
        4) EXIF is modified and image is stored in the output folder.

        :param folder: Name of the input folder
        :param output_folder: Name of the output folder.
        :return: None
        """
        extensions = ["jpg"]

        if not os.path.exists(output_folder):
            mkpath(output_folder)

        files = []
        for extension in extensions:
            files += glob.glob('%s/*.%s' % (folder, extension.lower()))
            files += glob.glob('%s/*.%s' % (folder, extension.upper()))

        timestamps = sorted(self.locations.keys())

        take_closest = lambda num, collection: min(collection, key=lambda x: abs(x-num))

        # http://coreygoldberg.blogspot.com.es/2014/01/python-fixing-my-photo-library-dates.html
        # https://git.gnome.org/browse/gexiv2/tree/GExiv2.py
        for filename in files:
            output_file = os.path.join(output_folder, os.path.basename(filename))
            print filename, "-->", output_file

            copyfile(filename, output_file)

            exif = GExiv2.Metadata(filename)

            curr_timestamp = datetime.strptime(exif['Exif.Image.DateTime'], "%Y:%m:%d %H:%M:%S")
            curr_timestamp = (curr_timestamp - datetime(1970, 1, 1)).total_seconds()

            closest_timestamp = take_closest(curr_timestamp, timestamps)

            gps_coords = self.locations[closest_timestamp]

            exif.set_gps_info(gps_coords[1], gps_coords[0], 0.0)
            if gps_coords[0] >= 0.0:
                exif.set_tag_string("Exif.GPSInfo.GPSLatitudeRef", "N")
            else:
                exif.set_tag_string("Exif.GPSInfo.GPSLatitudeRef", "S")

            if gps_coords[1] >= 0.0:
                exif.set_tag_string("Exif.GPSInfo.GPSLongitudeRef", "E")
            else:
                exif.set_tag_string("Exif.GPSInfo.GPSLongitudeRef", "W")

            exif.save_file(output_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Add geolocation to your images based on Google History.')
    parser.add_argument("locations", metavar="locations", type=str, help='.json file with the locations, as extracted from Google locations.')

    parser.add_argument("input_folder", metavar="input_folder", type=str, help='Folder with the original images.')

    parser.add_argument("output_folder", metavar="output_folder", type=str, help='Folder where destination images will be stored.')

    args = parser.parse_args()

    locations = os.path.abspath(args.locations)
    input_folder = os.path.abspath(args.input_folder)
    output_folder = os.path.abspath(args.output_folder)

    if input_folder == output_folder:
        print "Input folder %s is the same as the output folder. Continue? (y/n)"
        answer = None
        while not answer in ("y", "n"):
            answer=raw_input("Input folder %s is the same as the output folder. Continue? (y/n)" % input_folder).lower()

        if answer == "n":
            exit(0)

    if not os.path.exists(locations):
        print "Locations file %s invalid or not present." % locations

    if not os.path.exists(input_folder):
        print "Input folder %s invalid or not present." % input_folder

    img_locator = ImageLocator()
    img_locator.open_locations_json(locations)
    img_locator.update_images_info(input_folder, output_folder)

