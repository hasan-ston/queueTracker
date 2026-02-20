import redis
from taskqueue.storage.base import storage_backend
from taskqueue.task import Task, TaskStatus, Priority
import json 

class RedisBackend(storage_backend):
    def __init__(self, host='localhost', port=6379, db=0, password=None):
        try:
            self._redis = redis.Redis(host=host, port=port, db=db, password=password, decode_responses=True)
            self._redis.ping() # check if connection is successful

        except redis.ConnectionError as e:
            raise ConnectionError(f"failed to connect to redis server: {e}")
        
    QUEUE_KEY = "task_queue:queue"
    TASK_KEY = "task_queue:task"
    PROCESSING_KEY = "task_queue:processing"
    
    Priority_queues = {
        Priority.High: f"{QUEUE_KEY}:high",
        Priority.Medium: f"{QUEUE_KEY}:medium",
        Priority.Low: f"{QUEUE_KEY}:low",
    }
        
    def _get_queue_key(self, priority): # selects queue based on priority
        return self.Priority_queues.get(priority, self.Priority_queues[Priority.Medium]) # defaults to medium if none preexisting

    def _get_task_key(self, task_id):
        return f"{self.TASK_KEY}:{task_id}"
    
    def push(self, task):
        queue_key = self._get_queue_key(task.priority)
        task_key = self._get_task_key(task.id)

        # store task payload and push id onto the appropriate priority list
        self._redis.set(task_key, task.to_json())
        self._redis.lpush(queue_key, task.id)

    def pop(self, priority=None):
        """Pop a task from the specified priority queue, or highest available."""
        task_id = None

        if priority is not None:
            queue_key = self._get_queue_key(priority)
            task_id = self._redis.rpop(queue_key)
        else:
            for prior in [Priority.High, Priority.Medium, Priority.Low]:
                queue_key = self._get_queue_key(prior)
                task_id = self._redis.rpop(queue_key)
                if task_id:
                    break

        if not task_id:
            return None

        task_key = self._get_task_key(task_id)
        task_data = self._redis.get(task_key)
        if not task_data:
            return None

        task = Task.from_json(task_data)
        return task
    
    def get_task(self, task_id): #getting task data by id

        task_key = self._get_task_key(task_id)
        task_data = self._redis.get(task_key)

        if not task_data:
            return None
        
        return Task.from_json(task_data)
    
    def requeue(self, task):
        self._redis.srem(self.PROCESSING_KEY, task.id)
        task.status = TaskStatus.ENQUEUED  # reset status before pushing back
        self.update_task(task)
        queue_key = self._get_queue_key(task.priority)
        self._redis.lpush(queue_key, task.id)

    def close(self):
        self._redis.close()

    def get_processing_tasks(self): 
        task_ids = self._redis.smembers(self.PROCESSING_KEY)
        tasks = []
        for task_id in task_ids:
            task = self.get_task(task_id)
            if task:
                tasks.append(task)
        return tasks
    
    def get_processing_count(self):
        return self._redis.scard(self.PROCESSING_KEY)
    
    def update_task(self, task):
        task_key = self._get_task_key(task.id)
        self._redis.set(task_key, task.to_json())

    def mark_processing(self, task):
        # add to processing set and update status
        task.status = TaskStatus.PROCESSING
        self.update_task(task)
        self._redis.sadd(self.PROCESSING_KEY, task.id)

    def mark_completed(self, task):
        task.status = TaskStatus.COMPLETED
        self.update_task(task)
        self._redis.srem(self.PROCESSING_KEY, task.id)

    def mark_failed(self, task):
        task.status = TaskStatus.FAILED
        self.update_task(task)
        self._redis.srem(self.PROCESSING_KEY, task.id)

    def get_queue_length(self, priority=None):
        if priority is not None:
            queue_key = self._get_queue_key(priority)
            return self._redis.llen(queue_key)
        # sum of all priority queues
        total = 0
        for prior in [Priority.High, Priority.Medium, Priority.Low]:
            total += self._redis.llen(self._get_queue_key(prior))
        return total

    def get_stats(self):
        return {
            'high': self._redis.llen(self.Priority_queues[Priority.High]),
            'medium': self._redis.llen(self.Priority_queues[Priority.Medium]),
            'low': self._redis.llen(self.Priority_queues[Priority.Low]),
            'processing': self.get_processing_count(),
            'total': self.get_queue_length()
        }
        