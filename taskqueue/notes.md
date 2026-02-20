- Message Queues: they store messages in queue until the receiving service is ready to process them, ensuring decoupling between systems. Apache Kafka uses this
- Task Queues: Uses background workers for processing and distributing tasks, typically in an asynchronous manner, enabling efficient execution of task that don’t need to be completed immediately. Tasks are added to the queue and then assigned to workers which execute them in the background. Redis Queue uses this.
- To enqeue a job, we call the queue object, and call the enqeue method, and point it to the function to be exectued.
- Each job is defined by a unique id
- Task are serialized to JSON strings and stored in Redis. Then when a worker pulls a job, it deserializes the JSON string back into a python object. Reason why is because Redis stores everything as strings.
- ABC: It is a blueprint that forces subclasses to implement specific methods. It defines what methods must exist, not how they work. They dont have any implementation code, just pass.
- Methods like get_task(task_id) take just the ID because you're looking for the task
- Methods like requeue(task) take the whole object as we already have it.
- Using 'with' abstracts away most of the resource handling logic. It allows using context managers to pack the code that handles setup and teardown logic.

- Queue Class: 
1) purpose is to add tasks to the queue (user side)
2) enqueue() converts user input into Task objects
3) Converts string priorities to ints
4) Methods don't handle the logic, that is assigned to the backend
5) this is separate from the storage implementation, modular design

- Instantiating a logger: can be done by callling logging.getLogger()

- Worker Class:
1) Three main parts: registration, processing, and execution of tasks
2) Registration: @worker.task() decorator or `worker.register(name, handler)` method
3) _process_task(): executes handler, implements retry logic, marks completed or failed
4) _worker_loop(): polls for tasks using `_scheduler.get_next_task()`.
5) `run()`: lifecycle management, supports single/multi-threaded via ThreadPoolExecutor, and has implemented graceful shutdown
6) Error handling prevents worker crashes.

- RedisBackend:
1) Stores tasks as serialized JSON strings in Redis
2) Uses Redis lists for priority queues
3) FIFO 
4) Pop() iterates through priority levels in descending order to get highest priority task first
5) get_task() retrieves the stored task meta data and deserializes to Task object
6) get_processing_count() uses Redis set (SMEMBERS) to track currently processing tasks

- JSON serialization gotcha: json.loads() deserializes arrays back as lists, not tuples. If your code expects a tuple (e.g. task.args), you need to explicitly cast it back with tuple() after deserializing. 
- Task status must be reset on requeue: when a task fails and gets pushed back onto the queue, its status should be set back to ENQUEUED before saving. If skipped, the stored task metadata shows PROCESSING even though it's sitting in the queue waiting
- Shared mutable state across threads: if multiple worker threads update the same counter or dict, you need a threading.Lock() to prevent race conditions. Wrap reads and writes with with lock: to ensure only one thread touches the value at a time. 
- sys.path and script execution: when you run python examples/script.py, Python sets sys.path[0] to the examples/ directory, not the project root. This means import taskqueue fails even if the package exists one level up. Fix by inserting the project root into sys.path at the top of the script using os.path.abspath(file)
- Scheduler as a separate class: isolating priority-order task selection into a Scheduler class means the Worker doesn't need to know anything about priority levels or queue structure. If you add a new priority level or change selection logic, you only touch scheduler, not worker or RedisBackend.
