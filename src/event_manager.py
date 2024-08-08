from datetime import datetime


class EventManager:
    _modules = None  # Dictionary {"name": module}

    @classmethod
    def set_modules(cls, modules):
        cls._modules = modules

    @classmethod
    def get_modules(cls):
        return cls._modules

    def __init__(self):
        self.events = []
        self.log = []

    def _log_event(self, event):
        print("time: ", event.time)
        print("event:", event.title)
        self.log.append(event.time)
        self.log.append(event.title)

    def register(self, event):
        self.events.append(event)
        # print("received event")
        self.execute()

    def execute(self):
        # print("executing")
        while self.events:
            event = self.events.pop()
            self._log_event(event)
            event.emit()
        print("No more events")


class Event:
    def __init__(self):
        self.title = None
        self.time = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.listeners = None
        self.modules = EventManager.get_modules()
        self.name = "unknown"

    def emit(self):
        raise NotImplementedError
