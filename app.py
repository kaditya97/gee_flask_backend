#Importing GEE Requirements
import ee
import geemap
geemap.ee_initialize(token_name='EARTHENGINE_TOKEN')
from IPython.display import Image,display
import json
import os
import requests
import pygeoj
from flask import Flask, render_template, request, send_file
from flask_cors import CORS
from PIL import Image
import geo

app = Flask(__name__,static_url_path='', static_folder='static')
CORS(app)

@app.route("/geoapi")
def geoapi():
    data = geo.geo()
    arr = []
    record = {}
    i = 0
    for n in data.layers:
        arr.append({
            'id':i,
            'url':n.url,
            'attribution':n.attribution,
            'name':n.name
        })
        i+=1
    record['records'] = arr
    return record
    

@app.route("/world", methods=['GET','POST'])
def gemap():
    map = geemap.Map()
    data = 'lulc'
    if request.method == 'POST':
        data = request.form['indicat']
    def lulc():
        landcover = ee.Image("ESA/GLOBCOVER_L4_200901_200912_V2_3").select('landcover')
        info = landcover.getInfo()
        map.addLayer(landcover, {}, 'Land cover')
        return map, info
    def dem():
        dem = ee.Image('USGS/SRTMGL1_003')
        info = dem.getInfo()
        # Set visualization parameters.
        vis_params = {
        'min': 0,
        'max': 4000,
        'palette': ['006633', 'E5FFCC', '662A00', 'D8D8D8', 'F5F5F5']}
        map.addLayer(dem, vis_params, 'STRM DEM', True, 0.5)
        return map, info
    if(data=='lulc'):
        data, info = lulc()
    elif(data=='dem'):
        data, info = dem()
    states = ee.FeatureCollection('users/kaditya97/nepal_province')
    map.addLayer(states,{},'Nepal States')
    arr = []
    record = {}
    i = 0
    for n in data.layers:
        arr.append({
            'id':i,
            'url':n.url,
            'attribution':n.attribution,
            'name':n.name
        })
        i+=1
    record['records'] = arr
    record['info'] = info
    return record

@app.route("/", methods=['GET','POST'])
def getvalue():
    map = geemap.Map()
    coord = ''
    bbox = ''
    data = 'ndvi'
    start_date = '2019-01-01'
    end_date = '2019-04-30'
    img = "LANDSAT/LC08/C01/T1_RT"
    if request.method == 'POST':
        roi = request.files['roi']
        geofile = json.load(roi)
        data = request.form['indicator']
        
        a = pygeoj.load(None,geofile)
        for feature in a:
            coord = feature.geometry.coordinates
            bbox = feature.geometry.bbox
            bbox = [[bbox[1],bbox[0]],[bbox[3],bbox[2]]]
            gtype = feature.geometry.type
            print(gtype,bbox)
    if(coord != ''):
        region = ee.Geometry.MultiPolygon(coord)
    else:
        region = ee.Geometry.Polygon([[[83.829803, 28.316455],
            [84.157677, 28.316455],
            [84.157677, 28.150463],
            [83.829803, 28.150463]]])
    
    def index_calculation(a,b):
        return a.subtract(b).divide(a.add(b))
       
    def ndvi(img , region , start_date , end_date):
        data = ee.ImageCollection(img).filterBounds(region).filterDate(start_date,end_date).median()
        info = data.getInfo()
        vis_params = {"min": -1, "max": 1, "palette": ['blue', 'white', 'green']}
        # vis_params = {"min": -1, "max": 1, "palette": ['FFFFFF', 'CE7E45', 'DF923D', 'F1B555', 'FCD163', '998718', '74A901', '66A000', '529400','3E8601', '207401', '056201', '004C00', '023801', '011D01', '011301']}
        
        if (img == "LANDSAT/LC08/C01/T1_RT"):
            data = ee.ImageCollection(img).filterBounds(region).filterDate(start_date,end_date).sort('CLOUD_COVER').first()
            info = data.getInfo()
            nir = data.select('B5')
            red = data.select('B4')
            data = index_calculation(nir,red)
            # vis_params = {"min": -1, "max": 1, "palette": ['blue', 'white', 'green']}
          
        elif (img == "COPERNICUS/S2_SR"):
            nir = data.select('B8')
            red = data.select('B4')
            data = index_calculation(nir,red) 
            # vis_params= {"opacity":1,"bands":["B8"],"min":0.20868456628048035,"max":0.33335007464955435,"palette":["04ff00","ffc800"]}

        data=data.clip(region)
        map_id_dict = ee.Image(data)
        map.addLayer(map_id_dict, vis_params, 'ndvi', True, 0.5)
        return map, info

    def ndbi(img , region , start_date , end_date):
        data = ee.ImageCollection(img).filterBounds(region).filterDate(start_date,end_date).median()
        info = data.getInfo()
        vis_params = {"min": -1, "max": 1, "palette": ['ec5e08','e5bd09','8af204', '3ae204']}
        
        if (img == "LANDSAT/LC08/C01/T1_RT"):
            data = ee.ImageCollection(img).filterBounds(region).filterDate(start_date,end_date).sort('CLOUD_COVER').first()
            info = data.getInfo()
            data = data.clip(region)
            swir1 = data.select('B6')
            nir = data.select('B5')
            data = index_calculation(swir1,nir)
            # vis_params = {"opacity":1,"bands":["B6"],"min":-0.4212116988711605,"max":-0.12628187297607416,"palette":["ff7600","fff700","1bff00"]}
        elif (img == "COPERNICUS/S2_SR"):
            swir1 = data.select('B11')
            data = data.clip(region)
            nir = data.select('B8')
            data = index_calculation(swir1,nir)
            # vis_params = {"opacity":1,"bands":["B12"],"min":-0.6638634079736231,"max":0.27875025492150074,"palette":["00ff66","fbff00","ffc800"]}; 

        data = data.clip(region)   
        map_id_dict = ee.Image(data)
        map.addLayer(map_id_dict, vis_params, 'ndbi', True, 0.5)
        return map, info
    
    def ndwi(img , region , start_date , end_date):
        data = ee.ImageCollection(img).filterBounds(region).filterDate(start_date,end_date).median()
        info = data.getInfo()
        vis_params = {"min": -1, "max": 1, "palette": ['blue','white', 'green']}
        
        if (img == "LANDSAT/LC08/C01/T1_RT"):
            data = ee.ImageCollection(img).filterBounds(region).filterDate(start_date,end_date).sort('CLOUD_COVER').first()
            info = data.getInfo()
            nir = data.select('B5')
            swir1 = data.select('B6')
            data = index_calculation(swir1,nir)
        elif (img == "COPERNICUS/S2_SR"):
            nir = data.select('B8')
            swir1 = data.select('B11')
            data = index_calculation(swir1,nir) 
        
        data = data.clip(region)
        map_id_dict = ee.Image(data)
        map.addLayer(map_id_dict, vis_params, 'ndwi', True, 0.5)
        return map, info
    
    def hillshade(img , region , start_date , end_date):
        data = ee.Image("USGS/SRTMGL1_003")
        info = data.getInfo()
        dem = data.clip(region)
        hillshade = ee.Terrain.hillshade(dem)
        vis_params = {"opacity":1}
        map.addLayer(hillshade, vis_params, 'STRM hillshade', True, 0.5)
        return map, info   
    
    def slope(img , region , start_date , end_date):
        data = ee.Image("USGS/SRTMGL1_003")
        info = data.getInfo()
        dem = data.clip(region)
        slope = ee.Terrain.slope(dem)
        vis_params = {"opacity":1}
        map.addLayer(slope, vis_params, 'STRM Slope', True, 0.5)
        return map, info
    
    def aspect(img , region , start_date , end_date):
        data = ee.Image("USGS/SRTMGL1_003")
        info = data.getInfo()
        dem = data.clip(region)
        aspect = ee.Terrain.aspect(dem)
        vis_params = {"opacity":1}
        map.addLayer(aspect, vis_params, 'STRM Aspect', True, 0.5)
        return map, info

    def lulc(region):
        landcover = ee.Image("ESA/GLOBCOVER_L4_200901_200912_V2_3").select('landcover').clip(region)
        info = landcover.getInfo()
        map.addLayer(landcover, {}, 'Land cover')
        return map, info

    def dem(region):
        dem = ee.Image('USGS/SRTMGL1_003').clip(region)
        info = dem.getInfo()
        # Set visualization parameters.
        vis_params = {
        'min': 0,
        'max': 4000,
        'palette': ['006633', 'E5FFCC', '662A00', 'D8D8D8', 'F5F5F5']}
        map.addLayer(dem, vis_params, 'STRM DEM', True, 0.5)
        return map, info
    
    
    if (data=='ndvi'):
        data, info = ndvi(img , region , start_date , end_date)
    elif (data=='ndbi'):
        data, info = ndbi(img , region , start_date , end_date)
    elif (data=='ndwi'):
        data, info= ndwi(img , region , start_date , end_date)
    elif(data=='hillshade'):
        data, info= hillshade(img , region , start_date , end_date)
    elif(data=='slope'):
        data, info = slope(img , region , start_date , end_date)
    elif(data=='aspect'):
        data, info = aspect(img , region , start_date , end_date)
    elif(data=='lulc'):
        data, info = lulc(region)
    elif(data=='dem'):
        data, info = dem(region)
    arr = []
    record = {}
    i = 0
    for n in data.layers:
        arr.append({
            'id':i,
            'bounds':bbox,
            'url':n.url,
            'attribution':n.attribution,
            'name':n.name
        })
        i+=1
    record['records'] = arr
    record['info'] = info
    return record 
    

if __name__ == "__main__":
    app.run(debug=True)
    