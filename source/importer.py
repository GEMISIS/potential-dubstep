# -*- coding: utf-8 -*-
"""
Created on Sat Jun  6 23:58:51 2015

@author: jharrison902
"""

import gdal
import psycopg2
import os
import argparse
import xml.etree.ElementTree as ET

"""
Tile and import into database our raster files.
Usage:
importer.py --satellite SATELLITE --dir DIRECTORY
"""
class Importer:
    def __init__(self):
        #initialize variables
        self._directory = ""
        self._satellite = None
        self._table = "GISBox"
        self._projection_target = "EPSG:32618"
        self._bands={}
        self._masks={}
    
    def generate_cmd_string(self, tile_path, tile_x, tile_y):
        """
        Generate the string to store a tile in the database.
        """
        
        raise NotImplementedError
        
    def tile_raster(self,target_raster):
        """
        Convert raster into tiles using gdalwarp.
        Coordinates will be stored in self._projection_target projection.
        """
        
        raise NotImplementedError
    def determine_raster_files(self,input_directory):
        """
        Parse the product metadata and determine the bands and masks
        """
        