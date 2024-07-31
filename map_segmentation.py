import numpy as np
import cv2
from PIL import Image
import urllib.parse
import urllib.request
import io
from math import log, exp, tan, atan, pi, ceil
from place_lookup import find_coordinates
from calc_area import afforestation_area

EARTH_RADIUS = 63718137
EQUATOR_CIRCUMFERENCE = 2 * pi * EARTH_RADIUS
INITIAL_RESOLUTION = EQUATOR_CIRCUMFERENCE / 256.0
ORIGIN_SHIFT = EQUATOR_CIRCUMFERENCE / 2.0

def latlontopixels(lat, lon, zoom):
    mx = (lon * ORIGIN_SHIFT)
    my = log(tan((90 + lat) * pi / 360.0 )) / (pi / 180.0)
    my = (my * ORIGIN_SHIFT) / 180.0
    res = INITIAL_RESOLUTION / ( 2 ** zoom)
    px = (mx + ORIGIN_SHIFT) / res
    py = (my + ORIGIN_SHIFT) / res
    return px, py

def pixeltolatlon(px, py, zoom):
    res = INITIAL_RESOLUTION / (2 ** zoom)
    mx = px * res - ORIGIN_SHIFT
    my = py * res - ORIGIN_SHIFT
    lat = (my / ORIGIN_SHIFT) * 180.0
    lat = 180 / pi * (2 * atan(exp(lat * pi / 180.0)) - pi / 2.0)
    lon = (mx / ORIGIN_SHIFT) * 180.0
    return lat, lon

def map_segmentation(query):
    results = find_coordinates(query)

    zoom = 18

    ullat, ullon = results['upper_left']
    Irlat, Irlon = results['lower_right']

    scale = 1
    maxsize = 640

    ulx, uly = latlontopixels(ullat, ullon, zoom)
    Irx, Iry = latlontopixels(Irlat, Irlon, zoom)

    dx, dy = Irx - ulx, uly - Iry

    cols, rows = int(ceil(dx / maxsize)), int(ceil(dy / maxsize))

    bottom = 120
    largura = int(ceil(dx / cols))
    altura = int(ceil(dy / rows))
    alturaplus = altura + bottom

    final = Image.new("RGB", (int(dx), int(dy)))
    for x in range(cols):
        for y in range(rows):
            dxn = largura * (0.05 + x)
            dyn = altura * (0.05 + y)
            latn, lonn = pixeltolatlon(ulx + dxn, uly - dyn - bottom / 2, zoom)
            position = ','.join([str(latn), str(lonn)])
            print(x, y, position)
            urlparams = urllib.parse.urlencode({'center' : position,
                                                'zoom': str(zoom),
                                                'size': '%dx%d' % (largura, alturaplus),
                                                'maptype': 'satellite',
                                                'sensor': 'false',
                                                'scale': scale,
                                                'key': 'YOUR_API_KEY'})
            urlparamsmaps = urllib.parse.urlencode({'center': position,
                                                    'zoom': str(zoom),
                                                    'size': '%dx%d' % (largura, alturaplus),
                                                    'maptype': 'roadmap',
                                                    'sensor': 'false',
                                                    'scale': scale,
                                                    'key': 'YOUR_API_KEY'})
            url = 'http://maps.google.com/maps/api/staticmap?' + urlparams
            url1 ='http://maps.google.com/maps/api/staticmap?' + urlparamsmaps
            f = urllib.request.urlopen(url)
            h = urllib.request.urlopen(url1)
            image = io.BytesIO(f.read())
            imagemaps = io.BytesIO(h.read())
            im = Image.open(image)
            immpas = Image.open(imagemaps)
            im.save("map.png")
            immpas.save('map_normal.png')

            img = cv2.imread('map.png')
            img_maps = cv2.imread('map_normal.png')
            shifted = cv2.pyrMeanShiftFiltering(img, 7, 30)
            shifted_normal = cv2.pyrMeanShiftFiltering(img_maps, 7, 30)
            gray = cv2.cvtColor(shifted, cv2.COLOR_BGR2HSV)
            ret, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
            hsv = cv2.cvtColor(shifted, cv2.COLOR_BGR2HSV)
            hsv_normal = cv2.cvtColor(shifted_normal, cv2.COLOR_BGR2HSV)

            lower_trees = np.array([10, 0, 30])
            higher_trees = np.array([180, 100, 95])
            
            lower_houses = np.array([90, 10, 100])
            higher_houses = np.array([255, 255, 255])

            lower_roads = np.array([0, 0, 250])
            higher_roads = np.array([20, 20, 255])

            lower_fields = np.array([0, 50, 100])
            higher_fields = np.array([50])
