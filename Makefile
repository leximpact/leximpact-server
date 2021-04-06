#!/bin/bash

.PHONY: server

COLOR_CYAN='\033[0;36m'
COLOR_STOP='\033[0m'

uninstall:
	@# Uninstall all installed libraries of your current Python workspace.
	@# Handy when testing the instructions described in the README.md file.
	pip3 freeze | grep -v "^-e" | xargs pip3 uninstall -y

install:
	@# Install libraries as described in the requirements.txt file.
	pip3 install --upgrade pip
	pip3 install --editable .[dev] --upgrade

clean:
	find . -name '*.pyc' -exec rm \{\} \;

check-style:
	@# Do not analyse .gitignored files.
	@# `make` needs `$$` to output `$`. Ref: http://stackoverflow.com/questions/2382764.
	flake8 `git ls-files | grep "\.py$$"`

check-types:
	@# Do not analyse .gitignored files.
	@# `make` needs `$$` to output `$`. Ref: http://stackoverflow.com/questions/2382764.
	mypy `git ls-files | grep "\.py$$"`

format-style:
	@# Do not analyse .gitignored files.
	@# `make` needs `$$` to output `$`. Ref: http://stackoverflow.com/questions/2382764.
	autopep8 `git ls-files | grep "\.py$$"`
	black `git ls-files | grep "\.py$$"`

migrate:
	python3 repo/create_db.py
	alembic -x env=development upgrade head
	alembic -x env=test upgrade head

run:
	FLASK_ENV=development PORT=5000 python3 ./server/app.py

test: clean check-style check-types
	pytest
	@echo -e ${COLOR_CYAN}"Comparaison des calculs DGCL et LexImpact..."${COLOR_STOP}
	python3 ./tests/dotations/compare_with_dgcl.py

stress-server:
	./tests/server/stress/server.sh

stress-test:
	./tests/server/stress/benchmark.sh

simpop:
	python3 ./Simulation_engine/simulate_pop_from_reform.py

simpop_profile:
	python3 -m cProfile -o tests.cprof ./Simulation_engine/simulate_pop_from_reform.py

simpop_stats:
	python3 -c "import pstats; p = pstats.Stats('tests.cprof'); p.strip_dirs().sort_stats('tottime').print_stats(20)"

simpop_callers:
	python3 -c "import pstats; p = pstats.Stats('tests.cprof'); p.strip_dirs().sort_stats('tottime').print_callers(5)"

simpop_callees:
	python3 -c "import pstats; p = pstats.Stats('tests.cprof'); p.strip_dirs().sort_stats('tottime').print_callees(5)"

simpop_snakeviz:
	snakeviz tests.cprof
