from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QFileDialog,
    QGridLayout,
    QComboBox,
    QCheckBox,
)
from layer_class import Layer
from event_manager import Event
import ui.ui_styles as ui_styles
import mosaic_util.mosaic as mosaic
import mosaic_util.classify_image_library as cli
from PIL import Image


module_name = "MosaicTool"


def register(plugin_manager):
    plugin_manager.register_plugin("MosaicTool", "Tool for creating Mosaics", MosaicTool)


class MosaicTool(Layer):
    def __init__(self, name, event_manager):
        super(MosaicTool, self).__init__()
        self.type = "MosaicTool"
        self.name = name
        self.event_manager = event_manager

        # Mosaic Arguments
        self.lib_classification_path = None
        self.block_resolution = None
        self.color_delta_filter = None
        self.num_blocks_width = None
        self.target_color_delta = None
        self.shape_match_filter = None
        self.image_repeat_filter = None
        self.density_match_checkbox_state = False
        self.base_image = None
        self.packing_style = None

        self.create_canvas()
        self.create_right_frame()

        self.layout.setColumnStretch(0, 1)
        self.layout.setColumnStretch(1, 0)

        self.mosaic_np = None
        self.mosaic_obj = None

        self.active_tools = None
        self.available_base_images = []  # These are compatible plugins

    def configure(self):
        self.event_manager.register(GetConfigData(self.name))
        self.update_active_tools()

    def update_active_tools(self):
        self.event_manager.register(UpdateActiveTools(self.name))

    def update(self):
        self.update_active_tools()

    def create_right_frame(self):
        self.right_frame = QVBoxLayout()

        # Load Library Classification Button
        self.button_load_lib_class = QPushButton("Load Library Classification")
        self.button_load_lib_class.setStyleSheet(ui_styles.button_style)
        self.button_load_lib_class.clicked.connect(self.load_library_classification)
        self.right_frame.addWidget(self.button_load_lib_class)

        # Select base image
        self.base_image_select = QGridLayout()
        self.layout.setColumnStretch(0, 1)
        self.combo_label = QLabel("Select Base Image")
        self.combo_label.setStyleSheet("font: bold 14px Century Gothic; color: white;")
        self.base_image_select.addWidget(self.combo_label, 0, 0)

        # Create and style the dropdown
        self.plugin_dropdown = QComboBox()
        self.plugin_dropdown.setStyleSheet(ui_styles.combobox_style)
        self.plugin_dropdown.addItem("None")
        self.base_image_select.addWidget(self.plugin_dropdown, 1, 0)

        # Load Button
        self.load_base_image_button = QPushButton("Load")
        self.load_base_image_button.setStyleSheet(ui_styles.button_style)
        self.load_base_image_button.clicked.connect(self.load_base_image)
        self.base_image_select.addWidget(self.load_base_image_button, 1, 1)

        self.base_image_select_widget = QWidget()
        self.base_image_select_widget.setLayout(self.base_image_select)
        self.right_frame.addWidget(self.base_image_select_widget)

        # Block Resolution
        self.block_res_label = QLabel("Block Resolution")
        self.block_res_label.setStyleSheet(ui_styles.label_style)
        self.right_frame.addWidget(self.block_res_label)
        self.block_res_entry = QLineEdit()
        self.block_res_entry.setStyleSheet(ui_styles.line_edit_style)
        self.right_frame.addWidget(self.block_res_entry)

        # Num Blocks Width
        self.num_blocks_width_label = QLabel("Num Blocks Width")
        self.num_blocks_width_label.setStyleSheet(ui_styles.label_style)
        self.right_frame.addWidget(self.num_blocks_width_label)
        self.num_blocks_width_entry = QLineEdit()
        self.num_blocks_width_entry.setStyleSheet(ui_styles.line_edit_style)
        self.right_frame.addWidget(self.num_blocks_width_entry)

        # Color Delta Filter
        self.color_delta_filter_label = QLabel("Color Delta Filter")
        self.color_delta_filter_label.setStyleSheet(ui_styles.label_style)
        self.right_frame.addWidget(self.color_delta_filter_label)
        self.color_delta_filter_entry = QLineEdit()
        self.color_delta_filter_entry.setStyleSheet(ui_styles.line_edit_style)
        self.right_frame.addWidget(self.color_delta_filter_entry)

        # Target Color Delta
        self.target_color_delta_label = QLabel("Target Color Delta (Tilt)")
        self.target_color_delta_label.setStyleSheet(ui_styles.label_style)
        self.right_frame.addWidget(self.target_color_delta_label)
        self.target_color_delta_entry = QLineEdit()
        self.target_color_delta_entry.setStyleSheet(ui_styles.line_edit_style)
        self.right_frame.addWidget(self.target_color_delta_entry)

        # Shape Match Filter
        self.shape_match_filter_label = QLabel("Shape Match Filter")
        self.shape_match_filter_label.setStyleSheet(ui_styles.label_style)
        self.right_frame.addWidget(self.shape_match_filter_label)
        self.shape_match_filter_entry = QLineEdit()
        self.shape_match_filter_entry.setStyleSheet(ui_styles.line_edit_style)
        self.right_frame.addWidget(self.shape_match_filter_entry)

        # Image Repeat Filter
        self.image_repeat_filter_label = QLabel("Image Repeat Filter")
        self.image_repeat_filter_label.setStyleSheet(ui_styles.label_style)
        self.right_frame.addWidget(self.image_repeat_filter_label)
        self.image_repeat_filter_entry = QLineEdit()
        self.image_repeat_filter_entry.setStyleSheet(ui_styles.line_edit_style)
        self.right_frame.addWidget(self.image_repeat_filter_entry)

        # Add a density tilt checkbox
        self.density_match_layout = QGridLayout()
        self.density_match_layout.setColumnStretch(0, 1)
        self.density_match_checkbox = QCheckBox()
        self.density_match_checkbox.setStyleSheet(ui_styles.checkbox_style)
        self.density_match_checkbox.setChecked(self.density_match_checkbox_state)
        self.density_match_layout.addWidget(self.density_match_checkbox, 0, 0)
        self.density_match_label = QLabel("Density Match On (if checked)")
        self.density_match_label.setStyleSheet(ui_styles.label_style)
        self.density_match_layout.addWidget(self.density_match_label, 0, 1)
        self.density_match_widget = QWidget()
        self.density_match_widget.setLayout(self.density_match_layout)
        self.right_frame.addWidget(self.density_match_widget)

        # Packing Style Dropdown
        self.pack_style_dropdown = QComboBox()
        self.pack_style_dropdown.setStyleSheet(ui_styles.combobox_style)
        self.pack_style_dropdown.addItem("Square")
        self.pack_style_dropdown.addItem("Hex")
        self.right_frame.addWidget(self.pack_style_dropdown)

        # Build Mosaic Button
        self.button_build_mosaic = QPushButton("Build Mosaic")
        self.button_build_mosaic.setStyleSheet(ui_styles.button_style)
        self.button_build_mosaic.clicked.connect(self.generate_mosaic)
        self.right_frame.addWidget(self.button_build_mosaic)

        # Rescale Mosaic Button
        self.button_rescale_mosaic = QPushButton("Rescale Mosaic")
        self.button_rescale_mosaic.setStyleSheet(ui_styles.button_style)
        self.button_rescale_mosaic.clicked.connect(self.rescale_mosaic)
        self.right_frame.addWidget(self.button_rescale_mosaic)

        self.right_frame.addStretch()

        # Setup the right frame widget
        self.right_frame_widget = QWidget()
        self.right_frame_widget.setLayout(self.right_frame)

        self.layout.addWidget(self.right_frame_widget, 0, 1)

    def update_available_base_images(self):
        self.plugin_dropdown.clear()
        for tool in self.active_tools:
            if isinstance(self.active_tools[tool], Layer) and tool != self.name:
                self.available_base_images.append(tool)
                self.plugin_dropdown.addItem(tool)

    # SETTERS and GETTERS ------------------------------------------------------------
    def set_active_tools(self, tools):
        self.active_tools = tools

    def set_lib_classification(self, path):
        print("setting the lib class")
        self.lib_classification_path = path

    # TOOL FUNCTONS ---------------------------------------------------------------

    def load_base_image(self):
        text = self.plugin_dropdown.currentText()
        if text:
            self.canvas_image = self.active_tools[text].get_canvas_image()
            if self.canvas_image is not None:
                self.canvas_image = self.canvas_image.copy()
                self.base_image = self.canvas_image.copy()
                self.update_canvas()

    def load_library_classification(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self.tool_widget,
            "Select Library Classification",
            self.working_directory,
            "Pickle files (*.pkl)",
        )
        if filepath:
            self.lib_classification_path = filepath

    def get_mosaic_arguments(self):
        self.block_resolution = self.block_res_entry.text()
        self.block_resolution = int(self.block_resolution) if self.block_resolution else None
        self.num_blocks_width = self.num_blocks_width_entry.text()
        self.num_blocks_width = int(self.num_blocks_width) if self.num_blocks_width else None
        self.target_color_delta = self.target_color_delta_entry.text()
        self.target_color_delta = int(self.target_color_delta) if self.target_color_delta else None
        self.color_delta_filter = self.color_delta_filter_entry.text()
        self.color_delta_filter = int(self.color_delta_filter) if self.color_delta_filter else None
        self.shape_match_filter = self.shape_match_filter_entry.text()
        self.shape_match_filter = int(self.shape_match_filter) / 100 if self.shape_match_filter else None
        self.image_repeat_filter = self.image_repeat_filter_entry.text()
        self.image_repeat_filter = int(self.image_repeat_filter) if self.image_repeat_filter else 0
        self.density_match_checkbox_state = self.density_match_checkbox.isChecked()
        self.packing_style = self.pack_style_dropdown.currentText()

    def generate_mosaic(self):
        self.event_manager.register(MosaicInitiated())
        self.get_mosaic_arguments()
        print("libpath ", self.lib_classification_path)
        print(type(self.lib_classification_path))
        print(self.lib_classification_path is None)
        if self.lib_classification_path is None:
            print("enter")
            self.event_manager.register(MosaicFailed("missing_lib_classification"))
        elif self.base_image is None:
            self.event_manager.register(MosaicFailed("missing_base_image"))
        elif self.num_blocks_width is None:
            self.event_manager.register(MosaicFailed("missing_num_blocks_width"))
        elif self.color_delta_filter is None:
            self.event_manager.register(MosaicFailed("missing_color_delta_filter"))
        elif self.target_color_delta is None:
            self.event_manager.register(MosaicFailed("missing_target_color_delta"))
        elif self.block_resolution is None:
            self.event_manager.register(MosaicFailed("missing_block_resolution"))
        elif self.shape_match_filter is None:
            self.event_manager.register(MosaicFailed("missing_shape_match_filter"))
        else:
            lib_class = cli.pickle_loader(self.lib_classification_path)
            color_dict = lib_class["color_dict"]
            block_dict = lib_class["block_dict"]
            shape_dict = lib_class["shape_dict"]
            density_map = lib_class["density_map"]
            print(self.density_match_checkbox_state)
            self.mosaic_np, self.mosaic_obj = mosaic.main(
                self.base_image,
                self.num_blocks_width,
                color_dict,
                block_dict,
                shape_dict,
                density_map,
                self.color_delta_filter,
                self.target_color_delta,
                self.block_resolution,
                self.shape_match_filter,
                self.density_match_checkbox_state,
                self.image_repeat_filter,
                self.packing_style,
            )  # mosaic_np is a numpy array, mosaic_obj is a Mosaic object
            self.canvas_image = self.mosaic_np
            self.update_canvas()
            self.event_manager.register(MosaicComplete())

    def rescale_mosaic(self):
        self.block_resolution = self.block_res_entry.text()
        self.block_resolution = int(self.block_resolution) if self.block_resolution else None
        if not self.lib_classification_path:
            self.event_manager.register(RescaleFailed("missing_lib_classification"))
        elif not self.mosaic_obj:
            self.event_manager.register(RescaleFailed("missing_mosaic_obj"))
        elif not self.block_resolution:
            self.event_manager.register(RescaleFailed("missing_block_resolution"))
        else:
            lib_class = cli.pickle_loader(self.lib_classification_path)
            block_dict = lib_class["block_dict"]
            self.mosaic_np = mosaic.rescale_mosaic(self.mosaic_obj, block_dict, self.block_resolution)
            self.canvas_image = self.mosaic_np
            self.update_canvas()

    # SAVE AND LOAD -------------------------------------------------------------------

    def save_state(self):
        # This dict recreates the object; numpy points to numpy arrays that need to be loaded and assigned to object attributes
        data = {
            "data": {
                "type": self.type,
                "name": self.name,
                "lib_classification_path": self.lib_classification_path,
                "block_resolution": self.block_resolution,
                "color_delta_filter": self.color_delta_filter,
                "num_blocks_width": self.num_blocks_width,
                "target_color_delta": self.target_color_delta,
                "shape_match_filter": self.shape_match_filter,
                "image_repeat_filter": self.image_repeat_filter,
            },
            "big_data": {"canvas_image": None, "mosaic_np": None, "mosaic_obj": None, "base_image": None},
        }
        # This dict will assign file save names to the numpy arrays that we need to save
        big_data_files = {}
        if self.canvas_image is not None:
            data["big_data"]["canvas_image"] = f"{self.name}_canvas_image.npy"
            big_data_files[f"{self.name}_canvas_image.npy"] = self.canvas_image
        if self.mosaic_np is not None:
            data["big_data"]["mosaic_np"] = f"{self.name}_mosaic_np.npy"
            big_data_files[f"{self.name}_mosaic_np.npy"] = self.mosaic_np
        if self.base_image is not None:
            data["big_data"]["base_image"] = f"{self.name}_base_image.npy"
            big_data_files[f"{self.name}_base_image.npy"] = self.base_image
        if self.mosaic_obj is not None:
            data["big_data"]["mosaic_obj"] = f"{self.name}_mosaic_obj.pkl"
            big_data_files[f"{self.name}_mosaic_obj.pkl"] = self.mosaic_obj
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
        self.block_res_entry.setText(str(self.block_resolution))
        self.num_blocks_width_entry.setText(str(self.num_blocks_width))
        self.color_delta_filter_entry.setText(str(self.color_delta_filter))
        self.target_color_delta_entry.setText(str(self.target_color_delta))
        self.shape_match_filter_entry.setText(str(int(self.shape_match_filter)))
        self.image_repeat_filter_entry.setText(str(self.image_repeat_filter))


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


class UpdateActiveTools(Event):
    def __init__(self, name):
        super(UpdateActiveTools, self).__init__()
        self.module = module_name
        self.name = name
        self.title = "update_active_tools"
        self.listeners = None

    def emit(self):
        tools = self.modules["WorkspaceManager"].get_active_tools()
        self.modules[self.name].set_active_tools(tools)
        self.modules[self.name].update_available_base_images()
        self.modules["UserInterface"].update_log_stream()


class MosaicInitiated(Event):
    def __init__(self):
        super(MosaicInitiated, self).__init__()
        self.module = module_name
        self.title = "mosaic_initiated"
        self.listeners = None

    def emit(self):
        self.modules["UserInterface"].update_log_stream()


class MosaicFailed(Event):
    def __init__(self, report):
        super(MosaicFailed, self).__init__()
        self.module = module_name
        self.title = f"mosaic_failed_{report}"
        self.listeners = None

    def emit(self):
        self.modules["UserInterface"].update_log_stream()


class MosaicComplete(Event):
    def __init__(self):
        super(MosaicComplete, self).__init__()
        self.module = module_name
        self.title = "mosaic_complete"
        self.listeners = None

    def emit(self):
        self.modules["UserInterface"].update_log_stream()


class RescaleFailed(Event):
    def __init__(self, report):
        super(RescaleFailed, self).__init__()
        self.module = module_name
        self.title = f"rescale_failed_{report}"
        self.listeners = None

    def emit(self):
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
