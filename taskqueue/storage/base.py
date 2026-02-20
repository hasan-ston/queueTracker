
from abc import ABC, abstractmethod
from typing import Optional
from taskqueue.task import Task


class storage_backend(ABC):
    @abstractmethod
    def push(self, task: Task):
        """Push a task onto the queue.

        Args:
            task: The `Task` instance to be enqueued.
        """
        pass

    @abstractmethod
    def pop(self, priority: Optional[int] = None) -> Optional[Task]:
        """Pop a task from the queue.

        If `priority` is provided, pop from that priority queue; otherwise
        the implementation should return the highest-priority available task.
        """
        pass

    @abstractmethod
    def get_task(self, task_id: str) -> Optional[Task]:
        """Retrieve a task by its ID.

        Returns `None` if the task is not found.
        """
        pass

    @abstractmethod
    def update_task(self, task: Task):
        """Persist updated task state (status, retry_count, etc.)."""
        pass

    @abstractmethod
    def mark_processing(self, task: Task):
        """Mark a task as being processed and track it as in-flight."""
        pass

    @abstractmethod
    def mark_completed(self, task: Task):
        """Mark a task as completed and clear any in-flight tracking."""
        pass

    @abstractmethod
    def mark_failed(self, task: Task):
        """Mark a task as failed and clear any in-flight tracking."""
        pass

    @abstractmethod
    def requeue(self, task: Task):
        """Requeue a task for later processing (usually after retry increment)."""
        pass

    @abstractmethod
    def get_queue_length(self, priority: Optional[int] = None) -> int:
        """Return count of tasks in queue (or for a specific priority)."""
        pass

    @abstractmethod
    def get_processing_count(self) -> int:
        """Return count of tasks currently being processed."""
        pass

    @abstractmethod
    def get_stats(self) -> dict:
        """Return a dictionary of queue/processing statistics."""
        pass

    @abstractmethod
    def close(self):
        """Close connections to the backend and cleanup resources."""
        pass

