from taskqueue.task import Task, Priority
from taskqueue.storage.redis_backend import RedisBackend
from typing import Union, Optional

class Queue:
    def __init__(self, backend=None, redis_host='localhost', redis_port=6379, redis_db=0, redis_password=None):
        """Initialize the queue."""
        if backend is not None:
                self._backend = backend
        else:
            self._backend = RedisBackend(host = redis_host, port = redis_port, db = redis_db, password = redis_password)
                    

    def enqueue(self, task_name, *args, priority: Union[str,int] = "medium", max_retries: int = 3, **kwargs):

        if isinstance(priority, str): # checks if priority is of type string
            priority_lower = priority.lower()

            if priority_lower == "low":
                priority = Priority.Low

            elif priority_lower == "medium":
                priority = Priority.Medium
            
            elif priority_lower == "high":
                priority = Priority.High
            
            else:
                #default to medium
                priority = Priority.Medium
    
        task = Task(
            name = task_name,
            args = args,
            kwargs=kwargs,
            priority=priority,
            max_retries=max_retries
        )

        self._backend.push(task) #private attribute
        return task # to look it up later if needed
    
    def get_length(self, priority = None): # Allows for all or specific priority queues
        """Get the number of tasks in the queue."""
        return self._backend.get_queue_length(priority)
    
    # Calling backend methods and returning their results

    def get_task(self, task_id):
        """Retrieve a task by its ID."""
        return self._backend.get_task(task_id)
    
    def get_stats(self):
        """Get statistics about the queue."""
        return self._backend.get_stats()
    
    def clear(self):
        """Clear all tasks from the queue."""
        self._backend.clear()

    def __enter__(self):
        return self # returns object to be used in with statement
    
    def __exit__(self, exc_type, exc_value, traceback): # parameters define the exception type, value and traceback
        self._backend.close() # ensures backend connection is closed



