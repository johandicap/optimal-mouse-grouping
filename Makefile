###################################
# Optimal Mouse Grouping Makefile #
###################################

# Define Python files and folders to analyze
PYTHON_FILES_AND_FOLDERS = \
	mouse_grouping.py \
	optimal_mouse_grouping/mouse_grouping_cli.py \
	optimal_mouse_grouping/mouse_grouping_core.py \
	optimal_mouse_grouping/mouse_grouping_mip.py \
	optimal_mouse_grouping/mouse_grouping_utils.py \
	optimal_mouse_grouping/test/test_mouse_grouping_utils.py \
	optimal_mouse_grouping/test/integration_test.py

# Set Makefile shell to bash in order to print colored headers
SHELL := /bin/bash

# Function to print a colored header
COL=\033[1;35m
NC=\033[0m
define header
    @echo -e "${COL}$1${NC}"
endef

# List phony targets, i.e. targets that are not the name of a file
# See https://www.gnu.org/software/make/manual/html_node/Phony-Targets.html
.PHONY: ci ci_no_test style isort_check isort_fix mypy test

ci: ci_no_test test

ci_no_test: style isort_check mypy

style:
	$(call header,"[make style]")
	python3 -m pylama -o ./ci/pylama.ini $(PYTHON_FILES_AND_FOLDERS)

isort_check:
	$(call header,"[make isort_check]")
	isort --settings-path ./pyproject.toml --diff --color --check-only $(PYTHON_FILES_AND_FOLDERS)

isort_fix:
	$(call header,"[make isort_fix]")
	isort --settings-path ./pyproject.toml $(PYTHON_FILES_AND_FOLDERS)

mypy:
	$(call header,"[make mypy]")
	python3 -m mypy --config-file ./ci/mypy.ini $(PYTHON_FILES_AND_FOLDERS)

test:
	$(call header,"[make test]")
	python3 -m pytest --verbose optimal_mouse_grouping/test/
