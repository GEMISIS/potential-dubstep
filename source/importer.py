# -*- coding: utf-8 -*-
"""
Created on Sat Jun  6 23:58:51 2015

@author: jharrison902
"""

import gdal
import psycopg2
import os
import os.path
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
        self._projection_target = "EPSG:32618" #projection handy for the test region
        self._bands={}
        self._masks={}
    
    def get_satellite_dictionary(self):
        satellites = {}
        satellites['7']=self.set_satellite_landsat_7
        satellites['8']=self.set_satellite_landsat_8
        return satellites
    
    def parse_metadata(self):
        """
        Parse the product metadata and generate bounds, etc.
        """
        metadata_tree = ET.parse(os.path.join(self._directory,self._product_metadata))
        root = metadata_tree.getroot()
        assert root.tag == '{http://espa.cr.usgs.gov/v1.2}espa_metadata'
        """
        get overall metadata
        """
        global_metadata = root.find('{http://espa.cr.usgs.gov/v1.2}global_metadata')
        """
        get band information
        """
        band_metadata = root.find('{http://espa.cr.usgs.gov/v1.2}bands')
        """
        obtain data from global metadata
        """
        self._acquisition_date = global_metadata.find('{http://espa.cr.usgs.gov/v1.2}acquisition_date').text+'T'+global_metadata.find('{http://espa.cr.usgs.gov/v1.2}scene_center_time').text
        self._bounds={}
        """
        Get lat/lon bounds for records
        """
        ll_bounds = global_metadata.find('{http://espa.cr.usgs.gov/v1.2}bounding_coordinates')
        for direction in ll_bounds:
            cardinal = direction.tag.replace('{http://espa.cr.usgs.gov/v1.2}','')
            self._bound[cardinal]=float(direction.text)
        """
        Get satellite
        """
        satellite = global_metadata.find('{http://espa.cr.usgs.gov/v1.2}satellite').text
        """
        TODO: make this dynamically draw from available satellites
        """
        satellite_list = {'LANDSAT_7':self.set_satellite_landsat_7,'LANDSAT_8':self.set_satellite_landsat_8}
        satellite_list[satellite]()
        
        """
        Parse band metadata
        """
        self._bands={}
        for band in band_metadata:
            assert band.tag == '{http://espa.cr.usgs.gov/v1.2}band'
            attributes = band.attrib
            if attributes['category'] is 'image':
                #This is an sr_band 
                self._bands[attributes['name']]={}
                self._bands[attributes['name']]['fill']=attributes['fill_value']
                self._bands[attributes['name']]['file']=band.find('{http://espa.cr.usgs.gov/v1.2}file_name').text
            elif attributes['category'] is 'pq':
                self._masks[attributes['name']]={}
                self._masks[attributes['name']]['bits']=[]
                for bit in band.find('{http://espa.cr.usgs.gov/v1.2}bitmap_description'):
                    self._masks[attributes['name']]['bits']=bit.attrib[num]
        
                
                
        
        
        
        
    
    def set_satellite_landsat_7(self):
        """
        Set our importer to use Landsat 7 settings
        """
        self._satellite = LandSat7()
        
    def set_satellite_landsat_8(self):
        """
        Set our importer to use Landsat 8 settings
        """
        self._satellite = Landsat8()
    
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
        if not input_directory[0] is '/':
            path = os.getcwd()
            path = os.path.join(path,input_directory)
        else:
            path = input_directory
        files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path,f))]
        #find xml file
        for file_name in files:
            if file_name.endswith('.xml'):
                self._product_metadata = file_name
                break
        
        files.remove(self._product_metadata)
        self._raster_files = files
        self._directory=path
        
        
        
    
if __name__=="__main__":
    parser = argparse.ArgumentParser(description="Import Landsat surface reflectance products.")
    parser.add_argument('--satellite', type=str, metavar='SATELLITE',required=True,choices=['7','8'],help="The product's satellite",dest="target_satellite")
    parser.add_argument('--dir',type=str,metavar='DIRECTORY',required=True,help="The path of the directory of SR products.",dest="directory")
    importer = Importer()
    importer.get_satellite_dictionary[target_satellite]()
    importer.determine_raster_files(directory)
    importer.tile_raster()
    
    
    