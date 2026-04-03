# ACEest Fitness & Gym (Flask) - CI/CD Assignment

This repository contains a lightweight Flask web service that models a fitness & gym management workflow (clients, progress logging, workouts, metrics analytics) along with:

* `pytest` unit/integration tests
* a `Dockerfile` for consistent execution
* GitHub Actions workflow for CI (syntax check, Docker build, tests inside the container)
* a `Jenkinsfile` for Jenkins-based clean build + quality gate

## API Overview

Base URL (when running locally): `http://localhost:5000`

* `GET /healthz` - health check
* `POST /api/clients` - create a client
* `GET /api/clients/<name>` - fetch a client
* `POST /api/clients/<name>/progress` - log weekly adherence
* `GET /api/clients/<name>/progress` - list adherence records
* `POST /api/clients/<name>/workouts` - log a workout
* `POST /api/clients/<name>/metrics` - log body metrics
* `GET /api/clients/<name>/analytics` - compute BMI + membership status + latest metrics
* `POST /api/clients/<name>/program` - generate a deterministic program plan

## Local Setup

1. Create and activate a virtual environment:

   * `python3 -m venv .venv`
   * `. .venv/bin/activate`

2. Install dependencies:

   * `pip install -r requirements.txt`

3. Run the Flask app:

   * `python3 app.py`
   * Open `http://localhost:5000/healthz`

The service uses a local sqlite database file by default: `aceest.db`.
For tests you can override `DB_PATH` via `create_app(...)` in code.

## Run Tests (Manual)

From the repository root:

* `python3 -m pytest -q`

## Docker

### Build image

* `docker build -t aceest:local .`

### Run the service

* `docker run --rm -p 5000:5000 aceest:local`

### Run tests inside the container

* `docker run --rm aceest:local python3 -m pytest -q`

## Jenkins Integration (Quality Gate)

`Jenkinsfile` performs a clean build and validation by:

1. Checking out the latest code from SCM (`checkout scm`)
2. Creating a fresh python virtual environment (`python3 -m venv .venv`)
3. Installing dependencies (`pip install -r requirements.txt`)
4. Running a syntax/compile gate (`python -m compileall -q .`)
5. Running tests (`python -m pytest -q`)

To configure Jenkins:

* Create a Jenkins Pipeline job pointing to your GitHub repository
* Ensure the job is set to use this `Jenkinsfile`

## GitHub Actions Integration (CI Pipeline)

Workflow file: `.github/workflows/main.yml`

It triggers on every `push` and `pull_request` and runs:

1. `build-lint`
   * Installs dependencies
   * Runs `python -m compileall -q .` to catch syntax errors
2. `docker-build-and-test`
   * Builds the Docker image (`docker build -t aceest:ci .`)
   * Executes `pytest -q` inside the built container (`docker run --rm aceest:ci python -m pytest -q`)
