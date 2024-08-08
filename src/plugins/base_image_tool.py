import os
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QFileDialog,
)
from layer_class import Layer
from event_manager import Event
import numpy as np
from PIL import Image
import ui.ui_styles as ui_styles
from mosaic_util.image_utility import image_smart_open


module_name = "BaseImageTool"

script_dir = os.path.dirname(os.path.abspath(__file__))


def register(plugin_manager):
    plugin_manager.register_plugin(
        "BaseImageTool", "Tool for loading and manipulating a Base Image Layer", BaseImageTool
    )


class BaseImageTool(Layer):
    def __init__(self, name, event_manager):
        super(BaseImageTool, self).__init__()
        self.type = "BaseImageTool"
        self.name = name
        self.event_manager = event_manager

        self.canvas_image_path = None

        self.create_canvas()
        self.create_right_frame()

        self.layout.setColumnStretch(0, 1)
        self.layout.setColumnStretch(1, 0)

    def configure(self):
        self.event_manager.register(GetConfigData(self.name))

    def create_right_frame(self):
        self.right_frame = QVBoxLayout()

        # Open Base Image Button
        self.button_open_base_image = QPushButton("Open Base Image")
        self.button_open_base_image.setStyleSheet(ui_styles.button_style)
        self.button_open_base_image.clicked.connect(self.open_base_image)
        self.right_frame.addWidget(self.button_open_base_image)

        self.right_frame.addStretch()

        # Setup the right frame
        self.right_frame_widget = QWidget()
        self.right_frame_widget.setLayout(self.right_frame)
        self.layout.addWidget(self.right_frame_widget, 0, 1)

    # SETTERS and GETTERS ------------------------------------------------------------

    # TOOL FUNCTONS ---------------------------------------------------------------

    def open_base_image(self):
        print("clicked")
        filepath, _ = QFileDialog.getOpenFileName(
            self.tool_widget,
            "Select Base Image",
            self.working_directory,
            "Image files (*.png *.jpg *.jpeg *.bmp);;All Files (*)",
        )
        if filepath:
            self.canvas_image_path = filepath
            # Need to copy to avoid memoryview type after slicing
            img = image_smart_open(filepath)
            self.canvas_image = np.asarray(img)[:, :, :3].copy()
            self.update_canvas()
            self.event_manager.register(BaseImageSelected(filepath))

    # SAVE AND LOAD -------------------------------------------------------------------

    def save_state(self):
        # This dict recreates the object; numpy points to numpy arrays that need to be loaded and assigned to object attributes
        data = {
            "data": {"type": self.type, "name": self.name, "canvas_image_path": self.canvas_image_path},
            "big_data": {"canvas_image": None},
        }
        # This dict will assign file save names to the numpy arrays that we need to save
        big_data_files = {}
        if self.canvas_image is not None:
            data["big_data"]["canvas_image"] = f"{self.name}_canvas_image.npy"
            big_data_files[f"{self.name}_canvas_image.npy"] = self.canvas_image
        return data, big_data_files

    def load_state(self, data):
        print(data)
        for key, value in data["data"].items():
            if hasattr(self, key):
                # print("have")
                setattr(self, key, value)
        for attribute, data_name in data["big_data"].items():
            if hasattr(self, attribute):
                self.event_manager.register(LoadArrayFromSave(self.name, attribute, data_name))
        self.update_canvas()

    def load_attribute(self, attribute, data):
        setattr(self, attribute, data)
        # print(self.canvas_image)


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


class BaseImageSelected(Event):
    def __init__(self, filepath):
        super(BaseImageSelected, self).__init__()
        self.module = module_name
        self.title = "base_image_selected"
        self.listeners = None
        self.filepath = filepath

    def emit(self):
        # TODO: Tell the workplace manager that the layer was created?
        # self.modules["UserInterface"].update_log_stream()
        pass


class LoadArrayFromSave(Event):
    def __init__(self, name, attribute, array_name):
        super(LoadArrayFromSave, self).__init__()
        self.module = module_name
        self.name = name
        self.title = "load_array_from_save"
        self.listeners = None
        self.attribute = attribute
        self.array_name = array_name

    def emit(self):
        arr = self.modules["FileHandler"].retreive_data(self.array_name)
        self.modules[self.name].load_attribute(self.attribute, arr)
