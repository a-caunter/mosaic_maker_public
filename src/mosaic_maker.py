from PyQt6.QtWidgets import QApplication
import sys
import application
from mosaic_util.classify_image_library import Block  # need this
import ui.ui_styles as ui_styles


class AppLauncher:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyleSheet(ui_styles.tooltip)
        self.mosaic_maker = self.launch_app()

    def launch_app(self):
        # Create the main application
        app = application.MosaicMaker()
        return app


# Initialize and run the PyQt application
app_launcher = AppLauncher()
sys.exit(app_launcher.app.exec())
