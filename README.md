# MosaicMaker

An application for creating photographic mosaics from local image libraries. Reviving dormant libraries of your personal photos.

Read about [photographic mosaics](https://en.wikipedia.org/wiki/Photographic_mosaic).

MosaicMaker is written entirely in Python and is based on the PyQt application framework.

## Installation

Compatible with Python 3.11

Install the required packages:
`pip install -r requirements.txt`

## Usage

Note that all syntax is specific to Windows.

Follow the steps below to launch and use the application:

1. Locate "session_config.json" in '<repo directory>/src/', open it, and change the "working directory" to `<repo directory>/example/`.

2. From the repo directory, lauch the file `python src/mosaic_maker.py`. A GUI titled "Mosaic Maker" appears, and the terminal should read "No more events". 

3. In the top right of the Mosaic Maker window, find the + button. Click the + button and add a BaseImageTool from the dropdown. The BaseImageTool will appear as a tab inside the application "workspace".

4. With the BaseImageTool tab selected, click "Open Base Image" and Open "example_base_image.jpg" from `<repo directory>/example/`, or any other image file you'd like from your local storage. For good results, the remainder of this procedure assumes you opened "example_base_image.jpg".

5. Click the + button in the top right, and add a MosaicTool from the dropdown. The tab will appear.

6. Note: MosaicMaker uses custom library classification files to store information about a library of images for fast access. This repo is delivered with a sample library classification file from a library of images I shot during a ski day at Brighton Resort.
    - Inside the MosaicTool tab, click "Load Library Classification" and open "lib_classification.pkl" from `<repo directory>/example/`.

8. Click "Load" next to "Select Base Image". If you had multiple BaseImageTools open, they would be selectable from the dropdown.

9. Fill in the fields with the following values:
    - Block Resolution: 256
    - Num Blocks Width: 32
    - Color Delta Filter: 100
    - Target Color Delta: 50
    - Shape Match Filter: 0
    - Image Repeat Filter: 0

10. Click "Build Mosaic".
    - The application will be frozen while the mosaic is built, but you can confirm the process is happening by observing the readout on the terminal. The mosaic will appear in the MosaicTool window when complete.
    - Don't expect it to be anything special at this point! But it should have been fast.

12. For better results, enter the following values in the fields. Processing will take longer, but should be under a minute.
    - Block Resolution: 256
    - Num Blocks Width: 32
    - Color Delta Filter: 100
    - Target Color Delta: 50
    - Shape Match Filter: 100
    - Image Repeat Filter: 6

Using Shape Matching forces the algorithm to select an image that fits the underlying shape of the base image, increasing likeness.

Play around with values and have fun!

Note: It is possible to lock up your computer by comsuming all available memory. This happens when too many image pixels are being processed, for example by making the "Num Blocks Width" value far too high. Force close the program - memory is released. 

## Additional Features

Save and Load: To Save the active session of MosaicMaker, use the "Save Session" button in the top left, shaped like a floppy disk. To Open a session, use the "Open Session" button in the top left.

Save the Canvas: To save the active tab's display as a PNG (i.e. save the MosaicTool result), click the "Save Active Canvas" button in the top left.

Delete tabs: Right click on the tab and select "Delete".

## Project Status

This is a hobby project for demonstrating my software development abilities. More features may be added in the future.

## License

This project is licensed under the MIT License




