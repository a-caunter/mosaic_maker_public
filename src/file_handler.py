from event_manager import Event
import zipfile
import numpy as np
import json
import os
import pickle


module_name = "FileHandler"


class FileHandler:
    def __init__(self, event_manager):
        self.event_manager = event_manager
        self.working_directory = None
        self.session_filename = None
        self.save_json = {}  # Dictionary to dump to a  JSON
        self.save_big_data = {}  # Dictionary of numpy arrays to save as .npy files
        self.files_to_zip = []  # Individual files that will be zipped
        self.active_tools = {}

    # SETTERS and GETTERS ----------------------------------------------

    def set_active_tools(self, tools):
        if tools is not None:
            self.active_tools = tools.copy()

    def set_working_directory(self, path):
        self.working_directory = path
        print("path: ", self.working_directory)

    def set_session_filename(self, name):
        self.session_filename = name
        print("filename: ", self.session_filename)

    def save_session(self):
        self.event_manager.register(SaveWorkspaceManager())
        self.event_manager.register(UpdateActiveTools())
        ignore = ["LibraryViewer"]
        print(self.active_tools)
        for tool in self.active_tools:
            if self.active_tools[tool].type not in ignore:
                self.event_manager.register(SaveActiveTool(tool))
        # print("json: ", self.save_json)
        # print("big_data: ", self.save_big_data.keys())
        # Using json.dump() to write the data to a JSON file
        json_name = os.path.join(self.working_directory, "session.json")
        with open(json_name, "w") as json_file:
            json.dump(self.save_json, json_file)
            self.files_to_zip.append(json_name)
        for big in self.save_big_data:
            big_name = os.path.join(self.working_directory, big)
            if big.endswith(".npy"):
                np.save(big_name, self.save_big_data[big])
            elif big.endswith(".pkl"):
                with open(big_name, "wb") as file:
                    pickle.dump(self.save_big_data[big], file)
            self.files_to_zip.append(big_name)
        # Create a new ZIP file
        with zipfile.ZipFile(os.path.join(self.working_directory, self.session_filename), "w") as zipf:
            for file in self.files_to_zip:
                # Specify the name of the file within the ZIP archive
                arcname = os.path.basename(file)
                zipf.write(file, arcname=arcname)
                os.remove(file)
        self.reset()

    def load_session(self):
        zip_file_path = os.path.join(self.working_directory, self.session_filename)

        # Open the ZIP file for reading
        with zipfile.ZipFile(zip_file_path, "r") as zipf:
            # Extract the specific file you want to access (e.g., "data_file.txt")
            # try:
            with zipf.open("session.json") as file:
                # Read and process the contents of the file
                data = json.load(file)
                if "WorkspaceManager" in data:
                    self.event_manager.register(LoadWorkspaceManager(data["WorkspaceManager"]))
                    for obj in data:
                        if obj != "WorkspaceManager":
                            self.event_manager.register(LoadTool(data[obj]))
                else:
                    print("'WorkspaceManager' state not found.")
        # except KeyError:
        #     print("'session.json' not found in the ZIP archive.")
        # except Exception as e:
        #     print(f"An error occurred: {e}")

    def retreive_data(self, array_name):
        zip_file_path = os.path.join(self.working_directory, self.session_filename)
        # Open the ZIP file for reading
        with zipfile.ZipFile(zip_file_path, "r") as zipf:
            # Extract the specific NumPy array file you want to access (e.g., "data_array.npy")
            if array_name.endswith(".npy"):
                try:
                    with zipf.open(array_name) as file:
                        # Load the NumPy array from the file
                        arr = np.load(file)
                        return arr
                except KeyError:
                    print("'data_array.npy' not found in the ZIP archive.")
                except Exception as e:
                    print(f"An error occurred: {e}")
            elif array_name.endswith(".pkl"):
                try:
                    with zipf.open(array_name) as file:
                        loaded_data = pickle.load(file)
                        return loaded_data
                except KeyError:
                    print("'data_array.npy' not found in the ZIP archive.")
                except Exception as e:
                    print(f"An error occurred: {e}")

    def compile_save_file(self, object, data, arrays):
        print(data)
        self.save_json[object] = data
        self.save_big_data.update(arrays)

    def reset(self):
        self.working_directory = None
        self.session_filename = None
        self.save_json = {}  # Dictionary to dump to a  JSON
        self.save_big_data = {}  # Dictionary of numpy arrays to save as .npy files
        self.files_to_zip = []  # Individual files that will be zipped
        self.active_tools = {}


# EVENTS FROM THIS MODULE ----------------------------------------------------------------------------------


class SaveWorkspaceManager(Event):
    def __init__(self):
        super(SaveWorkspaceManager, self).__init__()
        self.module = module_name
        self.title = "save_workspace_manager"
        self.listeners = None

    def emit(self):
        data, arrays = self.modules["WorkspaceManager"].save_state()
        print("workspace save: ", data)
        self.modules["FileHandler"].compile_save_file("WorkspaceManager", data, arrays)
        self.modules["UserInterface"].update_log_stream()


class UpdateActiveTools(Event):
    def __init__(self):
        super(UpdateActiveTools, self).__init__()
        self.module = module_name
        self.title = "update_active_tools"
        self.listeners = None

    def emit(self):
        tools = self.modules["WorkspaceManager"].get_active_tools()
        self.modules["FileHandler"].set_active_tools(tools)
        self.modules["UserInterface"].update_log_stream()


class SaveActiveTool(Event):
    def __init__(self, tool_name):
        super(SaveActiveTool, self).__init__()
        self.module = module_name
        self.tool_name = tool_name
        self.title = "save_active_tool"
        self.listeners = None

    def emit(self):
        data, arrays = self.modules[self.tool_name].save_state()
        self.modules["FileHandler"].compile_save_file(self.tool_name, data, arrays)
        self.modules["UserInterface"].update_log_stream()


class LoadWorkspaceManager(Event):
    def __init__(self, data):
        super(LoadWorkspaceManager, self).__init__()
        self.module = module_name
        self.data = data
        self.title = "load_workspace_manager"
        self.listeners = None

    def emit(self):
        self.modules["WorkspaceManager"].load_state(self.data)
        self.modules["UserInterface"].update_log_stream()


class LoadTool(Event):
    def __init__(self, data):
        super(LoadTool, self).__init__()
        self.module = module_name
        self.data = data
        self.title = "load_tool"
        self.listeners = None

    def emit(self):
        name = self.data["data"]["name"]
        plugin_name, plugin_instance = self.modules["PluginManager"].create_plugin_instance(
            self.data["data"]["type"], load_name=name
        )
        print(plugin_name, plugin_instance)
        self.modules[name].load_state(self.data)
        self.modules["WorkspaceManager"].open_plugin_instance(plugin_name, plugin_instance)
        self.modules["UserInterface"].update_log_stream()
