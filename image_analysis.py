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
    center_x = roi_center(tweezer_freq)[0]
    center_y = roi_center(tweezer_freq)[1]
    return tuple((slice(round(center_y - roi_height / 2), round(center_y + roi_height / 2), 1), \
                  slice(round(center_x - roi_width / 2), round(center_x + roi_width / 2), 1)))

def roi_slice_func_background(tweezer_freq, y_offset):
    center_x = roi_center(tweezer_freq)[0]
    center_y = roi_center(tweezer_freq)[1]+y_offset
    return tuple((slice(round(center_y - roi_height_bg / 2), round(center_y + roi_height_bg / 2), 1),
                  slice(round(center_x - roi_width_bg / 2), round(center_x + roi_width_bg / 2), 1)))
############################################################################################
start = time.time()

def analyze_image(array, tweezer_freq_list, num_tweezers):
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




























