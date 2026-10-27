PYTHON ?= backend/.venv/bin/python

.PHONY: backend frontend test test-backend test-frontend build docker-build docker-up docker-down

backend:
	$(PYTHON) backend/run.py

frontend:
	npm --prefix frontend run dev

test: test-backend test-frontend

test-backend:
	$(PYTHON) -m unittest discover -s backend/tests -v

test-frontend:
	npm --prefix frontend run typecheck
	npm --prefix frontend test

build:
	npm --prefix frontend run build

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down
