from event_manager import Event
from PyQt6.QtWidgets import (
    QWidget,
    QFrame,
    QGridLayout,
    QSizePolicy,
)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt
from zoomable_view import ZoomableGraphicsView

module_name = "LayerClass"


class Layer:
    def __init__(self):
        self.name = None
        self.mask = None
        self.transparency = None
        self.priority = None

        self.layout = QGridLayout()

        self.canvas_image = None

        self.working_directory = r"C:\Users"

    def configure(self):
        # Should be implemented in the subclasses if needed
        pass

    def update(self):
        # Should be implemented in the subclasses if needed
        pass

    def get_name(self):
        return self.name

    def get_mask(self):
        return self.mask

    def get_transparency(self):
        return self.transparency

    def get_priority(self):
        return self.priority

    def get_canvas_image(self):
        return self.canvas_image

    def set_name(self, name):
        self.name = name

    def set_mask(self, mask):
        self.mask = mask

    def set_transparency(self, transparency):
        self.transparency = transparency

    def set_priority(self, priority):
        self.priority = priority

    def set_working_directory(self, path):
        self.working_directory = path

    def create_canvas(self):
        # Create a QGraphicsView instead of ZoomableLabel
        self.canvas_widget = ZoomableGraphicsView()
        self.canvas_widget.setFrameStyle(QFrame.Shape.Box)
        self.canvas_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.canvas_widget.setMinimumSize(400, 300)
        self.canvas_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Add the view to the layout
        self.layout.addWidget(self.canvas_widget, 0, 0)

    def update_canvas(self):
        if self.canvas_image is None:
            self.event_manager.register(ErrorNoImage())
        else:
            # Convert numpy array to QImage
            height, width, channel = self.canvas_image.shape
            print(height, width, channel)
            bytes_per_line = 3 * width
            q_img = QImage(self.canvas_image.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)

            self.canvas_widget.setPhoto(QPixmap.fromImage(q_img))

    def get_tool_widget(self):
        # Create a new QWidget
        self.tool_widget = QWidget()
        # Set the layout of WorkspaceManager to this widget
        self.tool_widget.setLayout(self.layout)
        # Return the widget
        return self.tool_widget


# EVENTS FROM THIS MODULE ----------------------------------------------------------------------------------


class ErrorNoImage(Event):
    def __init__(self):
        super(ErrorNoImage, self).__init__()
        self.module = module_name
        self.title = "ERROR_no_image"
        self.listeners = None

    def emit(self):
        self.modules["UserInterface"].update_log_stream()
