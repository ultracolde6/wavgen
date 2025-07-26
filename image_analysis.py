"""
Image Analysis Module

This module provides functions for analyzing camera images to detect and count atoms
in optical tweezers. It includes region-of-interest (ROI) detection and analysis
algorithms for real-time feedback in optical tweezer experiments.

The module includes:
- ROI center calculation based on tweezer frequency
- ROI slice generation for image analysis
- Background ROI analysis for noise reduction
- Atom counting algorithms with threshold detection
- Image processing utilities for optical tweezer analysis

This module is designed to work with camera feedback systems to provide real-time
analysis of atom positions and counts in optical tweezer arrays.
"""

import numpy as np
import time


######################### User input section ######################################

# ROI info
# must be even number
# roi_width = 16
# roi_height = 16
# roi_area = roi_width * roi_width
#

# def roi_center(tweezer_freq):
#     center_x = round(2 * (-1 * (tweezer_freq - 100) + 28)) / 2
#     center_y = round(2 * (27.8 * (tweezer_freq - 100) + 397.4)) / 2
#     return [center_x, center_y]
#
#
# def roi_slice_func(tweezer_freq):
#     center_x = roi_center(tweezer_freq)[0]
#     center_y = roi_center(tweezer_freq)[1]
#     return tuple((slice(round(center_y - roi_height / 2), round(center_y + roi_height / 2), 1), \
#                   slice(round(center_x - roi_width / 2), round(center_x + roi_width / 2), 1)))

# def roi_center(tweezer_freq):
#     center_x = round(2 * (-1 * (tweezer_freq - 100) + 31)) / 2
#     center_y = round(2 * (27.35 * (tweezer_freq - 100) + 394)) / 2
#     return [center_x, center_y]
# def roi_slice_func(tweezer_freq):
#     center_x = roi_center(tweezer_freq)[0]
#     center_y = roi_center(tweezer_freq)[1]
#     return tuple((slice(round(center_y - roi_height / 2), round(center_y + roi_height / 2), 1), \
#                   slice(round(center_x - roi_width / 2), round(center_x + roi_width / 2), 1)))

# def roi_center(tweezer_freq):
#     center_x = round(2 * (-1.2 * (tweezer_freq - 100) + 29)) / 2
#     center_y = round(2 * (27.7 * (tweezer_freq - 100) + 400)) / 2
#     return [center_x, center_y]
#
# def roi_slice_func(tweezer_freq):
#     center_x = roi_center(tweezer_freq)[0]
#     center_y = roi_center(tweezer_freq)[1]
#     return tuple((slice(round(center_y - roi_height / 2), round(center_y + roi_height / 2), 1), \
#                   slice(round(center_x - roi_width / 2), round(center_x + roi_width / 2), 1)))


# vertical tweezers
# def roi_center(tweezer_freq):
#     center_x = round(2 * (-1.2 * (tweezer_freq - 100) + 31)) / 2
#     center_y = round(2 * (27.7 * (tweezer_freq - 100) + 401)) / 2
#     return [center_x, center_y]
# def roi_slice_func(tweezer_freq):
#     center_x = roi_center(tweezer_freq)[0]
#     center_y = roi_center(tweezer_freq)[1]
#     return tuple((slice(round(center_y - roi_height / 2), round(center_y + roi_height / 2), 1), \
#                   slice(round(center_x - roi_width / 2), round(center_x + roi_width / 2), 1)))

# horizontal tweezers
# def roi_center(tweezer_freq):
#     center_x = round(2 * (27.3 * (tweezer_freq - 100) + 292)) / 2
#     center_y = round(2 * (-1.4 * (tweezer_freq - 100) + 31)) / 2
#     return [center_x, center_y]
# def roi_slice_func(tweezer_freq):
#     center_x = roi_center(tweezer_freq)[0]
#     center_y = roi_center(tweezer_freq)[1]
#     return tuple((slice(round(center_y - roi_height / 2), round(center_y + roi_height / 2), 1), \
#                   slice(round(center_x - roi_width / 2), round(center_x + roi_width / 2), 1)))

roi_width = 16
roi_height = 16
roi_area = roi_width * roi_width

roi_width_bg = 16
roi_height_bg = 16
roi_area_bg = roi_width_bg * roi_height_bg



def roi_center(tweezer_freq):
    """Calculate the center coordinates for a region of interest (ROI) based on tweezer frequency.
    
    Parameters
    ----------
    tweezer_freq : float
        The frequency of the tweezer in MHz.
        
    Returns
    -------
    list
        [center_x, center_y] coordinates for the ROI center.
    """
    ### weird drift ROI
    # center_x = round(2 * (0.020 * (tweezer_freq - 104) ** 2 + 26.6 * (tweezer_freq - 100) + 443)) / 2
    # center_y = round(2 * (-0.4 * (tweezer_freq - 100) + 72)) / 2
    ### 30 tweezer eight lambda roi
    center_x = round(2 * (0.020 * (tweezer_freq - 104) ** 2 + 26.6 * (tweezer_freq - 100) + 437)) / 2
    center_y = round(2 * (-0.5 * (tweezer_freq - 100) + 72)) / 2
    ### 50 tweezer four lambda roi
    # center_x = round(2 * (0.020 * (tweezer_freq - 104) ** 2 + 26.6 * (tweezer_freq - 100) + 443)) / 2
    # center_y = round(2 * (-0.5 * (tweezer_freq - 100) + 70)) / 2
    # return [center_x, center_y]
    ####
    # center_x = round(2 * (0.020 * (tweezer_freq - 104)**2+ 26.6 * (tweezer_freq - 100) + 449)) / 2
    #clock @ 10.0

    # center_x = round(2 * (0.01 * (tweezer_freq - 108) ** 2 + 26.7 * (tweezer_freq - 100) + 445)) / 2
    # center_y = round(2 * (-0.4 * (tweezer_freq - 100) + 63)) / 2
    return [center_x, center_y]

def roi_slice_func(tweezer_freq):
    """Generate slice indices for a region of interest (ROI) based on tweezer frequency.
    
    Parameters
    ----------
    tweezer_freq : float
        The frequency of the tweezer in MHz.
        
    Returns
    -------
    tuple
        Slice indices (y_slice, x_slice) for the ROI.
    """
    center_x = roi_center(tweezer_freq)[0]
    center_y = roi_center(tweezer_freq)[1]
    return tuple((slice(round(center_y - roi_height / 2), round(center_y + roi_height / 2), 1), \
                  slice(round(center_x - roi_width / 2), round(center_x + roi_width / 2), 1)))

def roi_slice_func_background(tweezer_freq, y_offset):
    """Generate slice indices for a background region of interest (ROI) based on tweezer frequency.
    
    Parameters
    ----------
    tweezer_freq : float
        The frequency of the tweezer in MHz.
    y_offset : int
        Vertical offset for the background ROI.
        
    Returns
    -------
    tuple
        Slice indices (y_slice, x_slice) for the background ROI.
    """
    center_x = roi_center(tweezer_freq)[0]
    center_y = roi_center(tweezer_freq)[1]+y_offset
    return tuple((slice(round(center_y - roi_height_bg / 2), round(center_y + roi_height_bg / 2), 1),
                  slice(round(center_x - roi_width_bg / 2), round(center_x + roi_width_bg / 2), 1)))
############################################################################################
start = time.time()

def analyze_image(array, tweezer_freq_list, num_tweezers):
    """Analyze an image array to count atoms in optical tweezers.
    
    Parameters
    ----------
    array : numpy.ndarray
        The image array to analyze.
    tweezer_freq_list : list
        List of tweezer frequencies in MHz.
    num_tweezers : int
        Number of tweezers to analyze.
        
    Returns
    -------
    tuple
        (atom_count, empty_list) where atom_count is the number of occupied tweezers
        and empty_list contains indices of empty tweezers.
    """
    counts_array = np.empty(num_tweezers)
    tweezer_freq_counter = 0
    upper_threshold = 500
    # background_counts = int(np.sum(array[roi_slice_func_background(tweezer_freq_list[20], 20)]))# + 250 #roi_area*91.01#105
    for tweezer_freq in tweezer_freq_list:
        counts_array[tweezer_freq_counter] = np.sum(
            array[roi_slice_func(tweezer_freq)]) - int(np.sum(array[roi_slice_func_background(tweezer_freq, -roi_height-roi_height_bg)]))/roi_area_bg*roi_area # -background_counts
        tweezer_freq_counter += 1
    atom_count = 0
    empty_list = []
    # print(counts_array)
    for i in range(num_tweezers):
        if counts_array[i] > upper_threshold:
            atom_count += 1
        else:
            empty_list.append(i)


    ######### Hack only, to not sort center tweezers##########
    # for i in empty_list:
    #     if 15<=i<=25:
    #         # delete i from empty_list:
    #         empty_list.remove(i)
    #         atom_count += 1
    ########################################################

    return atom_count, empty_list




























