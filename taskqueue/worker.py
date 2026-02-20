from concurrent.futures import ThreadPoolExecutor
import logging
import time
from taskqueue.task import Task, TaskStatus
from taskqueue.storage.redis_backend import RedisBackend
from taskqueue.scheduler import Scheduler

logger = logging.getLogger(__name__)


class Worker:
    def __init__(self, backend=None, redis_host='localhost', redis_port=6379, redis_db=0, redis_password=None, concurrency=1, poll_interval=1.0):
        """Initialize the worker."""
        if backend is not None:
            self._backend = backend
        else:
            self._backend = RedisBackend(host=redis_host, port=redis_port, db=redis_db, password=redis_password)

        self._scheduler = Scheduler(self._backend)
        self._handlers = {}
        self._concurrency = concurrency
        self._poll_interval = poll_interval
        self._executor = None
        self._running = False
        self._shutdown_requested = False

    def task(self, name=None):
        def decorator(func):
            task_name = name or func.__name__
            self._handlers[task_name] = func
            return func

        return decorator

    def register(self, name, handler):
        """Register a task handler."""
        self._handlers[name] = handler
        logger.debug("Task handler '%s' registered.", name)

    def _process_task(self, task):
        """Process one task."""
        handler = self._handlers.get(task.name)
        if not handler:
            raise ValueError(f"Registration for task '{task.name}' not found.")

        try:
            logger.info(f"Processing task ({task.name})")
            self._backend.mark_processing(task)
            handler(*task.args, **task.kwargs)
            self._backend.mark_completed(task)
            logger.info(f"Task ({task.name}) completion successful.")

        except Exception as e:
            logger.error("Task (%s) failed. Error: %s", task.name, e)
            if task.can_retry:
                task.increment_retry() 
                logger.info(f"requeuing task ({task.name})")
                logger.info(f"retries left: {task.retry_count+1}/{task.max_retries}")
                self._backend.requeue(task)
            else:
                logger.warning(f"Max retries reached for task ({task.name})")
                self._backend.mark_failed(task)

    def _worker_loop(self):
        while self._running:
            try:
                task = self._scheduler.get_next_task()
                if not task:
                    time.sleep(self._poll_interval)
                    continue

                if task.name not in self._handlers:
                    logger.error("No handlers for task '%s'. Moving on", task.name)
                    self._backend.mark_failed(task)
                    continue

                self._process_task(task)

            except Exception as e:
                logger.error("Error found in worker loop: %s", e)
                time.sleep(self._poll_interval)

    def run(self):
        if self._running:
            logger.warning("Worker is already running.")
            return

        self._running = True
        self._shutdown_requested = False

        logger.info("Worker started with concurrency: %s", self._concurrency)
        logger.info("Registered task handlers : %s", list(self._handlers.keys()))

        try:
            if self._concurrency == 1:
                self._worker_loop()
            else:
                self._executor = ThreadPoolExecutor(max_workers=self._concurrency)
                futures = [self._executor.submit(self._worker_loop) for _ in range(self._concurrency)]

                for future in futures:
                    try:
                        future.result()
                    except Exception as e:
                        logger.error("Worker thread encountered an error: %s", e)

        except KeyboardInterrupt:
            logger.info("Shuting down")

        finally:
            self._shutdown()

    def _shutdown(self):
        logger.info("Shutting worker down")
        self._running = False

        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None

        try:
            self._backend.close()
        except Exception:
            pass

        logger.info("Worker shutdown complete")
