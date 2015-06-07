# -*- coding: utf-8 -*-
"""
Created on Sat Jun  6 23:58:51 2015

@author: jharrison902
"""

import gdal

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
        self._projection_target_short = "EPSG:32618" #projection handy for the test region
        self._projection_target = 'PROJCS["WGS 84 / UTM zone 18N",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433],AUTHORITY["EPSG","4326"]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",-75],PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AUTHORITY["EPSG","32618"]]'
        self._tmp_dir = "/Users/jharrison902/Desktop/giswork/tmp"
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
        print "Parsing metadata"
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
            self._bounds[cardinal]=float(direction.text)
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
            print band.tag
            assert band.tag == '{http://espa.cr.usgs.gov/v1.2}band'
            attributes = band.attrib
            if attributes['category'] == "image":
                #This is an sr_band 
                self._bands[attributes['name']]={}
                print "Found band "+attributes['name']
                self._bands[attributes['name']]['fill']=attributes['fill_value']
                self._bands[attributes['name']]['file']=band.find('{http://espa.cr.usgs.gov/v1.2}file_name').text
            elif attributes['category'] =='pq':
                self._masks[attributes['name']]={}
                self._masks[attributes['name']]['bits']=[]
                for bit in band.find('{http://espa.cr.usgs.gov/v1.2}bitmap_description'):
                    self._masks[attributes['name']]['bits']=bit.attrib['num']
            else:
                print "Unidentified record in metadata: "+attributes['category']+"!"
        
                
                
        
        
        
        
    
    def set_satellite_landsat_7(self):
        """
        Set our importer to use Landsat 7 settings
        """
        self._satellite = 'LANDSAT_7'
        """
        TODO: should this do more?
        """
        
    def set_satellite_landsat_8(self):
        """
        Set our importer to use Landsat 8 settings
        """
        self._satellite = 'LANDSAT_8'
        """
        TODO: should this do more?
        """
    
    def generate_cmd_string(self, input_file, tile_path, tile_x, tile_y, size):
        """
        Generate the string to store a tile in the database.
        """
        cmd = 'gdalwarp'
        cmd+=' -of GTiff' #geotiff output
        cmd+=' -tr 30 30' #30m resolution
        cmd+=' -te '+str(tile_x)+' '+str(tile_y)+' '+str(tile_x+size)+' '+str(tile_y+size)
        cmd+=' -r cubic' #cubic resampling if we absolutely have to resample
        cmd+=' '+os.path.join(self._directory,input_file)
        cmd+=' '+os.path.join(self._tmp_dir,tile_path)
        
        return cmd
        
    def tile_raster(self):
        """
        Convert raster into tiles using gdalwarp.
        Coordinates will be stored in self._projection_target projection.
        """
        print "Preparing to create tiles"
        gdal.AllRegister()
        for band in self._bands:
            print band
            file_path = os.path.join(self._directory,self._bands[band]['file'])
            band_file = gdal.Open(file_path)
            """
            TODO: implement a database lock on inserts at this point
            """
            """
            Reproject our data
            """
            print "Reprojecting product..."
            band_file.SetProjection(self._projection_target)
            band_file.FlushCache()
            """
            Slice data into tiles based on size in coordinate system
            """
            x_size = band_file.RasterXSize
            y_size = band_file.RasterYSize
            geotrans = band_file.GetGeoTransform()
            x_arr = [0,x_size]
            y_arr = [0,y_size]
            extent = []
            #determine extents
            for xpixel in x_arr:
                for ypixel in y_arr:
                    x = geotrans[0]+(xpixel*geotrans[1])+(ypixel*geotrans[2])
                    y = geotrans[3]+(xpixel*geotrans[4])+(ypixel*geotrans[5])
                    extent.append([x,y])
                y_arr.reverse()
            """
            slice file based on 1000m squares
            """
            #get lower x, lower y
            low_x=10000000000.0
            low_y=10000000000.0
            high_x=-10000000000.0
            high_y=-10000000000.0
            for pair in extent:
                if pair[0]<low_x:
                    low_x=pair[0]
                if pair[0]>high_x:
                    high_x=pair[0]
                if pair[1]<low_y:
                    low_y=pair[1]
                if pair[1]>high_y:
                    high_y=pair[1]
            x_step = low_x
            y_step = low_y
            while x_step <= high_x:
                while y_step <= high_y:
                    print "Generating tile: "+str(x_step)+" "+str(y_step)
                    cmd = self.generate_cmd_string(self._bands[band]['file'],self._satellite+'_'+band+'_'+self._acquisition_date+'_'+str(x_step)+'_'+str(y_step)+'.tif',x_step,y_step,1000)
                    os.system(cmd)
                    """
                    Store raster in database
                    """
                    """
                    TODO: Implement psql insertion!
                    """
                    y_step+=100.0
                y_step = low_y
                x_step+=100.0
            
            
        
    def determine_raster_files(self,input_directory):
        """
        Parse the product metadata and determine the bands and masks
        """
        print "Locating raster files in: "+input_directory
        if not input_directory[0] is '/':
            path = os.getcwd()
            path = os.path.join(path,input_directory)
        else:
            print "This is an absolute path!"
            path = input_directory
        files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path,f))]
        #find xml file
        for file_name in files:
            if file_name.endswith('.xml'):
                print "Product metadata found! "+file_name
                self._product_metadata = file_name
                break
        
        files.remove(self._product_metadata)
        self._raster_files = files
        self._directory=path
        
        
        
        
    
if __name__=="__main__":
    import sys
    parser = argparse.ArgumentParser(description="Import Landsat surface reflectance products.")
    
    #parser.add_argument('--satellite', type=str, metavar='SATELLITE',required=True,choices=['7','8'],help="The product's satellite",dest="target_satellite")
    parser.add_argument('--directory','-d',type=str,metavar='DIRECTORY',required=True,action='store',help="The path of the directory of SR products.",dest="directory")
    args = parser.parse_args()
    importer = Importer()
    importer.determine_raster_files(args.directory)
    importer.parse_metadata()
    importer.tile_raster()
    
    
    