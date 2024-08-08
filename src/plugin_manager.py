import os
import importlib.util
from event_manager import Event
from datetime import datetime

module_name = "PluginManager"


class PluginManager:
    def __init__(self, event_manager, plugins_folder):
        """
        Initialize the PluginManager.

        :param event_manager: The event manager to register plugins with.
        :param plugins_folder: The folder where plugins are stored.
        """
        self.event_manager = event_manager
        self.plugin_folder = plugins_folder
        self.plugins = {}  # Store plugin info

    def discover_plugins(self):
        """Discovers and registers plugins from the plugin folder."""
        print("looking for plugins")
        for filename in os.listdir(self.plugin_folder):
            if filename.endswith(".py"):
                plugin_path = os.path.join(self.plugin_folder, filename)
                self.load_plugin(plugin_path)
        print(self.plugins)
        self.event_manager.register(RegisterPlugins())

    def load_plugin(self, plugin_path):
        """Loads a plugin file and registers the plugin."""
        print("loading: ", plugin_path)
        spec = importlib.util.spec_from_file_location("module.name", plugin_path)
        plugin_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(plugin_module)
        try:
            plugin_module.register(self)
        except:
            pass

    def register_plugin(self, name, description, plugin_class):
        """Registers a plugin with its information."""
        self.plugins[name] = {"description": description, "class": plugin_class}

    def create_plugin_instance(self, plugin_name, load_name=None):
        """Creates an instance of a plugin."""
        if plugin_name is not None:
            plugin_info = self.plugins.get(plugin_name)
            if plugin_info:
                if load_name is None:
                    # datetag for the instance
                    datetag = datetime.now().strftime("%y%m%d_%H%M%S")
                    name = f"{plugin_name}_{datetag}"
                else:
                    name = load_name
                plugin_instance = plugin_info["class"](name, self.event_manager)  # Create the instance
                self.event_manager._modules[name] = plugin_instance  # Register with the event manager
                plugin_instance.configure()  # Layer class function; configure after registering with event manager
                return name, plugin_instance
            else:
                raise ValueError(f"No plugin found with the name: {plugin_name}")

    def gen_plugins_list(self):
        return list(self.plugins.keys())

    def set_working_directory(self, path):
        pass


# EVENTS FROM THIS MODULE ----------------------------------------------------------------------------------


class RegisterPlugins(Event):
    def __init__(self):
        super(RegisterPlugins, self).__init__()
        self.module = module_name
        self.title = "register_plugins_with_workspace_manager"
        self.listeners = None

    def emit(self):
        plugins = self.modules["PluginManager"].gen_plugins_list()
        self.modules["WorkspaceManager"].init_plugins(plugins)
        self.modules["UserInterface"].update_log_stream()
