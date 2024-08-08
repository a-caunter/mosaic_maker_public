import pickle
import os
import sys
import numpy as np

# import matplotlib.pyplot as plt
# from mpl_toolkits.mplot3d import Axes3D
from PIL import Image


import mosaic_util.image_utility as util


class Block(object):
    """
    a block is a decoded png image
    """

    def __init__(self, name, pixels, style):
        self.name = name
        self.pixels = pixels
        self.average = None
        self.style = style

    def get_name(self):
        return self.name

    def get_pixels(self):
        return self.pixels

    def get_style(self):
        return self.style

    def color_average(self):
        """
        sets the attribute self.average as integer value of the average of all
        pixel greyscale values
        """
        if self.get_style() == "greyscale":
            self.average = np.mean(self.pixels).round().astype(np.int32)
        elif self.get_style() == "color":
            self.average = tuple(np.mean(self.pixels, axis=(0, 1)).round().astype(np.int32))

    def get_average(self):
        return self.average


def create_block(image, name, style):
    """
    create a block object from an image
    """
    block = Block(name, image, style)
    block.color_average()
    return block


def generate_block_list(path, crops, style):
    """
    generate a list that contains all of the block objects created from images
    stroed at the location "path". Style will be "color" or "greyscale".
    """
    image_names = os.listdir(path)
    block_list = []
    for item in image_names:
        if item.endswith((".png", ".jpg")):
            if style == "greyscale":
                image = util.load_greyscale_image(os.path.join(path, item))
            elif style == "color":
                image = util.image_smart_open(os.path.join(path, item))
            else:
                print("Style not accepted")
                block_list = None
                break
            if crops is not None:
                cropped_image = image.crop(crops[item])
            else:
                cropped_image = image
            final_image = cropped_image.resize((256, 256), Image.BICUBIC)
            block = create_block(np.asarray(final_image).astype(np.uint8), item, style)
            block_list.append(block)
            del block
    return block_list


def pickle_it(obj, filename):
    with open(filename, "wb") as outp:  # Overwrites any existing file.
        pickle.dump(obj, outp, 0)


def pickle_loader(filename):
    with open(filename, "rb") as inp:
        print(filename)
        block_list = pickle.load(inp)
    return block_list


def generate_density_map(block_list):
    split = 64
    count_array = np.zeros((int(256 / split), int(256 / split), int(256 / split)))
    for item in block_list:
        r, g, b = item.get_average()
        count_array[r // split, g // split, b // split] += 1
    density_scale = generate_density_scale()
    mid = density_scale.shape[0] // 2
    density_map = np.zeros_like(count_array)
    r, c, d = density_map.shape
    for i in range(r):
        for j in range(c):
            for k in range(d):
                density_map[i, j, k] = np.sum(
                    density_scale[mid - i : mid - i + 4, mid - j : mid - j + 4, mid - k : mid - k + 4] * count_array
                )
    return density_map, count_array


def generate_color_dict(block_list):
    """
    create a dictionary where the keys are a greyscale value and the values
    are a list of blocks whose self.average is equal to that key.
    """
    color_dict = {}
    for item in block_list:
        color_dict[item.get_average()] = item.get_name()
    return color_dict


def reduce_shapes(base_image):
    slices = 12
    width = base_image.shape[1] // slices
    conv = np.zeros((slices, slices))
    for r in range(slices):
        for c in range(slices):
            # conv[r, c] = np.mean(base_image[r * width : r * width + width, c * width : c * width + width, :])
            conv[r, c] = np.mean(
                np.sum(
                    base_image[r * width : r * width + width, c * width : c * width + width, :]
                    * np.array([0.299, 0.587, 0.114]).reshape(1, 1, 3),
                    axis=2,
                )
            )
    max_val = np.max(conv)
    min_val = np.min(conv)
    min_val += 1e-6 if min_val == max_val else min_val
    conv_std = (conv - min_val) / (max_val - min_val)
    return conv_std


# def reduce_shapes(base_image):
#     slices = 12
#     width = base_image.shape[1] // slices
#     conv = np.zeros((slices, slices, 3))
#     for r in range(slices):
#         for c in range(slices):
#             conv[r, c, :] = np.mean(
#                 base_image[r * width : r * width + width, c * width : c * width + width, :], axis=(0, 1)
#             )
#     # max_val = np.max(conv)
#     # min_val = np.min(conv)
#     # min_val += 1e-6 if min_val == max_val else min_val
#     # conv_std = (conv - min_val) / (max_val - min_val)
#     # return conv_std
#     return conv


def generate_shape_dict(block_list):
    shape_dict = {}
    for item in block_list:
        shape_dict[item.get_name()] = reduce_shapes(item.get_pixels())
    return shape_dict


def generate_density_scale():
    density_scale = np.zeros((5, 5, 5))  # 442 is max 3d dist in color space. 222 in 8 blocks overlaps color space
    r, c, d = density_scale.shape
    # print(r, c, d)
    for i in range(r):
        for j in range(c):
            for k in range(d):
                if i == 0 and j == 0 and k == 0:
                    density_scale[i, j, k] = 1
                else:
                    density_scale[i, j, k] = 1 / ((i**2 + j**2 + k**2) ** 0.5)  # 1/dist
    v_flip = np.flip(density_scale, axis=0)
    density_scale = np.concatenate((v_flip, density_scale[1:, :, :]), axis=0)
    h_flip = np.flip(density_scale, axis=1)
    density_scale = np.concatenate([h_flip, density_scale[:, 1:, :]], axis=1)
    d_flip = np.flip(density_scale, axis=2)
    density_scale = np.concatenate([d_flip, density_scale[:, :, 1:]], axis=2)
    # print("density_scale_shape", density_scale.shape)
    return density_scale


def generate_block_dict(block_list):
    block_dict = {}
    for item in block_list:
        block_dict[item.get_name()] = item
        # print(block_dict[item.get_name()].get_name())
    return block_dict


# def plot_data(data):
#     x, y, z, values = [], [], [], []
#     for i in range(data.shape[0]):
#         for j in range(data.shape[1]):
#             for k in range(data.shape[2]):
#                 x.append(i)
#                 y.append(j)
#                 z.append(k)
#                 values.append(data[i, j, k])

#     # Converting lists to NumPy arrays for better performance with Matplotlib
#     x = np.array(x)
#     y = np.array(y)
#     z = np.array(z)
#     values = np.array(values)

#     scaled_values = (values - values.min()) / (values.max() - values.min())
#     dot_sizes = scaled_values * 100  # Scaling factor for dot size

#     # Creating the figure
#     fig = plt.figure()
#     ax = fig.add_subplot(111, projection="3d")

#     # Creating the scatter plot
#     scatter = ax.scatter(x, y, z, c=values, s=dot_sizes, cmap="viridis")

#     # Adding a color bar
#     cbar = plt.colorbar(scatter)
#     cbar.set_label("Values")

#     # Setting labels
#     ax.set_xlabel("X Axis")
#     ax.set_ylabel("Y Axis")
#     ax.set_zlabel("Z Axis")

#     # Showing the plot
#     plt.show()


def main(directory, crops):
    # CREATING THE BLOCK LIST PICKLE FILE
    print("Generating Block List")
    block_list = generate_block_list(directory, crops, "color")

    print("Generating Color Dict")
    color_dict = generate_color_dict(block_list)

    print("Generating Density Map")
    density_map, count_array = generate_density_map(block_list)
    # print("count", np.min(count_array), np.max(count_array))
    # print("dmap", np.min(density_map), np.max(density_map))
    # print("Plotting")
    # plot_data(count_array)
    # plot_data(density_map)

    print("Generating Shape Dict")
    shape_dict = generate_shape_dict(block_list)

    print("Generating Block Dict")
    block_dict = generate_block_dict(block_list)
    print("Pickling Lib Classification")
    lib_classification = {
        "block_dict": block_dict,
        "color_dict": color_dict,
        "density_map": density_map,
        "shape_dict": shape_dict,
    }
    pickle_it(lib_classification, os.path.join(directory, "lib_classification.pkl"))
    print("Done")
