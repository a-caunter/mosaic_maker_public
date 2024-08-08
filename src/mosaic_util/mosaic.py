import sys
import os
import random
import math
import time
import numpy as np
from PIL import Image, ImageDraw
import cv2
from mosaic_util.classify_image_library import reduce_shapes

script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
sys.path.append(project_dir)


class Mosaic:
    def __init__(self, height, width, images=None):
        self.name = None
        self.images_list = images
        self.height = height
        self.width = width
        self.filenames = np.full((self.height, self.width), None)
        self.tilt_deltas = np.full((self.height, self.width, 3), 0)

    def fill_filenames_and_tilts(self, images_list):
        self.filenames = np.array([i[0] for i in images_list]).reshape(self.height, self.width)
        self.tilt_deltas = np.vstack([i[1] for i in images_list]).reshape(self.height, self.width, 3)


def generate_pixelated_image(base_image_np, num_blocks_width, style):
    """
    Compress the image by consolidating the original set of pixels into a set of
    pixels that averages a square area of pixels dictated by the number of blocks
    desired across the width of the image.
    """
    print("style: ", style)
    if style == "Square":
        block_size = base_image_np.shape[1] // num_blocks_width
        # Calculate the dimensions of the new array
        height, width, channels = base_image_np.shape
        new_height = height // block_size
        new_width = width // block_size

        # Create a new array to store the averaged values
        averaged_pixels = np.zeros((new_height, new_width, channels), dtype=np.int32)

        # Iterate over the slices of the input image
        for i in range(new_height):
            for j in range(new_width):
                # Extract the slice of size (block_size, block_size, 3)
                slice_ = base_image_np[i * block_size : (i + 1) * block_size, j * block_size : (j + 1) * block_size, :]
                # print(slice_)

                # Calculate the mean for each color channel
                averaged_values = np.mean(slice_, axis=(0, 1))

                # Assign the averaged values to the new array
                averaged_pixels[i, j, :] = averaged_values.round().astype(np.int16)
        # print(averaged_pixels)
        print(averaged_pixels, block_size)
        return averaged_pixels, block_size
    if style == "Hex":
        height, width, channels = base_image_np.shape
        block_width = width // num_blocks_width
        block_height = block_width * 1.1547
        new_height = int(height // (block_height * 0.75))
        new_width = int((width // block_width) - 1)
        # print(new_height, type(new_height))
        # print(new_width, type(new_width))

        # Create a new array to store the averaged values
        averaged_pixels = np.zeros((new_height, new_width, channels), dtype=np.int32)
        count = 0
        # Iterate over the slices of the input image
        for i in range(new_height):
            for j in range(new_width):
                j0 = j + 0.5 if count == 1 else j
                i0 = i * 0.75
                # Extract the slice of size (block_size, block_size, 3)
                slice_ = base_image_np[
                    int(i0 * block_height) : int((i0 + 1) * block_height),
                    int(j0 * block_width) : int((j0 + 1) * block_width),
                    :,
                ]
                # print(slice_)

                # Calculate the mean for each color channel
                averaged_values = np.mean(slice_, axis=(0, 1))

                # Assign the averaged values to the new array
                averaged_pixels[i, j, :] = averaged_values.round().astype(np.int16)
            count = 1 if count == 0 else 0
        # print(averaged_pixels)
        # print(averaged_pixels, block_width)
        return averaged_pixels, block_width


def calculate_color_difference(pixel, block_color, style):
    pixel = pixel.astype(np.int32)
    # print(type(pixel[0]))
    # print(type(block_color[0]))
    if style == "color":
        color_difference = np.linalg.norm(pixel - block_color)
        # color_difference = (
        #     (pixel[0] - block_color[0]) ** 2 + (pixel[1] - block_color[1]) ** 2 + (pixel[2] - block_color[2]) ** 2
        # ) ** 0.5
    elif style == "greyscale":
        color_difference = abs(pixel - block_color)
    return color_difference


def pic_match(
    pixel,
    color_dict,
    block_dict,
    indexed,
    indexed_arr,
    shape_dict,
    density_map,
    color_delta_filter,
    shape_match_filter,
    density_match,
    map_min,
    map_max,
    base_image,
    block_size,
    x,
    y,
    mosaic_obj,
    repeat_filter,
    packing_style,
):
    """
    Take a pixel from the pixelated image and return the pixels of the block that has a close color match.

    min delta images are the images found with the lowest color delta to the target
    """
    start = time.time()
    surrounding_pics = mosaic_obj.filenames[
        max(y - repeat_filter, 0) : y + repeat_filter + 1, max(x - repeat_filter, 0) : x + repeat_filter + 1
    ]
    end = time.time()
    # print("surrounding: ", end - start)
    start = time.time()
    if density_match == True:
        density = density_map[pixel[0] // 64, pixel[1] // 64, pixel[2] // 64]
        cdf = color_delta_filter + (100 - 100 * (density - map_min) / (map_max - map_min))
    else:
        cdf = color_delta_filter
    end = time.time()
    # print("checks: ", end - start)
    start = time.time()

    dist = np.linalg.norm(indexed_arr - pixel, axis=1)

    start = time.time()
    dist_arg = np.argsort(dist)
    choice_pics = []

    for i in range(dist.shape[0]):
        if choice_pics and (dist[dist_arg[i]] > cdf):
            break
        else:
            block = color_dict[indexed[dist_arg[i]]]
            if block not in surrounding_pics:
                choice_pics.append(block)
    end = time.time()
    # print("old method: ", end - start)
    # while (not choice_pics) or (dist[i] < cdf):
    #     block = color_dict[indexed[dist[i]]]
    #     if block not in surrounding_pics:
    #         choice_pics.append(block)
    #     i += 1
    # if filt.shape[0] == 0:
    #     dist = np.argsort(dist)
    #     i = 0
    #     while color_dict[indexed[dist[i]]] in surrounding_pics:
    #         i += 1
    #     filt = [dist[i]]
    #     print("filt: ", filt)
    # choice_pics = []
    # for i in filt:
    #     # print(color_dict[indexed[i]], indexed[i])
    #     block = color_dict[indexed[i]]
    #     if block not in surrounding_pics:
    #         choice_pics.append(color_dict[indexed[i]])
    # print(choice_pics)

    # for block in block_dict:
    #     # print("Color: ", color)
    #     color = block_dict[block].get_average()
    #     color_difference = calculate_color_difference(pixel, color, style)
    #     # print("Color Diff: ", color_difference)
    #     # block = color_dict[color]
    #     if block not in surrounding_pics:
    #         if color_difference <= cdf:
    #             delta_images.append((block, color))
    #         if color_difference < min_difference_tracker:
    #             min_difference_images = [(block, color)]
    #             min_difference_tracker = color_difference
    #         elif color_difference == min_difference_tracker:
    #             min_difference_images.append((block, color))
    end = time.time()
    # print("color diff: ", end - start)
    start = time.time()
    # print("Min diff images: " + str(min_difference_images))
    # choice_pics = delta_images if delta_images else min_difference_images
    if shape_match_filter > 0:
        start = time.time()
        if packing_style == "Hex":
            block_width = block_size
            block_height = block_width * 1.1547
            y0 = y + 0.5 if y % 2 == 1 else y
            x0 = x * 0.75
            og_img = reduce_shapes(
                base_image[
                    int(y0 * block_height) : int((y0 + 1) * block_height),
                    int(x0 * block_width) : int((x0 + 1) * block_width),
                ]
            )
        else:
            og_img = reduce_shapes(
                base_image[y * block_size : y * block_size + block_size, x * block_size : x * block_size + block_size]
            )
        end = time.time()
        # print("og reduce: ", end - start)
        start = time.time()
        # print(og_img)
        closest_score = np.inf
        closest_img = None
        # print(
        #     mosaic_obj.filenames[y - repeat_filter : y + repeat_filter + 1, x - repeat_filter : x + repeat_filter + 1]
        # )
        for block in choice_pics:
            # print(block)
            mse = np.mean((og_img - shape_dict[block]) ** 2)
            # print(mse)
            # print(y, x, repeat_filter)
            # print(block)
            if mse < closest_score:
                closest_img = block
                closest_score = mse
        end = time.time()
        # print("mse: ", end - start)
        if closest_score < shape_match_filter:
            result_image = closest_img
        else:
            result_image = random.choice(choice_pics)
    else:
        result_image = random.choice(choice_pics)
    end = time.time()
    # print("choose: ", end - start)
    # print("Result: " + result_image)
    result_color = block_dict[result_image].get_average()
    # print(result_image)
    return result_color, result_image


def color_tilt(matched_color, source_color, target_color_delta):
    """
    Tilt the color of the pic matched pixels to bring their average color closer to the average color of the pixelated base image in that location.
    """
    # print("matched_color", matched_color)
    # print("source_color", source_color)
    # Convert A and B into numpy arrays
    m = np.array(matched_color).astype(np.float32)
    s = np.array(source_color).astype(np.float32)
    # Calculate vector AB
    ms = s - m
    # Calculate the magnitude of vector AB
    magnitude_ms = np.linalg.norm(ms)
    if magnitude_ms < target_color_delta:
        return np.array([0, 0, 0])
    else:
        # Calculate the unit vector in the direction of AB
        unit_vector = ms / magnitude_ms
        # Calculate the coordinates of point C
        newav = s - target_color_delta * unit_vector
        # print("newav", newav)
        # delta = np.clip((m - newav), 0, 255).astype(np.uint8)
        delta = (m - newav).astype(np.int16)
        # delta = np.where(((ms >= 0) & (delta >= 0)) | ((ms < 0) & (delta < 0)), 0, delta)
        return delta


def create_hexagon_mask(image_size):
    """Creates a hexagon mask."""
    img = Image.new("L", image_size, 0)
    draw = ImageDraw.Draw(img)

    cx, cy = img.size[0] // 2, img.size[1] // 2
    hex_radius = min(cx, cy)

    angle_offset = math.pi / 6  # To align the hexagon vertically
    points = [
        (
            cx + hex_radius * math.cos(2 * math.pi * i / 6 + angle_offset),
            cy + hex_radius * math.sin(2 * math.pi * i / 6 + angle_offset),
        )
        for i in range(6)
    ]

    draw.polygon(points, fill=255)

    return img


def crop_to_hexagon(image, mask):
    """Applies the hexagon mask to an image."""
    img = Image.fromarray(image)
    output = Image.new("RGB", img.size)
    output.paste(img, mask=mask)
    return output


def pack_hexagons(hexagon_images, grid_size, mask):
    """Packs hexagonal images into a grid."""
    if not hexagon_images:
        return None

    hex_height = hexagon_images[0].size[1]
    hex_width = int(hex_height * 3**0.5)
    canvas_height = int(hex_height * (grid_size[0] * 0.75 + 0.5))
    canvas_width = int((hex_width * (grid_size[1] + (3**0.5) / 2)) // 2)  # Adjust for hexagonal packing

    canvas = Image.new("RGB", (canvas_width, canvas_height), (255, 255, 255))

    y_offset = 0
    for i, hex_img in enumerate(hexagon_images):
        row = i // grid_size[1]
        col = i % grid_size[1]

        x = col * hex_width // 2
        y = int(row * hex_height * 0.75)
        # print(x, y)

        if row % 2 == 1:
            x += hex_width // 4

        canvas.paste(hex_img, (x, y), mask)

        if col == grid_size[0] - 1:
            y_offset = 0 if y_offset else hex_height // 4
    mosaic_np = np.asarray(canvas)
    # print(mosaic_np.shape)
    return mosaic_np


def pack_images(mosaic_obj, block_dict, block_resolution, style):
    y_images = []
    for y in range(mosaic_obj.height):
        x_images = []
        for x in range(mosaic_obj.width):
            matched_image = block_dict[mosaic_obj.filenames[y, x]].get_pixels().copy()
            tilt_delta = mosaic_obj.tilt_deltas[y, x]
            matched_image = matched_image.astype(np.int16) - tilt_delta.astype(np.int16)
            matched_image = np.clip(matched_image, 0, 255).astype(np.uint8)
            matched_image = cv2.resize(matched_image, (block_resolution, block_resolution)).astype(np.uint8)
            x_images.append(matched_image)
        y_images.append(x_images)
    if style == "Square":
        y_final = []
        for i in y_images:
            y_final.append(np.hstack(i))
        mosaic_np = np.vstack(y_final).astype(np.uint8)
    if style == "Hex":
        s = Image.fromarray(y_images[0][0]).size
        mask = create_hexagon_mask(s)
        hex_images = []
        for i in y_images:
            for j in i:
                hex_images.append(crop_to_hexagon(j, mask))
        mosaic_np = pack_hexagons(hex_images, (mosaic_obj.height, mosaic_obj.width), mask)

    return mosaic_np


def build_mosaic(
    pixelated_source,
    color_dict,
    block_dict,
    shape_dict,
    density_map,
    style,
    color_delta_filter,
    target_color_delta,
    block_resolution,
    shape_match_filter,
    density_match,
    base_image,
    block_size,
    repeat_filter,
    packing_style,
):
    """
    The source image is the pixelated image that is to be used as the map for locating
    all of the blocks. The block resolution is used to size all of the blocks
    consistently and build the mosaic lists.

    TO DO: NEED TO RESIZE THE PIC_MATCH_PIXELS TO MATCH THE BLOCK RESOLUTION
    """
    # print("build mosaic ", repeat_filter)
    h, w, _ = pixelated_source.shape
    mosaic_obj = Mosaic(h, w)
    indexed = {}
    for i, block in enumerate(block_dict):
        indexed[i] = block_dict[block].get_average()
    indexed_arr = np.array(list(indexed.values()))
    if density_match == True:
        map_min = np.min(density_map)
        map_max = np.max(density_map)
    else:
        map_min = None
        map_max = None
    all_pixels_new = []
    for y in range(h):
        x_new = []
        for x in range(w):
            # print(source_pixels[y, x, :])
            source_color = pixelated_source[y, x, :].flatten()
            start = time.time()
            matched_color, matched_image_filename = pic_match(
                source_color,
                color_dict,
                block_dict,
                indexed,
                indexed_arr,
                shape_dict,
                density_map,
                color_delta_filter,
                shape_match_filter,
                density_match,
                map_min,
                map_max,
                base_image,
                block_size,
                x,
                y,
                mosaic_obj,
                repeat_filter,
                packing_style,
            )
            end = time.time()
            # print("match: ", end - start)
            start = time.time()
            if target_color_delta is not None:
                tilt_delta = color_tilt(matched_color, source_color, target_color_delta)
                mosaic_obj.tilt_deltas[y, x] = tilt_delta
            end = time.time()
            # print("tilt: ", end - start)
            start = time.time()
            # print(matched_image_filename)
            mosaic_obj.filenames[y, x] = matched_image_filename
            x_new.append(matched_image_filename)
            end = time.time()
            # print("resize: ", end - start)
            print(f"Processed {y}, {x}")
        start = time.time()
        all_pixels_new.append(x_new)
        end = time.time()
        # print("hstack: ", end - start)
    mosaic_np = pack_images(mosaic_obj, block_dict, block_resolution, packing_style)
    return mosaic_np, mosaic_obj


def rescale_mosaic(mosaic_obj, block_dict, block_res):
    print(block_res)
    all_pixels_new = []
    for y in range(mosaic_obj.height):
        x_new = []
        for x in range(mosaic_obj.width):
            pixels = block_dict[mosaic_obj.filenames[y, x]].get_pixels().copy()
            tilt_delta = mosaic_obj.tilt_deltas[y, x]
            pixels = pixels.astype(np.int16) - tilt_delta.astype(np.int16)
            pixels = np.where(pixels < 0, 0, pixels)
            pixels = np.where(pixels > 255, 255, pixels).astype(np.uint8)
            pixels = cv2.resize(pixels, (block_res, block_res))
            x_new.append(pixels)
            print(f"Processed {y}, {x}")
            # while True:
            #     pass
        all_pixels_new.append(np.hstack(x_new))
    mosaic_np = np.vstack(all_pixels_new).astype(np.uint8)
    return mosaic_np


def main(
    base_image,
    num_blocks_width,
    color_dict,
    block_dict,
    shape_dict,
    density_map,
    color_delta_filter,
    target_color_delta,
    block_resolution,
    shape_match_filter,
    density_match,
    repeat_filter,
    packing_style,
):
    print(color_dict)
    print("Pixelating Image")
    # print("main ", repeat_filter)
    pixelated_source, block_size = generate_pixelated_image(base_image, num_blocks_width, packing_style)
    print("Building Mosaic")
    mosaic_np, mosaic_obj = build_mosaic(
        pixelated_source,
        color_dict,
        block_dict,
        shape_dict,
        density_map,
        "color",
        color_delta_filter,
        target_color_delta,
        block_resolution,
        shape_match_filter,
        density_match,
        base_image,
        block_size,
        repeat_filter,
        packing_style,
    )
    # print(mosaic_obj.filenames)
    print("code complete")
    print(np.where(mosaic_obj.filenames == "0step_3.png"))
    return mosaic_np, mosaic_obj
