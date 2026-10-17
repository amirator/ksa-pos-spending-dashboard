PY ?= python3
VENV := .venv
BIN := $(VENV)/bin

.PHONY: all setup data build test clean

all: setup build test          ## create venv, run the pipeline, run the tests

setup: $(BIN)/activate
$(BIN)/activate: requirements.txt
	$(PY) -m venv $(VENV)
	$(BIN)/pip install -q -r requirements.txt
	touch $(BIN)/activate

data: setup                    ## force a fresh download from the KAPSARC API
	$(BIN)/python -c "import sys; sys.path.insert(0,'src'); from pos_dashboard.download import download_all; download_all(force=True)"

build: setup                   ## download (if needed) -> SQL -> KPIs -> charts -> reports
	$(BIN)/python run.py

test: setup                    ## data-validation tests
	$(BIN)/python -m pytest -q

clean:                         ## remove generated outputs (keeps raw downloads)
	rm -rf data/processed/* reports/*.png reports/*.pdf reports/*.html reports/*.md reports/figures/*
