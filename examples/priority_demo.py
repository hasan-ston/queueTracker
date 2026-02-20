import os
import sys
import threading
import time
import logging

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from rich.console import Console
from rich.logging import RichHandler
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from taskqueue.queue import Queue
from taskqueue.storage.redis_backend import RedisBackend
from taskqueue.worker import Worker

console = Console()

logging.basicConfig(
    level=logging.CRITICAL,
    format="%(message)s",
    handlers=[RichHandler(console=console, show_path=False, show_time=False, markup=True)],
)

demo_log = logging.getLogger("demo")
demo_log.setLevel(logging.INFO)
demo_log.propagate = False
demo_log.addHandler(
    RichHandler(console=console, show_path=False, show_time=True, markup=True)
)

counters = {"completed": 0, "failed": 0}
counters_lock = threading.Lock()


PRIORITY_COLOURS = {"high": "red", "medium": "yellow", "low": "cyan"}


def build_stats_table(stats: dict) -> Panel:
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold white")
    table.add_column("", justify="center")     
    table.add_column("Count", justify="right")

    for priority in ("high", "medium", "low"):
        count = stats.get(priority, 0)
        colour = PRIORITY_COLOURS[priority]
        table.add_row(
            Text(f"{priority.capitalize()} queued", style=f"bold {colour}"),
            str(count),
        )

    table.add_row("", "")  

    table.add_row(
        Text("Processing", style="bold magenta"),
        str(stats.get("processing", 0)),
    )

    table.add_row("", "")  

    #  Running totals tracked locally by handlers 
    with counters_lock:
        completed = counters["completed"]
        failed = counters["failed"]

    table.add_row(Text("Completed", style="bold green"),  str(completed))
    table.add_row(Text("Failed",    style="bold red"),    str(failed))

    return Panel(table, title="[bold]Queue Stats[/bold]", border_style="bright_black")

def simple_handler(*args, **kwargs):
    name = kwargs.get("_name", "unknown")
    time.sleep(1.0)
    with counters_lock:
        counters["completed"] += 1
    demo_log.info("[green]✓[/green] %s", name)


def make_flaky_handler(backend):
    """
    Returns a handler with `backend` in a closure — avoids storing a
    non-JSON-serialisable object in task.kwargs (which gets saved to Redis).
    """
    def flaky_handler(*args, **kwargs):
        task_id = kwargs.get("task_id")
        task = backend.get_task(task_id)

        demo_log.info(
            "[yellow]⚡[/yellow] flaky_task — attempt %d/%d",
            task.retry_count + 1,
            task.max_retries,
        )

        time.sleep(1.0)  

        if task.retry_count == 0:
            # Simulate a failure on the first attempt only
            with counters_lock:
                counters["failed"] += 1
            raise RuntimeError("simulated failure")

        with counters_lock:
            counters["completed"] += 1
            counters["failed"] = max(0, counters["failed"] - 1)

        demo_log.info("[green]✓[/green] flaky_task succeeded on retry")

    return flaky_handler

def main():
    backend = RedisBackend()
    try:
        backend._redis.flushdb()
    except Exception:
        pass

    q = Queue(backend=backend)

    q.enqueue("low_task",    priority="low",    _name="low_task")
    q.enqueue("medium_task", priority="medium", _name="medium_task")
    q.enqueue("high_task_1", priority="high",   _name="high_task_1")
    q.enqueue("high_task_2", priority="high",   _name="high_task_2")
    q.enqueue("low_task_2",  priority="low",    _name="low_task_2")

    flaky_task = q.enqueue("flaky_task", priority="high", _name="flaky_task")
    flaky_task.kwargs["task_id"] = flaky_task.id
    backend.update_task(flaky_task)

    console.print(
        Panel(
            "[bold]6 tasks enqueued[/bold]  (3 high · 1 medium · 2 low)\n"
            "Includes [yellow]flaky_task[/yellow] — will fail once then retry.",
            title="TaskQueue Demo",
            border_style="blue",
        )
    )

    worker = Worker(backend=backend, concurrency=1, poll_interval=0.5)
    worker.register("low_task",    simple_handler)
    worker.register("low_task_2",  simple_handler)
    worker.register("medium_task", simple_handler)
    worker.register("high_task_1", simple_handler)
    worker.register("high_task_2", simple_handler)
    worker.register("flaky_task",  make_flaky_handler(backend))

    t = threading.Thread(target=worker.run, daemon=True)
    t.start()

    try:
        with Live(console=console, refresh_per_second=4) as live:
            while True:
                stats = backend.get_stats()
                live.update(build_stats_table(stats))

                if stats.get("total", 0) == 0 and stats.get("processing", 0) == 0:
                    break

                time.sleep(0.25) 

    finally:
        worker._shutdown()
        t.join(timeout=2)
        backend.close()

    console.print(Panel("[bold green]All tasks complete.[/bold green]", border_style="green"))


if __name__ == "__main__":
    main()