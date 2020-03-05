# import os
import utils
import requests
from pathlib import Path


def test_url_true():
    url = 'http://gitea.avalon.konstru.evektor.cz/jverner/dochazka2/raw/branch/next/main.py'
    res = requests.get(url)
    assert res.ok is True


def test_url_false():
    url = 'http://non-existing.avalon.konstru.evektor.cz'
    res = requests.get(url)
    assert res.ok is False


def test_download_filepath_as_dir():
    url = 'http://gitea.avalon.konstru.evektor.cz/jverner/dochazka2/raw/branch/next/main.py'
    filename: Path = utils.download(url, Path('/tmp'))
    filename.unlink()
    assert filename == Path('/tmp/main.py')


def test_download_filepath_as_filename():
    url = 'http://gitea.avalon.konstru.evektor.cz/jverner/dochazka2/raw/branch/next/main.py'
    filename: Path = utils.download(url, Path('/tmp/result.py'))
    filename.unlink()
    assert filename == Path('/tmp/result.py')
