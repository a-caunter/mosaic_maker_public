from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QGridLayout,
    QColorDialog,
    QFileDialog,
)
from PyQt6.QtGui import QColor
import mosaic_util.classify_image_library as cli
from layer_class import Layer
from event_manager import Event
import ui.ui_styles as ui_styles
import numpy as np


module_name = "GradientTool"


def register(plugin_manager):
    plugin_manager.register_plugin(module_name, "Tool for creating color gradients", GradientTool)


class GradientTool(Layer):
    def __init__(self, name, event_manager):
        super(GradientTool, self).__init__()
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
        self.ul_r = None
        self.ul_g = None
        self.ul_b = None
        self.ur_r = None
        self.ur_g = None
        self.ur_b = None
        self.ll_r = None
        self.ll_g = None
        self.ll_b = None
        self.ul = None
        self.ur = None
        self.ll = None
        self.selected_color = None

    def configure(self):
        self.event_manager.register(GetConfigData(self.name))

    def create_right_frame(self):
        self.right_frame = QVBoxLayout()

        # Load Library Classification Button
        self.button_load_lib_class = QPushButton("Load Library Classification")
        self.button_load_lib_class.setStyleSheet(ui_styles.button_style)
        self.button_load_lib_class.clicked.connect(self.load_library_classification)
        self.right_frame.addWidget(self.button_load_lib_class)

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

        # Upper Left Color
        self.ul = QGridLayout()
        self.ul.setColumnStretch(1, 0)
        self.ul.setColumnStretch(1, 1)
        self.ul.setColumnStretch(2, 1)
        self.ul.setColumnStretch(3, 1)
        self.ul_label = QLabel("Upper Left")
        self.ul_label.setStyleSheet(ui_styles.label_style)
        self.ul.addWidget(self.ul_label, 0, 0)
        self.ul_r_entry = QLineEdit()
        self.ul_r_entry.setStyleSheet(ui_styles.line_edit_style)
        self.ul.addWidget(self.ul_r_entry, 0, 1)
        self.ul_g_entry = QLineEdit()
        self.ul_g_entry.setStyleSheet(ui_styles.line_edit_style)
        self.ul.addWidget(self.ul_g_entry, 0, 2)
        self.ul_b_entry = QLineEdit()
        self.ul_b_entry.setStyleSheet(ui_styles.line_edit_style)
        self.ul.addWidget(self.ul_b_entry, 0, 3)
        # Open Color Selector
        self.ul_color_select = QPushButton("Color")
        self.ul_color_select.setStyleSheet(ui_styles.button_style)
        self.ul_color_select.clicked.connect(self.set_ul_color)
        self.ul.addWidget(self.ul_color_select, 0, 4)
        self.ul_widget = QWidget()
        self.ul_widget.setLayout(self.ul)
        self.right_frame.addWidget(self.ul_widget)

        # Upper Right Color
        self.ur = QGridLayout()
        self.ur.setColumnStretch(1, 0)
        self.ur.setColumnStretch(1, 1)
        self.ur.setColumnStretch(2, 1)
        self.ur.setColumnStretch(3, 1)
        self.ur_label = QLabel("Upper Right")
        self.ur_label.setStyleSheet(ui_styles.label_style)
        self.ur.addWidget(self.ur_label, 0, 0)
        self.ur_r_entry = QLineEdit()
        self.ur_r_entry.setStyleSheet(ui_styles.line_edit_style)
        self.ur.addWidget(self.ur_r_entry, 0, 1)
        self.ur_g_entry = QLineEdit()
        self.ur_g_entry.setStyleSheet(ui_styles.line_edit_style)
        self.ur.addWidget(self.ur_g_entry, 0, 2)
        self.ur_b_entry = QLineEdit()
        self.ur_b_entry.setStyleSheet(ui_styles.line_edit_style)
        self.ur.addWidget(self.ur_b_entry, 0, 3)
        # Open Color Selector
        self.ur_color_select = QPushButton("Color")
        self.ur_color_select.setStyleSheet(ui_styles.button_style)
        self.ur_color_select.clicked.connect(self.set_ur_color)
        self.ur.addWidget(self.ur_color_select, 0, 4)
        self.ur_widget = QWidget()
        self.ur_widget.setLayout(self.ur)
        self.right_frame.addWidget(self.ur_widget)

        # Lower Left Color
        self.ll = QGridLayout()
        self.ur.setColumnStretch(1, 0)
        self.ur.setColumnStretch(1, 1)
        self.ur.setColumnStretch(2, 1)
        self.ur.setColumnStretch(3, 1)
        self.ll_label = QLabel("Lower Left")
        self.ll_label.setStyleSheet(ui_styles.label_style)
        self.ll.addWidget(self.ll_label, 0, 0)
        self.ll_r_entry = QLineEdit()
        self.ll_r_entry.setStyleSheet(ui_styles.line_edit_style)
        self.ll.addWidget(self.ll_r_entry, 0, 1)
        self.ll_g_entry = QLineEdit()
        self.ll_g_entry.setStyleSheet(ui_styles.line_edit_style)
        self.ll.addWidget(self.ll_g_entry, 0, 2)
        self.ll_b_entry = QLineEdit()
        self.ll_b_entry.setStyleSheet(ui_styles.line_edit_style)
        self.ll.addWidget(self.ll_b_entry, 0, 3)
        # Open Color Selector
        self.ll_color_select = QPushButton("Color")
        self.ll_color_select.setStyleSheet(ui_styles.button_style)
        self.ll_color_select.clicked.connect(self.set_ll_color)
        self.ll.addWidget(self.ll_color_select, 0, 4)
        self.ll_widget = QWidget()
        self.ll_widget.setLayout(self.ll)
        self.right_frame.addWidget(self.ll_widget)

        # Create Gradient Button
        self.button_create_gradient = QPushButton("Create Gradient")
        self.button_create_gradient.setStyleSheet(ui_styles.button_style)
        self.button_create_gradient.clicked.connect(self.create_gradient)
        self.right_frame.addWidget(self.button_create_gradient)

        # Optimal Color Button
        self.button_optimal_color = QPushButton("Optimal Color")
        self.button_optimal_color.setStyleSheet(ui_styles.button_style)
        self.button_optimal_color.clicked.connect(self.optimal_color)
        self.right_frame.addWidget(self.button_optimal_color)

        self.right_frame.addStretch()

        # Setup the right frame widget
        self.right_frame_widget = QWidget()
        self.right_frame_widget.setLayout(self.right_frame)

        self.layout.addWidget(self.right_frame_widget, 0, 1)

    # SETTERS and GETTERS ------------------------------------------------------------

    # TOOL FUNCTONS ---------------------------------------------------------------

    def get_gradient_arguments(self):
        self.width = self.width_entry.text()
        self.width = int(self.width) if self.width else None
        self.height = self.height_entry.text()
        self.height = int(self.height) if self.height else None
        self.ul_r = self.ul_r_entry.text()
        self.ul_r = int(self.ul_r) if self.ul_r else None
        self.ul_g = self.ul_g_entry.text()
        self.ul_g = int(self.ul_g) if self.ul_g else None
        self.ul_b = self.ul_b_entry.text()
        self.ul_b = int(self.ul_b) if self.ul_b else None
        self.ul = np.array((self.ul_r, self.ul_g, self.ul_b))
        self.ur_r = self.ur_r_entry.text()
        self.ur_r = int(self.ur_r) if self.ur_r else None
        self.ur_g = self.ur_g_entry.text()
        self.ur_g = int(self.ur_g) if self.ur_g else None
        self.ur_b = self.ur_b_entry.text()
        self.ur_b = int(self.ur_b) if self.ur_b else None
        self.ur = np.array((self.ur_r, self.ur_g, self.ur_b))
        self.ll_r = self.ll_r_entry.text()
        self.ll_r = int(self.ll_r) if self.ll_r else None
        self.ll_g = self.ll_g_entry.text()
        self.ll_g = int(self.ll_g) if self.ll_g else None
        self.ll_b = self.ll_b_entry.text()
        self.ll_b = int(self.ll_b) if self.ll_b else None
        self.ll = np.array((self.ll_r, self.ll_g, self.ll_b))

    def make_gradient(self):
        image = np.empty((self.height, self.width, 3))
        for y in range(self.height):
            for x in range(self.width):
                image[y, x] = self.ul + (self.ur - self.ul) * (x / self.width) + (self.ll - self.ul) * (y / self.height)
        image = np.clip(image, 0, 255).astype(np.uint8)
        self.canvas_image = image
        self.update_canvas()

    def create_gradient(self):
        self.get_gradient_arguments()
        if self.width is None:
            self.event_manager.register(GradientFailed("missing_width"))
        elif self.height is None:
            self.event_manager.register(GradientFailed("missing_height"))
        elif None in self.ul:
            self.event_manager.register(GradientFailed("missing_ul"))
        elif None in self.ur:
            self.event_manager.register(GradientFailed("missing_ur"))
        elif None in self.ll:
            self.event_manager.register(GradientFailed("missing_ll"))
        else:
            self.make_gradient()

    def set_ul_color(self):
        self.selected_color = ColorSelectionWidget().showColorDialog()
        if self.selected_color is not None:
            self.ul_r = self.selected_color.red()
            self.ul_g = self.selected_color.green()
            self.ul_b = self.selected_color.blue()
            self.ul = np.array((self.ul_r, self.ul_g, self.ul_b))
        self.ul_r_entry.setText(str(self.ul_r))
        self.ul_g_entry.setText(str(self.ul_g))
        self.ul_b_entry.setText(str(self.ul_b))

    def set_ur_color(self):
        self.selected_color = ColorSelectionWidget().showColorDialog()
        if self.selected_color is not None:
            self.ur_r = self.selected_color.red()
            self.ur_g = self.selected_color.green()
            self.ur_b = self.selected_color.blue()
            self.ur = np.array((self.ur_r, self.ur_g, self.ur_b))
        self.ur_r_entry.setText(str(self.ur_r))
        self.ur_g_entry.setText(str(self.ur_g))
        self.ur_b_entry.setText(str(self.ur_b))

    def set_ll_color(self):
        self.selected_color = ColorSelectionWidget().showColorDialog()
        if self.selected_color is not None:
            self.ll_r = self.selected_color.red()
            self.ll_g = self.selected_color.green()
            self.ll_b = self.selected_color.blue()
            self.ll = np.array((self.ll_r, self.ll_g, self.ll_b))
        self.ll_r_entry.setText(str(self.ll_r))
        self.ll_g_entry.setText(str(self.ll_g))
        self.ll_b_entry.setText(str(self.ll_b))

    def load_library_classification(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self.tool_widget,
            "Select Library Classification",
            self.working_directory,
            "Pickle files (*.pkl)",
        )
        if filepath:
            self.lib_classification_path = filepath

    def optimal_color(self):
        def d_to_3d(i, dim):
            c = i // (dim[0] * dim[1])
            j = i - (dim[0] * dim[1]) * c
            a = j // dim[1]
            b = i - c * (dim[0] * dim[1]) - a * dim[1]
            return c, a, b

        lib_class = cli.pickle_loader(self.lib_classification_path)
        density_map = lib_class["density_map"]
        s = np.argsort(density_map.flatten())[::-1]
        channel = [self.set_ur_color, self.set_ul_color, self.set_ll_color]
        for i in range(3):
            r, g, b = d_to_3d(s[i], density_map.shape)
            # self.selected_color = QColor(r, g, b)
            print(r * 64, g * 64, b * 64)

    # SAVE AND LOAD -------------------------------------------------------------------

    def save_state(self):
        # This dict recreates the object; numpy points to numpy arrays that need to be loaded and assigned to object attributes
        data = {
            "data": {
                "type": self.type,
                "name": self.name,
                "height": self.height,
                "width": self.width,
                "ul_r": self.ul_r,
                "ul_g": self.ul_g,
                "ul_b": self.ul_b,
                "ur_r": self.ur_r,
                "ur_g": self.ur_g,
                "ur_b": self.ur_b,
                "ll_r": self.ll_r,
                "ll_g": self.ll_g,
                "ll_b": self.ll_b,
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
        self.ul_r_entry.setText(str(self.ul_r))
        self.ul_g_entry.setText(str(self.ul_g))
        self.ul_b_entry.setText(str(self.ul_b))
        self.ur_r_entry.setText(str(self.ur_r))
        self.ur_g_entry.setText(str(self.ur_g))
        self.ur_b_entry.setText(str(self.ur_b))
        self.ll_r_entry.setText(str(self.ll_r))
        self.ll_g_entry.setText(str(self.ll_g))
        self.ll_b_entry.setText(str(self.ll_b))
        self.ul = np.array((self.ul_r, self.ul_g, self.ul_b))
        self.ur = np.array((self.ur_r, self.ur_g, self.ur_b))
        self.ll = np.array((self.ll_r, self.ll_g, self.ll_b))


class ColorSelectionWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.color = None

        self.btn = QPushButton("Choose Color", self)
        self.btn.clicked.connect(self.showColorDialog)

        self.label = QLabel("Selected Color", self)

        layout = QVBoxLayout()
        layout.addWidget(self.btn)
        layout.addWidget(self.label)

        self.setLayout(layout)
        self.setWindowTitle("Color Selection Widget")
        self.setGeometry(300, 300, 300, 200)

    def showColorDialog(self):
        color = QColorDialog.getColor()

        if color.isValid():
            return color
        else:
            return None


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


class GradientFailed(Event):
    def __init__(self, report):
        super(GradientFailed, self).__init__()
        self.module = module_name
        self.title = f"mosaic_failed_{report}"
        self.listeners = None

    def emit(self):
        self.modules["UserInterface"].update_log_stream()
