PYTHON ?= dashboard/.venv/bin/python

.PHONY: backend frontend test test-backend test-frontend build

backend:
	$(PYTHON) dashboard/run.py

frontend:
	npm --prefix dashboard/frontend run dev

test: test-backend test-frontend

test-backend:
	$(PYTHON) -m unittest discover -s dashboard/tests -v

test-frontend:
	npm --prefix dashboard/frontend run typecheck
	npm --prefix dashboard/frontend test

build:
	npm --prefix dashboard/frontend run build
