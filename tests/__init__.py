"""Docu model"""
# Very good sources to read:
# https://www.linuxjournal.com/content/testing-your-code-pythons-pytest
# https://www.linuxjournal.com/content/testing-your-code-pythons-pytest-part-ii
# https://www.linuxjournal.com/content/python-testing-pytest-fixtures-and-coverage
from pathlib import Path

SCRIPTDIR = Path(__file__).resolve().parent
TEST_FILES = SCRIPTDIR / 'files'
