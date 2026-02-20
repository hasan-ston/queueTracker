from .task import Task, Priority

class Scheduler:
    def __init__(self, backend):
        self.backend = backend

    def get_next_task(self):
        # Priority constants on Task use `High`, `Medium`, `Low` (capitalized)
        for priority in [Priority.High, Priority.Medium, Priority.Low]:
            task = self.backend.pop(priority)
            if task:
                return task
        return None