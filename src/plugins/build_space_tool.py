import numpy as np
from event_manager import Event
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QGridLayout,
    QListWidget,
    QComboBox,
    QListWidgetItem,
    QCheckBox,
)
from layer_class import Layer
import ui.ui_styles as ui_styles
import cv2

module_name = "BuildSpaceTool"


def register(plugin_manager):
    plugin_manager.register_plugin("BuildSpaceTool", "Tool for combining layers", BuildSpaceTool)


class BuildSpaceTool(Layer):
    def __init__(self, name, event_manager):
        super(BuildSpaceTool, self).__init__()
        self.type = "BuildSpaceTool"
        self.name = name
        self.event_manager = event_manager
        self.layers_log = {}  # Dictionary of active Layers in this tool

        self.create_canvas()
        self.create_right_frame()

        self.layout.setColumnStretch(0, 1)
        self.layout.setColumnStretch(1, 0)

        self.active_tools = None
        self.available_base_images = []  # These are compatible plugins

        self.new_canvas_retreive = None  # Temp storage for fetched canvases

    def configure(self):
        self.event_manager.register(GetConfigData(self.name))
        self.update_active_tools()

    def update_active_tools(self):
        self.event_manager.register(UpdateActiveTools(self.name))

    def update(self):
        self.update_active_tools()

    def create_right_frame(self):
        self.right_frame = QVBoxLayout()

        # Select base image
        self.base_image_select = QGridLayout()
        self.base_image_select.setColumnStretch(0, 1)

        self.combo_label = QLabel("Add Layer")
        self.combo_label.setStyleSheet("font: bold 14px Century Gothic; color: white;")
        self.base_image_select.addWidget(self.combo_label, 0, 0)

        # Create and style the dropdown
        self.plugin_dropdown = QComboBox()
        self.plugin_dropdown.setStyleSheet(ui_styles.combobox_style)
        self.plugin_dropdown.addItem("None")
        self.base_image_select.addWidget(self.plugin_dropdown, 1, 0)

        # Add Layer Button
        self.addLayerButton = QPushButton("Add")
        self.addLayerButton.setStyleSheet(ui_styles.button_style)
        self.addLayerButton.clicked.connect(self.add_layer)
        self.base_image_select.addWidget(self.addLayerButton, 1, 1)

        self.base_image_select_widget = QWidget()
        self.base_image_select_widget.setLayout(self.base_image_select)
        self.right_frame.addWidget(self.base_image_select_widget)

        # List Widget for layers
        self.layer_list = CustomListWidget()
        self.layer_list.setStyleSheet(ui_styles.list_style)
        self.right_frame.addWidget(self.layer_list)

        # Up Down buttons
        self.up_down_buttons = QGridLayout()

        # Up Button
        self.upButton = QPushButton("Move Up")
        self.upButton.setStyleSheet(ui_styles.button_style)
        self.upButton.clicked.connect(self.move_up)
        self.up_down_buttons.addWidget(self.upButton, 0, 0)

        # Down Button
        self.downButton = QPushButton("Move Down")
        self.downButton.setStyleSheet(ui_styles.button_style)
        self.downButton.clicked.connect(self.move_down)
        self.up_down_buttons.addWidget(self.downButton, 0, 1)

        # Remove Button
        self.removeButton = QPushButton("Remove")
        self.removeButton.setStyleSheet(ui_styles.button_style)
        self.removeButton.clicked.connect(self.remove_layer)
        self.up_down_buttons.addWidget(self.removeButton, 0, 2)

        self.up_down_buttons_widget = QWidget()
        self.up_down_buttons_widget.setLayout(self.up_down_buttons)
        self.right_frame.addWidget(self.up_down_buttons_widget)

        # Print Button
        self.print_button = QPushButton("Print")
        self.print_button.setStyleSheet(ui_styles.button_style)
        self.print_button.clicked.connect(self.print_info)
        self.right_frame.addWidget(self.print_button)

        # Combine Button
        self.combine_button = QPushButton("Combine")
        self.combine_button.setStyleSheet(ui_styles.button_style)
        self.combine_button.clicked.connect(self.combine_layers)
        self.right_frame.addWidget(self.combine_button)

        self.right_frame.addStretch()

        # Setup the right frame widget
        self.right_frame_widget = QWidget()
        self.right_frame_widget.setLayout(self.right_frame)

        self.layout.addWidget(self.right_frame_widget, 0, 1)

    def print_info(self):
        self.layer_list.setItemWidget(self.layer_list.item(0), self.layer_list.item(0).widget)
        print(self.layer_list.item(0))
        print(self.layer_list.item(0).widget)
        print(self.layer_list.itemWidget(self.layer_list.item(0)))
        print(self.layer_list.item(1))
        print(self.layer_list.item(1).widget)
        print(self.layer_list.itemWidget(self.layer_list.item(1)))
        print("-")

    # SETTERS and GETTERS ------------------------------------------------------------

    def set_active_tools(self, tools):
        self.active_tools = tools

    def set_new_canvas_retreive(self, img):
        self.new_canvas_retreive = img

    # TOOL FUNCTONS ---------------------------------------------------------------
    def update_available_base_images(self):
        self.plugin_dropdown.clear()
        for tool in self.active_tools:
            if isinstance(self.active_tools[tool], Layer) and tool != self.name:
                self.available_base_images.append(tool)
                self.plugin_dropdown.addItem(tool)

    def add_layer(self):
        # Add a new layer to the bottom of the list
        text = self.plugin_dropdown.currentText()
        if text:
            self.layer_list.new_add(text)
            self.layers_log = self.layer_list.gen_layers_log()

    def remove_layer(self):
        # Remove a layer from the layer list
        current_row = self.layer_list.currentRow()
        self.layer_list.takeItem(current_row)
        self.layers_log = self.layer_list.gen_layers_log()

    def move_up(self):
        self.layer_list.move_up()
        self.layers_log = self.layer_list.gen_layers_log()

    def move_down(self):
        self.layer_list.move_down()
        self.layers_log = self.layer_list.gen_layers_log()

    def load_base_image(self):
        text = self.plugin_dropdown.currentText()
        if text:
            self.canvas_image = self.active_tools[text].get_canvas_image()
            if self.canvas_image is not None:
                self.canvas_image = self.canvas_image.copy()
                self.base_image = self.canvas_image.copy()
                self.update_canvas()

    def combine_layers(self):
        self.layers_log = self.layer_list.gen_layers_log()
        print("log: ", self.layers_log)
        combo = None
        for i in range(len(self.layers_log)):
            item = self.layers_log[i]
            if item["checkbox_state"] == True:
                self.event_manager.register(GetLayerCanvas(self.name, item["text"]))
                combo = self.new_canvas_retreive
                break
        if combo is not None:
            for j in range(i + 1, len(self.layers_log)):
                print("combine")
                item = self.layers_log[j]
                if item["checkbox_state"] == True:
                    self.event_manager.register(GetLayerCanvas(self.name, item["text"]))
                    m = item["dropdown_selection"]
                    t = item["value_box_text"]
                    if t == "":
                        self.event_manager.register(CombineError("no_values"))
                        break
                    else:
                        t = int(t) / 100
                    c = self.new_canvas_retreive
                    combo_aspect = combo.shape[0] / combo.shape[1]  # h/w
                    c_aspect = c.shape[0] / c.shape[1]
                    if c_aspect > combo_aspect:
                        c = c[: int(c.shape[0] * (combo_aspect / c_aspect)), ...]
                    else:
                        c = c[:, : int(c.shape[1] * (c_aspect / combo_aspect)), ...]
                    h = max(c.shape[0], combo.shape[0])
                    w = max(c.shape[1], combo.shape[1])
                    c = cv2.resize(c, (w, h), interpolation=cv2.INTER_NEAREST)
                    combo = cv2.resize(combo, (w, h), interpolation=cv2.INTER_NEAREST)
                    print("combo_aspect ", combo.shape[0] / combo.shape[1])
                    print("c_aspect", c.shape[0] / c.shape[1])
                    # else:
                    #     self.event_manager.register(AspectMismatch(self.name))
                    #     combo = None
                    #     break
                    if m == "None":
                        combo = np.clip(combo * (1 - t) + c * t, 0, 255).astype(np.uint8)
                    elif m == "Black":
                        full_combine = np.clip(combo * (1 - t) + c * t, 0, 255).astype(np.uint8)
                        combo = np.where(c == np.array([[[0, 0, 0]]]), combo, full_combine)
                    elif m == "White":
                        full_combine = np.clip(combo * (1 - t) + c * t, 0, 255).astype(np.uint8)
                        combo = np.where(c == np.array([[[255, 255, 255]]]), combo, full_combine)
                    else:
                        raise ValueError
            self.canvas_image = combo
            self.update_canvas()
            self.event_manager.register(CombineLayersComplete())
        else:
            self.event_manager.register(CombineError("no_layers"))

        # SAVE AND LOAD -------------------------------------------------------------------

    def save_state(self):
        # This dict recreates the object; numpy points to numpy arrays that need to be loaded and assigned to object attributes
        data = {
            "data": {"type": self.type, "name": self.name, "layers_log": self.layers_log},
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
        self.layers_log = {int(key): value for key, value in self.layers_log.items()}
        print(self.layers_log)
        for attribute, data_name in data["big_data"].items():
            if hasattr(self, attribute):
                print(attribute)
                self.event_manager.register(LoadDataFromSave(self.name, attribute, data_name))
        self.update_canvas()
        self.layer_list.build_from_layers_log(self.layers_log)

    def load_attribute(self, attribute, data):
        setattr(self, attribute, data)


class CustomListWidget(QListWidget):
    def __init__(self):
        super(CustomListWidget, self).__init__()
        self.setStyleSheet(ui_styles.list_style)

    def new_add(self, text, value_box_text="", dropdown_selection="None", checkbox_state=True):
        # Create a CustomListItem
        custom_item = CustomListItem(text, value_box_text, dropdown_selection, checkbox_state)

        # Add it to the list widget
        self.addItem(custom_item)

        # Set the custom widget
        self.setItemWidget(custom_item, custom_item.widget)

    def move_up(self):
        current_row = self.currentRow()
        if current_row >= 1:
            current_item = self.takeItem(current_row)
            current_item.store_values()
            current_item.create_widget()
            self.insertItem(current_row - 1, current_item)
            self.setItemWidget(current_item, current_item.widget)
            self.setCurrentItem(current_item)

    def move_down(self):
        current_row = self.currentRow()
        if current_row < self.count() - 1:
            current_item = self.takeItem(current_row)
            current_item.store_values()
            current_item.create_widget()
            self.insertItem(current_row + 1, current_item)
            self.setItemWidget(current_item, current_item.widget)
            self.setCurrentItem(current_item)

    def gen_layers_log(self):
        log = {}
        for i in range(self.count()):
            item = self.item(i)
            item.store_values()
            log[i] = {
                "text": item.text,
                "value_box_text": item.value_box_text,
                "dropdown_selection": item.dropdown_selection,
                "checkbox_state": item.checkbox_state,
            }
        return log

    def build_from_layers_log(self, log):
        for i in log:
            j = log[i]
            self.new_add(j["text"], j["value_box_text"], j["dropdown_selection"], j["checkbox_state"])


class CustomListItem(QListWidgetItem):
    def __init__(self, text, value_box_text="", dropdown_selection="None", checkbox_state=True):
        # Create a QWidget to hold the layout
        super(CustomListItem, self).__init__()
        self.text = text
        self.value_box_text = value_box_text
        self.dropdown_selection = dropdown_selection
        self.checkbox_state = checkbox_state
        self.create_widget()

    def create_widget(self):
        self.widget = QWidget()

        self.layout = QGridLayout(self.widget)
        self.layout.setColumnStretch(1, 1)

        # Add a checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.checkbox_state)
        self.layout.addWidget(self.checkbox, 0, 0)

        self.label = QLabel(self.text)
        self.label.setStyleSheet(ui_styles.label_style)
        self.layout.addWidget(self.label, 0, 1)

        self.value_box = QLineEdit()
        self.value_box.setStyleSheet(ui_styles.line_edit_style)
        self.value_box.setFixedWidth(40)
        self.value_box.setText(self.value_box_text)
        self.layout.addWidget(self.value_box, 0, 2)

        self.dropdown = QComboBox()
        self.dropdown.setStyleSheet(ui_styles.combobox_style)
        self.dropdown.addItem("None")
        self.dropdown.addItem("Black")
        self.dropdown.addItem("White")
        self.dropdown.setCurrentText(self.dropdown_selection)
        self.layout.addWidget(self.dropdown, 0, 3)

        self.widget.setLayout(self.layout)

        # Set the size hint for the list item
        self.setSizeHint(self.widget.sizeHint())

    def store_values(self):
        self.value_box_text = self.value_box.text()
        self.dropdown_selection = self.dropdown.currentText()
        self.checkbox_state = self.checkbox.isChecked()


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


class CombineError(Event):
    def __init__(self, report):
        super(CombineError, self).__init__()
        self.module = module_name
        self.title = f"combine_failed_{report}"
        self.listeners = None

    def emit(self):
        self.modules["UserInterface"].update_log_stream()


class CombineLayersComplete(Event):
    def __init__(self):
        super(CombineLayersComplete, self).__init__()
        self.module = module_name
        self.title = f"combine_layers_complete"
        self.listeners = None

    def emit(self):
        self.modules["UserInterface"].update_log_stream()


class GetLayerCanvas(Event):
    def __init__(self, name, layer_name):
        super(GetLayerCanvas, self).__init__()
        self.module = module_name
        self.name = name
        self.layer_name = layer_name
        self.title = "get_layer_canvas"
        self.listeners = None

    def emit(self):
        img = self.modules[self.layer_name].get_canvas_image().copy()
        self.modules[self.name].set_new_canvas_retreive(img)
        self.modules["UserInterface"].update_log_stream()


class AspectMismatch(Event):
    def __init__(self, name):
        super(AspectMismatch, self).__init__()
        self.module = module_name
        self.name = name
        self.title = "aspect_mismatch_during_combine"
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
