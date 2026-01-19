# any storage backend must implement these methods

from abc import ABC, abstractmethod
from typing import Optional
from taskqueue.task import Task


class storage_backend(ABC):
    @abstractmethod # this method must be implemented by any subclass
    def push(self, task):
        """Push a task onto the queue.

        Args:
            task: The task to be added to the queue.
        """
        pass

    @abstractmethod
    def pop(self, priority=Optional[int] = None ):
        """Pop a task from the queue.

        Returns:
            The task that was removed from the queue.
        """
        pass

    @abstractmethod
    def peek(self, priority=Optional[int] = None):
        """Peek at the next task in the queue without removing it.

        Returns:
            The next task in the queue.
        """
        pass

    @abstractmethod
    def get_task(self, task_id):
        """Retrieve a task by its ID.

        Args:
            task_id: The unique identifier of the task.

        Returns:
            The task with the specified ID.
        """
        pass

    @abstractmethod
    def update_task(self, task):
        """Update an existing task in the queue.

        Args:
            task: The task with updated information.
        """
        pass

    @abstractmethod
    def delete_task(self, task_id):
        """Delete a task from the queue by its ID.

        Args:
            task_id: The unique identifier of the task to be deleted.
        """
        pass

    @abstractmethod
    def mark_processing(self, task_id):
        """Mark a task as being processed.

        Args:
            task_id: The unique identifier of the task to be marked.
        """
        pass

    @abstractmethod
    def mark_completed(self, task_id):
        """Mark a task as completed.

        Args:
            task_id: The unique identifier of the task to be marked.
        """
        pass

    @abstractmethod
    def mark_failed(self, task_id):
        """Mark a task as failed.

        Args:
            task_id: The unique identifier of the task to be marked.
        """
        pass

    @abstractmethod
    def requeue(self, task):
        """Requeue a task for processing.

        Args:
            task: The task to be requeued.
        """
        pass

    @abstractmethod
    def get_queue_length(self, priority=Optional[int] = None):
        """Get the number of tasks in the queue.

        Returns:
            The number of tasks in the queue.
        """
        pass

    @abstractmethod
    def get_processing_count(self):
        """Get the number of tasks currently being processed.

        Returns:
            The number of tasks being processed.
        """
        pass

    @abstractmethod
    def get_stats(self):
        """Get statistics about the task queue.

        Returns:
            A dictionary containing various statistics about the queue.
        """
        pass

    @abstractmethod
    def clear(self):
        """Clear all tasks from the queue."""
        pass

    @abstractmethod
    def close(self):
        """Close the connecting to backend storage."""
        pass

