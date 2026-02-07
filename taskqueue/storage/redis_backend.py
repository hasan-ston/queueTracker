import redis
from taskqueue.storage.base import storage_backend
from taskqueue.task import Task, TaskStatus, Priority
import json 

class RedisBackend(storage_backend):
    def __init__(self, host='localhost', port=6379, db=0, password=None):
        #try to connect to redis server

        try:
            self._redis = redis.Redis(host=host, port=port, db=db, password=password, decode_responses=True)
            self._redis.ping() # check if connection is successful

        except redis.ConnectionError as e:
            raise ConnectionError(f"failed to connect to redis server: {e}")
        
    QUEUE_KEY = "task_queue:queue"
    TASK_KEY = "task_queue:task"
    
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

        self._redis.set(task_key, task.to_json()) # writes task data inside redis with task id as key and json string as value
        self._redis.lpush(queue_key, task.id) #FIFO
        self._redis.hincrby(f"{self.QUEUE_KEY}", 1) # increment total task count in queue

    def pop(self, piority=None):
        
        for prior in [Priority.High, Priority.Medium, Priority.Low]: 
            queue_key = self._get_queue_key(prior)
            task_id = self._redis.rpop(queue_key) #FIFO

            if task_id:
                break
        if not task_id:
            return None
        
        #retrieving task data from redis and deserializing

        task_key = self._get_task_key(task_id)
        task_data = self._redis.get(task_key)

        if not task_data:
            return None
        
        return Task.from_json(task_data)
    
    def get_task(self, task_id): #getting task data by id

        task_key = self._get_task_key(task_id)
        task_data = self._redis.get(task_key)

        if not task_data:
            return None
        
        return Task.from_json(task_data)
    
    def requeue(self, task): 
        self._redis.srem(self.Processing_key, task.id) # remove from processing 
        retried_task = task.increment_retry()
        self.update_task(retried_task)
        queue_key = self._get_queue_key(retried_task.priority)
        self._redis.lpush(queue_key, retried_task.id) # requeue task

    def close(self):
        self._redis.close()

    def get_processing_tasks(self): 
        task_ids = self._redis.smembers(self.Processing_key)
        tasks = []
        for task_id in task_ids:
            task = self.get_task(task_id)
            if task:
                tasks.append(task)
        return tasks
    
    def get_processing_count(self):
        return self._redis.scard(self.Processing_key)
        