from datetime import datetime, timezone
import json

class Task:
    """
    This represents a task in the task queue system.
    Attributes include:
    - id: a unique identifier for the task
    - name: name of task to be performed
    - args, kwargs: positional and keyword arguments for the task
    - priority: 1 (highest) to 3(lowest)
    - status of task currently
    - created_at: timestamp when task was created
    - retry_count: number of times task has been retried
    - max_retries: maximum number of retries allowed for the task
    """
    def __init__(self, id, name, args = None, kwargs = None, priority=Priority.High, status = TaskStatus.PENDING, created_at = None, retry_count=0, max_retries=3):
        self.id = id
        self.name = name
        self.args = args or () # 'or' returns the first truthy value
        self.kwargs = kwargs if kwargs is not None else {}
        self.priority = priority
        self.retry_count = retry_count
        self.max_retries = max_retries
        self.created_at = created_at or datetime.now(timezone.utc)
        self.status = status

    def to_json(self):
        data = {
            'id': self.id,
            'name': self.name,
            'args': self.args,
            'kwargs': self.kwargs,
            'priority': self.priority,
            'status': self.status,
            'created_at': self.created_at
        }
        return json.dumps(data)  # converts python object to json string
    
    """ deserializing from json string to python object """
    def from_json(json_str):
        data = json.loads(json_str)
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return Task(**data)
    
    """ retrying if retry counts left """
    @property
    def can_retry(self):
        return self.retry_count < self.max_retries

class TaskStatus:
    """ Current status of task, whether it's pending, enqueued, completed, or failed. """
    PENDING = 'pending'
    ENQUEUED = 'enqueued'
    COMPLETED = 'completed'
    FAILED = 'failed'


class Priority:
    """ level 1 to 3 """
    High = 1
    Medium = 2
    Low = 3