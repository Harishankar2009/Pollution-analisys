import numpy as np

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
