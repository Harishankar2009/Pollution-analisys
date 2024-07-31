import numpy as np
import cv2
from PIL import Image
import urllib.parse
import urllib.request
import io
from math import log, exp, tan, atan, pi, ceil
from place_lookup import find_coordinates

EARTH_RADIUS = 6378137
EQUATOR_CIRCUMFERENCE = 2 * pi * EARTH_RADIUS
INITIAL_RESOLUTION = EQUATOR_CIRCUMFERENCE / 256.0
ORIGIN_SHIFT = EQUATOR_CIRCUMFERENCE / 2.0

def latlon_to_pixels(lat, lon, zoom):
    mx = (lon * ORIGIN_SHIFT) / 180.0
    my = log(tan((90 + lat) * pi / 360.0)) / (pi / 180.0)
    my = (my * ORIGIN_SHIFT) / 180.0
    res = INITIAL_RESOLUTION / (2 ** zoom)
    px = (mx + ORIGIN_SHIFT) / res
    py = (my + ORIGIN_SHIFT) / res
    return px, py

def pixels_to_latlon(px, py, zoom):
    res = INITIAL_RESOLUTION / (2 ** zoom)
    mx = px * res - ORIGIN_SHIFT
    my = py * res - ORIGIN_SHIFT
    lat = (my / ORIGIN_SHIFT) * 180.0
    lat = 180 / pi * (2 * atan(exp(lat * pi / 180.0)) - pi / 2.0)
    lon = (mx / ORIGIN_SHIFT) * 180.0
    return lat, lon

def calculate_area(res):
    total_pixels = res.size // 3
    non_zero_pixels_rgb = np.count_nonzero(res)
    row, col, _ = res.shape
    percentage_of_land = non_zero_pixels_rgb / (row * col * 3)

    cm_2_pixels = 37.795275591
    row_cm = row / cm_2_pixels
    col_cm = col / cm_2_pixels
    total_area_cm = total_pixels / (row_cm * col_cm)
    total_area_cm_land = total_area_cm * percentage_of_land

    total_area_m_actual_land = total_area_cm_land * 516.5289256198347
    total_area_acre_land = total_area_m_actual_land * 0.000247105

    number_of_trees = total_area_acre_land * 10890
    print(f"{round(number_of_trees)} number of trees can be planted in {total_area_acre_land} acres.")

    return total_area_acre_land, round(number_of_trees)

def air_pollution_core(ullat, ullon, lrlat, lrlon, results):
    zoom = 18
    scale = 1
    maxsize = 640

    ulx, uly = latlon_to_pixels(ullat, ullon, zoom)
    lrx, lry = latlon_to_pixels(lrlat, lrlon, zoom)

    dx, dy = lrx - ulx, lry - uly

    cols, rows = int(ceil(dx / maxsize)), int(ceil(dy / maxsize))
    bottom = 120
    largura = int(ceil(dx / cols))
    altura = int(ceil(dy / rows))
    alturaplus = altura + bottom

    final_image = Image.new('RGB', (int(dx), int(dy)))
    total_acres_place, total_trees = 0., 0.
    total_tile_results = {}

    for x in range(cols):
        for y in range(rows):
            dxn = largura * (0.5 + x)
            dyn = altura * (0.5 + y)
            latn, lonn = pixels_to_latlon(ulx + dxn, uly - dyn - bottom / 2, zoom)
            position = f'{latn},{lonn}'
            print(x, y, position)

            urlparams = urllib.parse.urlencode({
                'center': position,
                'zoom': str(zoom),
                'size': f'{largura}x{alturaplus}',
                'maptype': 'satellite',
                'sensor': 'false',
                'scale': scale,
                'key': 'YOUR_API_KEY_HERE'
            })
            url = f'http://maps.google.com/maps/api/staticmap?{urlparams}'
            f = urllib.request.urlopen(url)
            image = io.BytesIO(f.read())
            im = Image.open(image)
            im.save(f'map_{x}_{y}_{position}.png')

            img = cv2.imread(f'map_{x}_{y}_{position}.png')
            shifted = cv2.pyrMeanShiftFiltering(img, 7, 30)
            hsv = cv2.cvtColor(shifted, cv2.COLOR_BGR2HSV)

            lower_trees = np.array([10, 0, 10])
            higher_trees = np.array([180, 180, 75])

            mask_trees = cv2.inRange(hsv, lower_trees, higher_trees)
            res = cv2.bitwise_and(img, img, mask=mask_trees)

            area_in_acres, number_of_trees = calculate_area(res)
            total_acres_place += area_in_acres
            total_trees += number_of_trees
            print(f'Area: {area_in_acres}, Number of trees: {number_of_trees}')

            tile_results = {
                'name_of_tile_image': f'map_{x}_{y}_{position}.png',
                'area_acres': area_in_acres,
                'number_of_trees': number_of_trees
            }
            total_tile_results[f'{x}_{y}_{position}'] = tile_results

            cv2.imshow('Result', res)
            cv2.imshow('Original Image', img)
            cv2.waitKey(2000)
            cv2.destroyAllWindows()

    results['total_tile_results'] = total_tile_results
    results['total_acres_of_land'] = total_acres_place
    results['total_number_of_trees'] = total_trees
    return results

def location_based_estimation(place):
    results = find_coordinates(place)
    ullat, ullon = results['upper_left']
    lrlat, lrlon = results['lower_right']
    return air_pollution_core(ullat, ullon, lrlat, lrlon, results)

def coordinates_based_estimation(upper_left, lower_right):
    ullat, ullon = map(float, upper_left.split(','))
    lrlat, lrlon = map(float, lower_right.split(','))
    results = {}
    return air_pollution_core(ullat, ullon, lrlat, lrlon, results)