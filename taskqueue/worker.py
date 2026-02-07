from concurrent.futures import ThreadPoolExecutor
import logging
from time import time
from taskqueue.task import Task, TaskStatus

logger = logging.getLogger(__name__)

# worker has 3 main parts, registration, processing, execution

class Worker:
    def __init__(self, backend=None, redis_host='localhost', redis_port=6379, redis_db=0, redis_password=None, concurrency=1):
        """Initialize the worker."""
        if backend is not None:
            self._backend = backend
        else:
            self._backend = RedisBackend(host=redis_host, port=redis_port, db=redis_db, password=redis_password)

    
    def task(self, name=None):
        def decorator(func):
            task_name = name or func.__name__
            self._handlers[task_name] = func
            return func 
        return decorator
    
    def register(self, name, handler):
        """Register a task handler."""
        self._handlers[name] = handler
        logger.debug(f"Task handler '{name}' registered.")

    def _process_task(self, task): # Private method
        """process one task only"""

        handler = self._handlers.get(task.name)
        if not handler:
            raise ValueError(f"Registration for task '{task.name}' not found.")
        try:
            logger.info(f"Processing task ({task.name})")
            self._backend.mark_processing(task)
            result = handler(*task.args, **task.kwargs)

            self._backend.mark_completed(task)
            logger.info(f"Task ({task.name}) completion successful.")

        except Exception as e:
            logger.error(f"Task ({"task.name}) failed. Error: {e}"}")
            
            if task.can_retry():
                logger.info(f"requeuing task ({task.name})")
                logger.info(f"retries left: {task.retry_count+1}/{task.max_retries}")
                self._backend.requeue(task)
            else: 
                logger.warning(f"Max retries reached for task ({task.name})")
                self._backend.mark_failed(task)
    
    def _worker_loop(self): # main worker loop that manages task processing
        while self._running:
            try:
                task = self._scheduler.get_next_task()
                if not task: # no tasks found, wait before polling again 
                    time.sleep(self._poll_interval)
                    continue

                if task.name not in self._handlers: #check if handler is registered
                    logger.error(f"No handlers for task '{task.name}'. Moving on")
                    self._backnend.mark_failed(task)
                    continue

                self._process_task(task)

            except Exception as e:
                logger.error(f"Error found in worker loop: {e}")
                time.sleep(self._poll_interval)


    def run(self):
        if self._running:
            logger.warning("Worker is already running.")
            return
        
        self._running = True
        self._shutdown_requested = False
        self._setup_signal_handlers()

        logger.info(f"Worker started with concurrency: {self._concurrency}")
        logger.info(f"Registered task handlers : {list(self._handlers.keys())}")

        try:
            if self._concurrency == 1:
                self._worker_loop() # single threaded
            else:
                self._executor = ThreadPoolExecutor(max_workers = self.concurrency)
                futures = [self._executor.submit(self._worker_loop) for i in range (self._concurrency)]

                for future in futures:
                    try:
                        future.result()
                    except Exception as e:
                        logger.error(f"Worker thread encountered an error: {e}")

        except KeyboardInterrupt:
            logger.info("Shutdown signal received")
        
        finally: 
            self._shutdown()

    def _shutdown(self):
        logger.info("Shutting worker down")
        self._running = False

        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None

        self._backend.close()
        logger.info("Worker shutdown complete")
