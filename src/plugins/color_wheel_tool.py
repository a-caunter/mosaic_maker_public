from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
)
from layer_class import Layer
from event_manager import Event
import ui.ui_styles as ui_styles
import numpy as np


module_name = "ColorWheelTool"


def register(plugin_manager):
    plugin_manager.register_plugin(module_name, "Tool for creating color gradients", ColorWheelTool)


class ColorWheelTool(Layer):
    def __init__(self, name, event_manager):
        super(ColorWheelTool, self).__init__()
        self.type = module_name
        self.name = name
        self.event_manager = event_manager

        self.create_canvas()
        self.create_right_frame()

        self.layout.setColumnStretch(0, 1)
        self.layout.setColumnStretch(1, 0)

        # Gradient paramters
        self.width = None
        self.height = None
        self.saturation = None
        self.value = None

    def configure(self):
        self.event_manager.register(GetConfigData(self.name))

    def create_right_frame(self):
        self.right_frame = QVBoxLayout()

        # Image Height
        self.height_label = QLabel("Height")
        self.height_label.setStyleSheet(ui_styles.label_style)
        self.right_frame.addWidget(self.height_label)
        self.height_entry = QLineEdit()
        self.height_entry.setStyleSheet(ui_styles.line_edit_style)
        self.right_frame.addWidget(self.height_entry)

        # Image width
        self.width_label = QLabel("Width")
        self.width_label.setStyleSheet(ui_styles.label_style)
        self.right_frame.addWidget(self.width_label)
        self.width_entry = QLineEdit()
        self.width_entry.setStyleSheet(ui_styles.line_edit_style)
        self.right_frame.addWidget(self.width_entry)

        # Saturation
        self.saturation_label = QLabel("Saturation")
        self.saturation_label.setStyleSheet(ui_styles.label_style)
        self.right_frame.addWidget(self.saturation_label)
        self.saturation_entry = QLineEdit()
        self.saturation_entry.setStyleSheet(ui_styles.line_edit_style)
        self.right_frame.addWidget(self.saturation_entry)

        # Value
        self.value_label = QLabel("Value")
        self.value_label.setStyleSheet(ui_styles.label_style)
        self.right_frame.addWidget(self.value_label)
        self.value_entry = QLineEdit()
        self.value_entry.setStyleSheet(ui_styles.line_edit_style)
        self.right_frame.addWidget(self.value_entry)

        # Create Color Wheel Button
        self.button_create_color_wheel = QPushButton("Create Color Wheel")
        self.button_create_color_wheel.setStyleSheet(ui_styles.button_style)
        self.button_create_color_wheel.clicked.connect(self.spiral_color_wheel)
        self.right_frame.addWidget(self.button_create_color_wheel)

        self.right_frame.addStretch()

        # Setup the right frame widget
        self.right_frame_widget = QWidget()
        self.right_frame_widget.setLayout(self.right_frame)

        self.layout.addWidget(self.right_frame_widget, 0, 1)

    # SETTERS and GETTERS ------------------------------------------------------------

    # TOOL FUNCTONS ---------------------------------------------------------------

    def get_wheel_arguments(self):
        self.width = self.width_entry.text()
        self.width = int(self.width) if self.width else None
        self.height = self.height_entry.text()
        self.height = int(self.height) if self.height else None
        self.saturation = self.saturation_entry.text()
        self.saturation = int(self.saturation) / 100 if self.saturation else None
        self.value = self.value_entry.text()
        self.value = int(self.value) / 100 if self.value else None

    def create_spiral_rainbow_color_wheel(self):
        def hsv_to_rgb(h, s, v):
            if s == 0.0:
                return v, v, v
            i = int(h * 6.0)  # Assume H ∈ [0, 1]
            f = (h * 6.0) - i
            p, q, t = v * (1.0 - s), v * (1.0 - s * f), v * (1.0 - s * (1.0 - f))
            i = i % 6
            if i == 0:
                return v, t, p
            if i == 1:
                return q, v, p
            if i == 2:
                return p, v, t
            if i == 3:
                return p, q, v
            if i == 4:
                return t, p, v
            if i == 5:
                return v, p, q

        image = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        center_y, center_x = self.height // 2, self.width // 2
        radius = min(center_x, center_y)

        for y in range(self.height):
            for x in range(self.width):
                dy, dx = y - center_y, x - center_x
                distance = np.sqrt(dx**2 + dy**2)
                angle = np.arctan2(dy, dx) if distance != 0 else 0

                normalized_distance = distance / radius
                normalized_angle = (angle + np.pi) / (2 * np.pi)

                # Using HSV to RGB conversion
                # print(normalized_angle)
                # print(self.saturation)
                # print(self.value)
                color = hsv_to_rgb(normalized_angle, self.saturation, self.value)
                image[y, x] = [int(c * 255) for c in color]

        self.canvas_image = image
        self.update_canvas()

    def spiral_color_wheel(self):
        self.get_wheel_arguments()
        if self.width is None:
            self.event_manager.register(MosaicFailed("missing_width"))
        elif self.height is None:
            self.event_manager.register(MosaicFailed("missing_height"))
        elif self.saturation is None:
            self.event_manager.register(MosaicFailed("missing_saturation"))
        elif self.value is None:
            self.event_manager.register(MosaicFailed("missing_value"))
        else:
            self.create_spiral_rainbow_color_wheel()

    # SAVE AND LOAD -------------------------------------------------------------------

    def save_state(self):
        # This dict recreates the object; numpy points to numpy arrays that need to be loaded and assigned to object attributes
        data = {
            "data": {
                "type": self.type,
                "name": self.name,
                "height": self.height,
                "width": self.width,
                "saturation": self.saturation,
                "value": self.value,
            },
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
                print(attribute)
                self.event_manager.register(LoadDataFromSave(self.name, attribute, data_name))
        self.update_canvas()
        self.populate_fields()

    def load_attribute(self, attribute, data):
        setattr(self, attribute, data)

    def populate_fields(self):
        self.height_entry.setText(str(self.height))
        self.width_entry.setText(str(self.width))
        self.saturation_entry.setText(str(self.saturation))
        self.value_entry.setText(str(self.value))


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
        # self.modules[self.name].set_lib_classification(cfg["lib_classification"])
        self.modules[self.name].set_working_directory(cfg["working_directory"])
        self.modules["UserInterface"].update_log_stream()


class LoadDataFromSave(Event):
    def __init__(self, name, attribute, array_name):
        super(LoadDataFromSave, self).__init__()
        self.module = module_name
        self.name = name
        self.title = "load_array_from_save"
        self.listeners = None
        self.attribute = attribute
        self.array_name = array_name

    def emit(self):
        arr = self.modules["FileHandler"].retreive_data(self.array_name)
        self.modules[self.name].load_attribute(self.attribute, arr)


class MosaicFailed(Event):
    def __init__(self, report):
        super(MosaicFailed, self).__init__()
        self.module = module_name
        self.title = f"mosaic_failed_{report}"
        self.listeners = None

    def emit(self):
        self.modules["UserInterface"].update_log_stream()
