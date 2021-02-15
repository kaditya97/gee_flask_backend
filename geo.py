import ee
import geemap

def geo():
    data = geemap.Map()
    dem = ee.Image('USGS/SRTMGL1_003')
    landcover = ee.Image("ESA/GLOBCOVER_L4_200901_200912_V2_3").select('landcover')
    landsat7 = ee.Image('LE7_TOA_5YEAR/1999_2003')

    # Set visualization parameters.
    vis_params = {
    'min': 0,
    'max': 4000,
    'palette': ['006633', 'E5FFCC', '662A00', 'D8D8D8', 'F5F5F5']}

    # Add Earth Eninge layers to data
    data.addLayer(dem, vis_params, 'STRM DEM', True, 0.5)
    data.addLayer(landcover, {}, 'Land cover')
    data.addLayer(landsat7, {'bands': ['B4', 'B3', 'B2'], 'min': 20, 'max': 200}, 'Landsat 7')
    return data