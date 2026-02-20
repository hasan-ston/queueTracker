from datetime import datetime, timezone
import json
import uuid

class TaskStatus:
    PENDING = 'pending'
    ENQUEUED = 'enqueued'
    COMPLETED = 'completed'
    FAILED = 'failed'
    PROCESSING = 'processing'


class Priority:
    """ level 1 to 3 """
    High = 1
    Medium = 2
    Low = 3

class Task:

    def __init__(self, name, id=None, args = None, kwargs = None, priority=Priority.High, status = TaskStatus.PENDING, created_at = None, retry_count=0, max_retries=3):
        self.id = id or str(uuid.uuid4())
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
            'created_at': self.created_at.isoformat(),
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
        }
        return json.dumps(data)  # converts python object to json string
    
    @staticmethod
    def from_json(json_str):
        data = json.loads(json_str)
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        # ensure retry fields are present
        data.setdefault('retry_count', 0)
        data.setdefault('max_retries', 3)
        return Task(**data)
    
    """ retrying if retry counts left """
    @property
    def can_retry(self):
        return self.retry_count < self.max_retries

    def increment_retry(self):
        self.retry_count = (self.retry_count or 0) + 1
        return self
