# TaskQueue — Quick start (Docker)

This repository uses Docker for running Redis. The included examples run on your host Python environment and connect to the Redis container.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.8+ (for running examples on host)

## Start Redis (Docker)

From the project root run:

```bash
docker-compose up -d
```

This brings up a Redis server listening on the host port 6379 (container service name `redis`).

## Install Python dependencies (on host)

Create and activate a virtual environment, then install requirements:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Run the demo

With Redis running (via `docker-compose`) and your virtualenv active, run:

```bash
python examples/priority_demo.py
```

The demo will enqueue tasks and start a worker to process them. It expects Redis to be accessible at `localhost:6379` (the default in the library).

## Stop services

To stop and remove the Redis container and volume:

```bash
docker-compose down -v
```

## Docker-only (advanced)

If you prefer running the demo inside a container (so everything is in Docker), you can run a one-off Python container attached to the compose network. Note: the example code uses `localhost` by default when creating the Redis client, so you'll need to edit the code (or pass the correct host when instantiating `RedisBackend`) to connect to the `redis` service by name.

Example (attach to the compose network):

```bash
# starts redis
docker-compose up -d

# run a temporary python container attached to the same network
docker run --rm -it -v "$PWD":/app -w /app --network taskqueue_default python:3.11-slim bash
# inside container:
# pip install -r requirements.txt
# python examples/priority_demo.py  # only works if demo is configured to use host 'redis'
```

If your project directory name is different, replace `taskqueue_default` with the correct compose network name.

## Troubleshooting

- If the demo cannot connect to Redis, ensure `docker-compose ps` shows the `redis` service running and that `6379` is exposed.
- If running the demo inside a container, make sure the demo connects to host `redis` (service name) instead of `localhost`.

---

If you'd like, I can also add a `Dockerfile` / `docker-compose` service for running the demo fully in Docker so no host Python is needed. Want me to add that?