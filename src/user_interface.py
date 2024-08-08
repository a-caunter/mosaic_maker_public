import os
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFileDialog,
    QTextEdit,
    QGridLayout,
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize
from event_manager import Event
import ui.ui_styles as ui_styles
from PIL import Image

module_name = "MainUI"

script_dir = os.path.dirname(os.path.abspath(__file__))


class UserInterface(QMainWindow):
    def __init__(self, event_manager):
        super().__init__()
        self.event_manager = event_manager
        self.setWindowTitle("Mosaic Maker")
        self.setStyleSheet(f"background-color: {ui_styles.app_color};")  # Dark Grey color

        self.layout = QGridLayout()

        self.create_top_frame()
        self.create_left_frame()

        self.layout.setColumnStretch(0, 0)
        self.layout.setColumnStretch(1, 1)
        self.layout.setRowStretch(0, 0)
        self.layout.setRowStretch(1, 1)

        self.working_directory = r"C:\Users"

        widget = QWidget()
        widget.setLayout(self.layout)
        self.setCentralWidget(widget)

        # For fetching for a canvas save
        self.active_tool = None
        self.canvas_to_save = None

    def create_top_frame(self):
        self.top_frame = QHBoxLayout()

        icon_size = QSize(24, 24)
        button_dim = 60

        # Open Session Button
        self.button_load_session = QPushButton()
        self.button_load_session.setToolTip("Open Session")
        self.button_load_session.setIcon(QIcon(os.path.join(script_dir, "ui", "open.svg")))
        self.button_load_session.setIconSize(icon_size)  # Set the size of the icon
        self.button_load_session.setFixedSize(button_dim, button_dim)  # Set width and height
        self.button_load_session.setStyleSheet(ui_styles.button_style)
        self.button_load_session.clicked.connect(self.load_session)
        self.top_frame.addWidget(self.button_load_session)

        # Save Session Button
        self.button_save_session = QPushButton()
        self.button_save_session.setToolTip("Save Session")
        self.button_save_session.setIcon(QIcon(os.path.join(script_dir, "ui", "save.svg")))
        self.button_save_session.setIconSize(icon_size)  # Set the size of the icon
        self.button_save_session.setFixedSize(button_dim, button_dim)  # Set width and height
        self.button_save_session.setStyleSheet(ui_styles.button_style)
        self.button_save_session.clicked.connect(self.save_session)
        self.top_frame.addWidget(self.button_save_session)

        # Select Working Directory Button
        self.button_select_working_directory = QPushButton()
        self.button_select_working_directory.setToolTip("Select Working Directory")
        self.button_select_working_directory.setIcon(QIcon(os.path.join(script_dir, "ui", "wd.svg")))
        self.button_select_working_directory.setIconSize(icon_size)  # Set the size of the icon
        self.button_select_working_directory.setFixedSize(button_dim, button_dim)  # Set width and height
        self.button_select_working_directory.setStyleSheet(ui_styles.button_style)
        self.button_select_working_directory.clicked.connect(self.select_working_directory)
        self.top_frame.addWidget(self.button_select_working_directory)

        # Save Active Canvas
        self.button_save_active_canvas = QPushButton()
        self.button_save_active_canvas.setToolTip("Save Active Canvas")
        self.button_save_active_canvas.setIcon(QIcon(os.path.join(script_dir, "ui", "download.svg")))
        self.button_save_active_canvas.setIconSize(icon_size)  # Set the size of the icon
        self.button_save_active_canvas.setFixedSize(button_dim, button_dim)  # Set width and height
        self.button_save_active_canvas.setStyleSheet(ui_styles.button_style)
        self.button_save_active_canvas.clicked.connect(self.save_active_canvas)
        self.top_frame.addWidget(self.button_save_active_canvas)

        self.top_frame.addStretch()

        # Setup the top frame
        self.top_frame_widget = QWidget()
        self.top_frame_widget.setLayout(self.top_frame)
        self.layout.addWidget(self.top_frame_widget, 0, 0, 1, 1)

    def create_left_frame(self):
        self.left_frame = QVBoxLayout()

        line_edit_style = """
            QLineEdit {
                color: white;
                font: 12px Century Gothic;
                background-color: #455361;
                border-radius: 0px;
                padding: 5px;
            }
            """

        # Log Stream Window
        self.log_stream = QTextEdit()
        self.log_stream.setStyleSheet(line_edit_style)
        self.log_stream.setReadOnly(True)
        # Apply additional styles to QTextEdit if needed
        self.left_frame.addWidget(self.log_stream)

        # Setup the left frame widget
        self.left_frame_widget = QWidget()
        self.left_frame_widget.setLayout(self.left_frame)

        self.layout.addWidget(self.left_frame_widget, 1, 0)

    def create_workspace(self, widget):
        # Get the widget from WorkspaceManager
        self.workspace_widget = widget
        self.layout.addWidget(self.workspace_widget, 0, 1, 2, 1)

    def get_workspace(self):
        self.event_manager.register(CreateWorkspace())

    def set_working_directory(self, filepath):
        self.working_directory = filepath
        print(self.working_directory)

    def set_active_tool(self, tool):
        self.active_tool = tool

    def set_canvas_to_save(self, canvas):
        self.canvas_to_save = canvas

    # Button Functions
    def select_working_directory(self):
        print(self.working_directory)
        directory = QFileDialog.getExistingDirectory(self, "Select Working Directory", self.working_directory)
        print(directory)
        if directory:
            self.event_manager.register(ChangedWorkingDirectory(directory))

    def save_session(self):
        filepath, _ = QFileDialog.getSaveFileName(
            None, "Save Session", self.working_directory, "Mosaic files (*.mosaic)"
        )
        if filepath:
            filepath = filepath if filepath.endswith((".mosaic")) else filepath + ".mosaic"
            self.event_manager.register(SaveSession(filepath))

    def load_session(self):
        filepath, _ = QFileDialog.getOpenFileName(
            None, "Load Session", self.working_directory, "Mosaic files (*.mosaic)"
        )
        if filepath:
            filepath = filepath if filepath.endswith((".mosaic")) else filepath + ".mosaic"
            self.event_manager.register(LoadSession(filepath))

    def save_active_canvas(self):
        self.event_manager.register(GetActiveTool())
        # print(self.active_tool)
        if self.active_tool is not None:
            self.event_manager.register(GetActiveCanvas(self.active_tool))
            # print(type(self.canvas_to_save))
            # print(self.canvas_to_save.shape)
            if self.canvas_to_save is not None:
                filepath, _ = QFileDialog.getSaveFileName(
                    None, "Select Base Image", self.working_directory, "PNG files (*.png)"
                )
                if filepath:
                    filepath = filepath if filepath.endswith((".png", ".PNG")) else filepath + ".png"
                    Image.fromarray(self.canvas_to_save).save(filepath)
                    self.event_manager.register(MosaicSaved())
            else:
                self.event_manager.register(MosaicSaveFailed())
        self.active_tool = None
        self.canvas_to_save = None

    # Backend Functions -------------------------------------------------------

    def update_log_stream(self):
        # Assuming self.log_stream is a QTextEdit or QPlainTextEdit instance
        text = ""
        for t in self.event_manager.log:
            text += f"{t}\n"

        # Define the style for the log stream, similar to other widgets
        log_stream_style = """
            QTextEdit {
                color: white;
                font: 12px Century Gothic;
                background-color: #455361;
                border-radius: 0px;
                padding: 5px;
            }
            """

        self.log_stream.clear()  # Clear the current text
        self.log_stream.setStyleSheet(log_stream_style)  # Apply the defined style
        self.log_stream.setPlainText(text)  # Use setPlainText for QPlainTextEdit or setHtml for rich text in QTextEdit

        # Optionally, scroll to the end of the log
        # self.log_stream.moveCursor(QTextEdit.End)


# EVENTS FROM THIS MODULE ----------------------------------------------------------------------------------


class CreateWorkspace(Event):
    def __init__(self):
        super(CreateWorkspace, self).__init__()
        self.module = module_name
        self.title = "create_workspace_widget"
        self.listeners = None

    def emit(self):
        widget = self.modules["WorkspaceManager"].get_workspace_widget()
        self.modules["UserInterface"].create_workspace(widget)
        self.modules["UserInterface"].update_log_stream()


class GetActiveTool(Event):
    def __init__(self):
        super(GetActiveTool, self).__init__()
        self.module = module_name
        self.title = "get_active_tool"
        self.listeners = None

    def emit(self):
        tool = self.modules["WorkspaceManager"].get_active_tool()
        self.modules["UserInterface"].set_active_tool(tool)
        self.modules["UserInterface"].update_log_stream()


class GetActiveCanvas(Event):
    def __init__(self, tool):
        super(GetActiveCanvas, self).__init__()
        self.module = module_name
        self.title = "get_active_canvas"
        self.listeners = None
        self.tool = tool

    def emit(self):
        canvas = self.modules[self.tool].get_canvas_image()
        self.modules["UserInterface"].set_canvas_to_save(canvas)
        self.modules["UserInterface"].update_log_stream()


class ChangedWorkingDirectory(Event):
    def __init__(self, filepath):
        super(ChangedWorkingDirectory, self).__init__()
        self.module = module_name
        self.title = "changed_working_directory"
        self.listeners = None
        self.filepath = filepath

    def emit(self):
        for tool in self.modules:
            self.modules[tool].set_working_directory(self.filepath)
        self.modules["UserInterface"].update_log_stream()


class SaveSession(Event):
    def __init__(self, filepath):
        super(SaveSession, self).__init__()
        self.module = module_name
        self.title = "save_session_from_main_UI"
        self.filepath = filepath
        self.listeners = None

    def emit(self):
        self.modules["FileHandler"].set_working_directory(os.path.dirname(self.filepath))
        self.modules["FileHandler"].set_session_filename(os.path.basename(self.filepath))
        self.modules["FileHandler"].save_session()
        self.modules["UserInterface"].update_log_stream()


class LoadSession(Event):
    def __init__(self, filepath):
        super(LoadSession, self).__init__()
        self.module = module_name
        self.title = "load_session_from_main_UI"
        self.filepath = filepath
        self.listeners = None

    def emit(self):
        self.modules["FileHandler"].set_working_directory(os.path.dirname(self.filepath))
        self.modules["FileHandler"].set_session_filename(os.path.basename(self.filepath))
        self.modules["FileHandler"].load_session()
        self.modules["UserInterface"].update_log_stream()


class MosaicSaved(Event):
    def __init__(self):
        super(MosaicSaved, self).__init__()
        self.module = module_name
        self.title = "mosaic_saved"
        self.listeners = None

    def emit(self):
        self.modules["UserInterface"].update_log_stream()


class MosaicSaveFailed(Event):
    def __init__(self):
        super(MosaicSaveFailed, self).__init__()
        self.module = module_name
        self.title = "mosaic_save_failed"
        self.listeners = None

    def emit(self):
        self.modules["UserInterface"].update_log_stream()
