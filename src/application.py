from user_interface import UserInterface
from event_manager import EventManager
from config_manager import ConfigManager
from plugin_manager import PluginManager
from workspace_manager import WorkspaceManager
from file_handler import FileHandler

import os

script_dir = os.path.dirname(os.path.abspath(__file__))


class MosaicMaker:
    def __init__(self, config_path=None):
        self.modules = {}  # Dictionary of modules for the event manager
        self.config_path = config_path
        self.plugins_path = os.path.join(script_dir, "plugins")

        # Modules
        self.event_manager = EventManager()
        self.workspace_manager = WorkspaceManager(self.event_manager)
        self.modules["WorkspaceManager"] = self.workspace_manager
        self.plugin_manager = PluginManager(self.event_manager, self.plugins_path)
        self.modules["PluginManager"] = self.plugin_manager
        self.user_interface = UserInterface(self.event_manager)
        self.modules["UserInterface"] = self.user_interface
        self.config_manager = ConfigManager(self.event_manager, self.config_path)
        self.modules["ConfigManager"] = self.config_manager
        self.file_handler = FileHandler(self.event_manager)
        self.modules["FileHandler"] = self.file_handler
        EventManager.set_modules(self.modules)

        self.config_manager.load_config()

        self.user_interface.get_workspace()
        self.plugin_manager.discover_plugins()
        self.user_interface.show()
