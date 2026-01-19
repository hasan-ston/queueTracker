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
