import os
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QGridLayout,
    QTabWidget,
    QStackedWidget,
    QComboBox,
    QDialog,
    QMenu,
)
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt, QSize
from event_manager import Event
import ui.ui_styles as ui_styles

module_name = "WorkspaceManager"

script_dir = os.path.dirname(os.path.abspath(__file__))


class WorkspaceManager:
    def __init__(self, event_manager):
        self.type = "WorkspaceManager"
        self.event_manager = event_manager
        self.plugins = {}
        self.active_tools = {}  # Dictionary of active tools {name: instance}
        self.tab_map = {}  # For mapping tabs to active tools {index, name}

        # Initialize layout
        self.layout = QGridLayout()

        self.create_tool_space()
        self.create_tab_frame()
        self.create_default_frame()
        self.options_window = OptionsWindow()  # Adding this for later configuration

        self.layout.setRowStretch(0, 0)
        self.layout.setRowStretch(1, 0)
        self.layout.setRowStretch(2, 1)

    def init_plugins(self, plugins):
        # Tools will be passed over by the plugin manager at app launch
        self.plugins = plugins
        self.options_window.configure_plugin_selector(self.plugins)

    def create_default_frame(self):
        self.default_frame = QHBoxLayout()

        self.default_frame.addStretch()

        icon_size = QSize(24, 24)
        button_dim = 60

        # Add a label for the dropdown
        self.add_plugin_button = QPushButton()
        self.add_plugin_button.setToolTip("Add Tool")
        self.add_plugin_button.setIcon(QIcon(os.path.join(script_dir, "ui", "add_plugin.svg")))
        self.add_plugin_button.setIconSize(icon_size)  # Set the size of the icon
        self.add_plugin_button.setFixedSize(button_dim, button_dim)  # Set width and height
        self.add_plugin_button.setStyleSheet(ui_styles.button_style)
        self.add_plugin_button.clicked.connect(self.select_plugin_dialog)
        self.default_frame.addWidget(self.add_plugin_button)

        # Setup the frame
        self.default_frame_widget = QWidget()
        self.default_frame_widget.setLayout(self.default_frame)
        self.layout.addWidget(self.default_frame_widget, 0, 0)

    def create_tab_frame(self):
        # Create the tab widget
        # self.tab_widget = QTabWidget()
        self.tab_widget = CustomTabWidget()
        # Connect the tab change signal to a method
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        self.tab_widget.delete_tab_action.triggered.connect(self.delete_current_tab)
        # Apply the custom style to the tab widget
        self.tab_widget.setStyleSheet(ui_styles.tab_style)
        # Add the tab widget to the layout
        self.layout.addWidget(self.tab_widget, 1, 0)

    def create_tool_space(self):
        # Initialize QStackedWidget for tools
        self.tools_stack = QStackedWidget()
        # Add the tools_stack to the layout
        self.layout.addWidget(self.tools_stack, 2, 0)

    # SETTERS AND GETTERS ----------------------------------------------------------

    def get_active_tools(self):
        return self.active_tools

    def set_working_directory(self, path):
        pass

    def select_plugin_dialog(self):
        plugin = self.options_window.select_plugin()  # string
        # print(plugin)
        if plugin is not None:
            self.event_manager.register(PluginSelected(plugin))

    def open_plugin_instance(self, plugin_name, plugin_instance):
        # Use the plugin manager to create an instance
        # add it to active plugins
        self.active_tools[plugin_name] = plugin_instance
        # Create a tab for it
        self.tab_widget.addTab(QWidget(), plugin_name)
        # Update the tab map
        self.tab_map[len(self.tab_map)] = plugin_name
        # Add it to the tool stack
        self.tools_stack.addWidget(plugin_instance.get_tool_widget())
        self.update_tools_emit()
        print(self.active_tools)
        print(self.tab_map)
        # for index in range(self.tools_stack.count()):
        #     widget = self.tools_stack.widget(index)
        #     print(f"Widget at index {index}: {widget}")
        #     print(f" - Type: {type(widget)}")
        #     print(f" - Object Name: {widget.objectName()}")

    def update_tools_emit(self):
        for tool in self.active_tools:
            self.active_tools[tool].update()

    def on_tab_changed(self, index):
        self.tools_stack.setCurrentIndex(index)

    def delete_current_tab(self):
        # Delete the tab
        index = self.tab_widget.delete_current_tab()
        name = self.tab_map[index]
        # Remove that tool from the tool stack
        self.tools_stack.removeWidget(self.active_tools[name].tool_widget)
        # Remove that tool from the active tools
        del self.active_tools[name]
        # Remove that tool from the tab map and reindex the map
        del self.tab_map[index]
        new_tab_map = {}
        for key in self.tab_map:
            if key > index:
                new_tab_map[key - 1] = self.tab_map[key]
            else:
                new_tab_map[key] = self.tab_map[key]
        self.tab_map = new_tab_map
        self.update_tools_emit()

    def get_active_tool(self):
        # Get the current index of the selected tab
        current_index = self.tab_widget.currentIndex()

        # Use the tab_map to get the tool's name associated with this tab
        tool_name = self.tab_map.get(current_index)

        if tool_name is not None:
            # Return the instance of the tool from active_tools dictionary
            return tool_name
        else:
            # If there's no tool associated with the current tab, return None
            return None

    def get_workspace_widget(self):
        # Create a new QWidget
        self.workspace_widget = QWidget()
        # Set the layout of WorkspaceManager to this widget
        self.workspace_widget.setLayout(self.layout)
        # Return the widget
        return self.workspace_widget

    def save_state(self):
        active_tools_temp = {}
        for i in self.active_tools:
            active_tools_temp[i] = None
        data = {
            "data": {
                "type": self.type,
                "active_tools": active_tools_temp,
                "tab_map": self.tab_map,
            },
            "numpy": {},
        }
        arrays = {}
        return data, arrays

    def load_state(self, data):
        """
        At this point in time, we don't need to recreate a workspace manager unless it starts doing something more important. We're going through the entire standard process of opening a new plugin, which takes care of everything the recreation was doing.
        """

        # print(data)
        # data["data"]["tab_map"] = {int(key): value for key, value in data["data"]["tab_map"].items()}
        # for key, value in data["data"].items():
        #     if hasattr(self, key):
        #         print("have")
        #         setattr(self, key, value)
        # print(self.active_tools)
        # print(self.type)
        # print(self.tab_map)
        pass


class OptionsWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Add Plugin")
        self.setStyleSheet(f"background-color: {ui_styles.app_color};")  # Dark Grey color
        self.initUI()
        self.setGeometry(500, 300, 400, 100)  # x: 100, y: 100, width: 400, height: 300s
        self.selected_plugin = None

    def initUI(self):
        # Set the window layout and style
        self.frame = QVBoxLayout()

        # Add a label for the dropdown
        self.label = QLabel("Select Plugin")
        self.label.setStyleSheet("font: bold 14px Century Gothic; color: white;")
        self.frame.addWidget(self.label)

        # Create and style the dropdown
        self.plugin_dropdown = QComboBox()
        self.plugin_dropdown.setStyleSheet(ui_styles.combobox_style)
        self.plugin_dropdown.addItem("No Plugins Available")
        self.frame.addWidget(self.plugin_dropdown)

        # Add a button to close the window
        self.btn = QPushButton("Select")
        self.btn.setStyleSheet(ui_styles.button_style)
        self.btn.clicked.connect(self.on_select_clicked)
        self.frame.addWidget(self.btn)
        self.setLayout(self.frame)

    def configure_plugin_selector(self, plugins):
        if plugins:
            self.plugin_dropdown.clear()
            for p in plugins:
                self.plugin_dropdown.addItem(p)

    def select_plugin(self):
        result = self.exec()  # Use exec_ to show the dialog as modal
        if result == 1:  # Select button was used
            return self.selected_plugin
        else:
            return None

    def on_select_clicked(self):
        # Get the currently selected item in the combobox
        self.selected_plugin = self.plugin_dropdown.currentText()
        self.accept()  # Use accept to close the dialog and return QDialog.Accepted


class CustomTabWidget(QTabWidget):
    def __init__(self):
        super().__init__()

        # Create a context menu for tabs
        self.tab_context_menu = QMenu(self)
        # self.tab_context_menu.setStyleSheet(ui_styles.button_style)
        self.delete_tab_action = QAction("Delete", self)
        self.tab_context_menu.addAction(self.delete_tab_action)

        # Connect the context menu event
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_tab_context_menu)

    def show_tab_context_menu(self, position):
        # Show the context menu at the right-clicked tab position
        tab_index = self.tabBar().tabAt(position)
        if tab_index >= 0:
            self.tab_context_menu.exec(self.tabBar().mapToGlobal(position))

    def delete_current_tab(self):
        current_index = self.currentIndex()
        if current_index >= 0:
            self.removeTab(current_index)
        return current_index


# EVENTS FROM THIS MODULE ----------------------------------------------------------------------------------


class PluginSelected(Event):
    def __init__(self, plugin):
        super(PluginSelected, self).__init__()
        self.module = module_name
        self.title = "plugin_selected"
        self.listeners = None
        self.plugin = plugin

    def emit(self):
        plugin_name, plugin_instance = self.modules["PluginManager"].create_plugin_instance(self.plugin)
        self.modules["WorkspaceManager"].open_plugin_instance(plugin_name, plugin_instance)
        self.modules["UserInterface"].update_log_stream()
