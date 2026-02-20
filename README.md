# TaskQueue — Quick start (Docker)

This repository uses Docker for running Redis. 

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
