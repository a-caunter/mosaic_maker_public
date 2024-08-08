import os
import sys
from PyQt6.QtWidgets import (
    QWidget,
    QScrollArea,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QFileDialog,
    QPushButton,
)
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QRect
import time
import ui.ui_styles as ui_styles
from event_manager import Event
import json

from mosaic_util import classify_image_library as cli

# from autocrop import autocropper

module_name = "library_viewer"


def register(plugin_manager):
    plugin_manager.register_plugin("LibraryViewer", "Tool for viewing image library", LibraryViewer)


class LibraryViewer(QWidget):
    def __init__(self, name, event_manager):
        super().__init__()
        self.type = "LibraryViewer"
        self.name = name
        self.event_manager = event_manager
        self.working_directory = r"C:\Users"
        self.image_directory = self.working_directory
        self.tool_widget = self

        self.layout = QGridLayout(self)
        self.create_library_view()
        self.create_right_frame()

        self.layout.setColumnStretch(0, 1)
        self.layout.setColumnStretch(1, 0)

        self.count = 0
        self.im_count = 0
        self.done = False
        self.active_thread = None

        self.crops_shown = False

    def create_library_view(self):
        # Layout for the main widget
        self.lib_view = QGridLayout(self)

        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        # Widget for containing image thumbnails
        self.image_container = QWidget()
        self.image_layout = QGridLayout()
        for r in range(5):
            self.image_layout.setRowStretch(r, 1)
        for c in range(5):
            self.image_layout.setColumnStretch(c, 0)
        self.image_container.setLayout(self.image_layout)
        self.scroll_area.setWidget(self.image_container)
        self.lib_view.addWidget(self.scroll_area)

        self.lib_view_widget = QWidget()
        self.lib_view_widget.setLayout(self.lib_view)

        self.layout.addWidget(self.lib_view_widget, 0, 0)

    def create_right_frame(self):
        self.right_frame = QVBoxLayout()

        # Select Image Library Button
        self.button_select_library = QPushButton("Select Image Library")
        self.button_select_library.setStyleSheet(ui_styles.button_style)
        self.button_select_library.clicked.connect(self.select_image_library)
        self.right_frame.addWidget(self.button_select_library)

        # Load Images
        self.button_load_images = QPushButton("Load Images")
        self.button_load_images.setStyleSheet(ui_styles.button_style)
        self.button_load_images.clicked.connect(self.load_images)
        self.right_frame.addWidget(self.button_load_images)

        # Run Autocropper - commented out for public repo
        # self.button_load_images = QPushButton("Run Autocropper")
        # self.button_load_images.setStyleSheet(ui_styles.button_style)
        # self.button_load_images.clicked.connect(self.run_autocropper)
        # self.right_frame.addWidget(self.button_load_images)

        # Show/Hide Crops
        self.button_show_hide_crops = QPushButton("Show/Hide Crops")
        self.button_show_hide_crops.setStyleSheet(ui_styles.button_style)
        self.button_show_hide_crops.clicked.connect(self.show_hide_crops)
        self.right_frame.addWidget(self.button_show_hide_crops)

        # Create Image Library Classification
        self.button_image_class = QPushButton("Create Image Library Classification")
        self.button_image_class.setStyleSheet(ui_styles.button_style)
        self.button_image_class.clicked.connect(self.create_image_class)
        self.right_frame.addWidget(self.button_image_class)

        self.right_frame.addStretch()

        # Setup the right frame widget
        self.right_frame_widget = QWidget()
        self.right_frame_widget.setLayout(self.right_frame)

        self.layout.addWidget(self.right_frame_widget, 0, 1)

    def set_working_directory(self, path):
        self.working_directory = path
        self.image_directory = path

    def select_image_library(self):
        # Load image paths
        dir = QFileDialog.getExistingDirectory(self, "Select Image Library", self.image_directory)
        if dir:
            self.image_directory = dir
            self.files = os.listdir(self.image_directory)
            print(len(self.files))

    def load_images(self):
        loader_thread = ImageLoaderThread(self.image_directory)
        loader_thread.image_loaded.connect(self.on_image_loaded)
        loader_thread.finished.connect(self.thread_finished)
        self.active_thread = loader_thread
        loader_thread.start()

    # def run_autocropper(self):
    #     autocropper.main(self.image_directory)
    #     # pass

    def show_hide_crops(self):
        if self.crops_shown:
            self.crops_shown = False
            for i in range(self.image_layout.count()):
                # print(f"{i} --------------------------------------------------------------")
                item = self.image_layout.itemAt(i)
                widget = item.widget()
                widget.crops_shown = False
                widget.update()
        else:
            files = os.listdir(self.image_directory)
            if "lib.crop" in files:
                self.crops_shown = True
                with open(os.path.join(self.image_directory, "lib.crop"), "r") as json_file:
                    crops = json.load(json_file)
                for i in range(self.image_layout.count()):
                    # print(f"{i} --------------------------------------------------------------")
                    item = self.image_layout.itemAt(i)
                    widget = item.widget()
                    name = widget.filename
                    xl, yl, xr, yr = crops[name]
                    widget.set_crop_rect(xl, yl, xr, yr)

    def create_image_class(self):
        files = os.listdir(self.image_directory)
        if "lib.crop" in files:
            with open(os.path.join(self.image_directory, "lib.crop"), "r") as json_file:
                crops = json.load(json_file)
            cli.main(self.image_directory, crops)
        else:
            print("No lib.crop file")
            cli.main(self.image_directory, None)

    def on_image_loaded(self, filename, pixmap, width_original, height_orignal, r, c):
        label = ImageLabel(filename, width_original, height_orignal)
        label.setPixmap(pixmap)
        self.image_layout.addWidget(label, r, c)

    def thread_finished(self):
        self.active_thread = None

    def get_tool_widget(self):
        return self

    def configure(self):
        self.event_manager.register(GetConfigData(self.name))

    def update(self):
        pass

    def save_state(self):
        return None, None

    def load_state(self):
        pass


class CustomScrollArea(QScrollArea):
    def __init__(self, parent):
        super(CustomScrollArea, self).__init__()
        self.parent = parent

    def wheelEvent(self, event):
        super().wheelEvent(event)
        if self.parent.done != True:
            if self.verticalScrollBar().value() == self.verticalScrollBar().maximum():
                self.parent.loadImagePaths(30)


class ImageLoaderThread(QThread):
    image_loaded = pyqtSignal(str, QPixmap, int, int, int, int)

    def __init__(self, folder):
        QThread.__init__(self)
        self.folder = folder
        self.im_count = 0

    def run(self):
        start = time.time()
        num_ims_width = 5
        files = os.listdir(self.folder)
        for file in files:
            if file.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp")):
                image_path = os.path.join(self.folder, file)
                pixmap = QPixmap(image_path)
                width_original = pixmap.width()
                height_original = pixmap.height()
                pixmap = pixmap.scaled(
                    200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                )
                r = self.im_count // num_ims_width
                c = self.im_count - (r * num_ims_width)
                self.im_count += 1
                self.image_loaded.emit(file, pixmap, width_original, height_original, r, c)
                time.sleep(0.01)
        print(time.time() - start)


class ImageLabel(QLabel):
    def __init__(self, filename, width_original, height_original, parent=None):
        super().__init__(parent)
        self.filename = filename
        self.width_original = width_original
        self.height_original = height_original
        self.crop_rect = None  # Initialize a variable for the cropping rectangle
        self.crops_shown = False

    def set_crop_rect(self, xl, yl, xr, yr):
        self.crops_shown = True
        p = self.pixmap()
        if p:
            # print(xl, yl, xr, yr)
            w = p.width()
            h = p.height()
            scale = max(w, h)
            ratio = max(self.width_original, self.height_original) / scale
            # print(self.width_original)
            # print(self.height_original)
            # print(scale)
            # print(ratio)
            xl_o = int(xl / ratio)
            yl_o = int(((scale - h) / 2) + (yl / ratio))
            xr_o = int(xr / ratio) - xl_o
            yr_o = int(yl_o + ((yr - yl) / ratio)) - yl_o
            # print(xl_o, yl_o, xr_o, yr_o)
            self.crop_rect = QRect(xl_o, yl_o, xr_o, yr_o)  # Set the rectangle dimensions
            self.update()  # Trigger a repaint

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        pen = QPen(QColor(255, 255, 255), 1)  # white color, 1 pixels thick
        painter.setPen(pen)
        p = self.pixmap()
        d = max(p.width(), p.height())
        painter.drawRect(QRect(0, 0, d, d))  # Draw the rectangle
        if self.crops_shown and self.crop_rect:  # Check if a cropping rectangle is set
            # painter = QPainter(self)
            pen = QPen(QColor(255, 0, 0), 3)  # Red color, 3 pixels thick
            painter.setPen(pen)
            painter.drawRect(self.crop_rect)  # Draw the rectangle


# class ImageLabel(QLabel):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.crop_rect = None
#         self.pixmap = None

#     def setPixmap(self, pixmap):
#         self.pixmap = pixmap
#         self.update()

#     def set_crop_rect(self, xl, yl, xr, yr):
#         self.crop_rect = QRect(xl, yl, xr, yr)
#         self.update()

#     def paintEvent(self, event):
#         if self.pixmap:
#             painter = QPainter(self)
#             # Calculate the top-left position for centering the pixmap
#             x = (self.width() - self.pixmap.width()) // 2
#             y = (self.height() - self.pixmap.height()) // 2
#             painter.drawPixmap(x, y, self.pixmap)

#             if self.crop_rect:
#                 pen = QPen(QColor(255, 0, 0), 3)
#                 painter.setPen(pen)
#                 painter.drawRect(self.crop_rect)

#             painter.end()
#         else:
#             super().paintEvent(event)


# EVENTS FROM THIS MODULE ----------------------------------------------------------------------------------


class GetConfigData(Event):
    def __init__(self, name):
        super(GetConfigData, self).__init__()
        self.module = module_name
        self.name = name
        self.title = "get_config_data"
        self.listeners = None

    def emit(self):
        cfg = self.modules["ConfigManager"].get_config()
        self.modules[self.name].set_working_directory(cfg["working_directory"])
        self.modules["UserInterface"].update_log_stream()
