import os
import sys
import json
from event_manager import Event

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

module_name = "ConfigManager"


class ConfigManager:
    def __init__(self, event_manager, config_path=None):
        self.event_manager = event_manager
        self.config = None
        self.config_path = config_path
        self.working_directory = r"C:\Users"

    def get_config(self):
        return self.config.copy()

    def set_config_path(self, config_path):
        self.config_path = config_path

    def load_config(self):
        if self.config_path is not None:
            with open(self.config_path, "r") as cfg:
                cfg = json.load(cfg)
            self.config = cfg
        else:
            files = os.listdir(script_dir)
            for f in files:
                if "session_config" in f:
                    with open(os.path.join(script_dir, f), "r") as cfg:
                        self.config = json.load(cfg)
                    break
        if self.config is not None:
            self.event_manager.register(LoadConfig(self.config))

    def set_working_directory(self, dir):
        self.working_directory = dir


# EVENTS FROM THIS MODULE ----------------------------------------------------------------------------------


class LoadConfig(Event):
    def __init__(self, config):
        super(LoadConfig, self).__init__()
        self.module = module_name
        self.title = "launch_config"
        self.listeners = None
        self.config = config

    def emit(self):
        wd = self.config.get("working_directory", r"C:\Users")
        print(wd)
        self.modules["ConfigManager"].set_working_directory(wd)
        self.modules["UserInterface"].set_working_directory(wd)
        self.modules["UserInterface"].update_log_stream()
