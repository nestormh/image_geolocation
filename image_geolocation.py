# -*- coding: utf-8 -*-

__author__ = 'nestor'

import argparse
import os
import pexif
import json
import glob
from pprint import pprint
from pykml import parser
from lxml import etree
import xml.etree.ElementTree
from datetime import datetime
from gi.repository import GExiv2
import numpy as np
from sklearn.neighbors import KDTree
from distutils.dir_util import mkpath
from shutil import copyfile

class ImageLocator:
    NAMESPACE = "{http://www.opengis.net/kml/2.2}"

    def __init__(self):
        pass

    def open_localizations(self, input_dir):
        files = glob.glob('%s/*.kml' % input_dir)

        for kml_file in files:
            with open(kml_file) as f:
                parser = etree.XMLParser(ns_clean=True)
                doc = etree.parse(f, parser=parser)

            print etree.tostring(doc, pretty_print=True)


            e = doc.getroot()
            # e = xml.etree.ElementTree.parse(kml_file).getroot()

            # print etree.tostring(doc, pretty_print=True)

            for document in e.findall("%sDocument" % self.NAMESPACE):
                if "%sDocument" % self.NAMESPACE == document.tag:
                    for placemark in document.findall("%sPlacemark" % self.NAMESPACE):
                    # print(atype.get('foobar'))
                        print document, placemark.tag
                        placemark_data = {}
                        for item in placemark.findall("*"):
                            print item.tag, item.text

                        exit(0)
            # print type(doc)
            # for node in doc.iteritems():
            #     print node.tag, node.text

            # print doc["kml"]
            exit(0)

    def open_locations_json(self, filename):
        with open(filename, "r") as f:
            locations = json.load(f)

        self.locations = {}
        for location in locations["locations"]:
            # print location.keys()
            # timestamp = datetime.utcfromtimestamp(int(location["timestampMs"]) / 1000)
            timestamp = int(location["timestampMs"]) / 1000

            latitude = float(location["latitudeE7"]) / 1e7
            longitude = float(location["longitudeE7"]) / 1e7

            # print timestamp, datetime.utcfromtimestamp(timestamp).strftime("%Y/%m/%d %H:%M:%S"), latitude, longitude

            self.locations[timestamp] = (latitude, longitude)

    def update_images_info(self, folder, output_folder):
        extensions = [ "jpg" ]

        if not os.path.exists(output_folder):
            mkpath(output_folder)

        files = []
        for extension in extensions:
            files += glob.glob('%s/*.%s' % (folder, extension.lower()))
            files += glob.glob('%s/*.%s' % (folder, extension.upper()))

        timestamps = sorted(self.locations.keys())

        takeClosest = lambda num,collection:min(collection,key=lambda x:abs(x-num))
        # closest = takeClosest(timestamps[0], timestamps[1:])
        # print timestamps[0], timestamps[1], closest

        # http://coreygoldberg.blogspot.com.es/2014/01/python-fixing-my-photo-library-dates.html
        # https://git.gnome.org/browse/gexiv2/tree/GExiv2.py
        for filename in files:
            output_file = os.path.join(output_folder, os.path.basename(filename))
            print filename, "-->", output_file

            copyfile(filename, output_file)

            exif = GExiv2.Metadata(filename)

            # exif.set_gps_info(10, 20, 30)
            # pprint(exif.get_tags())

            curr_timestamp = datetime.strptime(exif['Exif.Image.DateTime'], "%Y:%m:%d %H:%M:%S")
            curr_timestamp = (curr_timestamp - datetime(1970, 1, 1)).total_seconds()

            # print curr_timestamp, exif['Exif.Image.DateTime']
            closest_timestamp = takeClosest(curr_timestamp, timestamps)
            # print curr_timestamp, closest, datetime.utcfromtimestamp(closest)

            gps_coords = self.locations[closest_timestamp]


            # print gps_coords
            exif.set_gps_info(gps_coords[1], gps_coords[0], 0.0)
            # print curr_timestamp
            if gps_coords[0] >= 0.0:
                exif.set_tag_string("Exif.GPSInfo.GPSLatitudeRef", "N")
            else:
                exif.set_tag_string("Exif.GPSInfo.GPSLatitudeRef", "S")

            if gps_coords[1] >= 0.0:
                exif.set_tag_string("Exif.GPSInfo.GPSLongitudeRef", "E")
            else:
                exif.set_tag_string("Exif.GPSInfo.GPSLongitudeRef", "W")

            # print exif['Exif.Image.DateTime']
            # print exif['Exif.Photo.DateTimeDigitized']
            # print exif['Exif.Photo.DateTimeOriginal']
            # print exif['Exif.GPSInfo.GPSLatitude']
            # print exif['Exif.GPSInfo.GPSLongitude']
            # print exif['Exif.GPSInfo.GPSAltitude']
            # print exif['Exif.GPSInfo.GPSLatitudeRef']
            # print exif['Exif.GPSInfo.GPSLongitudeRef']
            # print exif['Exif.GPSInfo.GPSAltitudeRef']
            # print exif['Exif.GPSInfo.GPSMapDatum']
            # print exif['Exif.GPSInfo.GPSVersionID']

            exif.save_file(output_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Add geolocation to your images based on Google History.')
    parser.add_argument("locations", metavar="locations", type=str,
                       help='.json file with the locations, as extracted from Google locations.')
    parser.add_argument("input_folder", metavar="input_folder", type=str,
                       help='Folder with the original images.')
    parser.add_argument("output_folder", metavar="output_folder", type=str,
                       help='Folder where destination images will be stored.')

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

