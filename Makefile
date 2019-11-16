PYTHON?=python

.PHONY: venv
venv:
	$(PYTHON) -m venv .venv
	source .venv/bin/activate && make setup
	@echo 'run `source .venv/bin/activate` to use virtualenv'

# The rest of these are intended to be run within the venv, where python points
# to whatever was used to set up the venv.

.PHONY: setup
setup:
	python -m pip install -Ur requirements-dev.txt

.PHONY: test
test:
	which python
	python -m coverage run -m imperfect.tests $(TESTOPTS)
	python -m coverage report --fail-under=90 --omit='.venv/*,.tox/*' --show-missing

.PHONY: fuzz
fuzz:
	python -m unittest imperfect.tests.imperfect_hypothesis

.PHONY: lint
lint:
	isort --recursive -y imperfect setup.py
	black imperfect setup.py
	flake8 imperfect

.PHONY: release
release:
	pip install -U wheel
	rm -rf dist
	python setup.py sdist bdist_wheel
	twine upload dist/*
