from .task import Task, Priority

class Scheduler:
    def __init__(self, backend):
        self.backend = backend

    def get_next_task(self):
        for priority in [Priority.HIGH, Priority.MEDIUM, Priority.LOW]:
            task = self.backend.pop(priority)
            if task:
                return task
        return None