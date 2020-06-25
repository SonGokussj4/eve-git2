# import os
import utls
import requests
import configparser
from pathlib import Path
from eve_git import cfg


def test_url_true():
    url = f"{cfg['server']['url']}/C2/ansarun/raw/branch/master/ansarun.sh"
    res = requests.get(url)
    assert res.ok is True


def test_url_false():
    url = f"{cfg['server']['url']}/C2/lalalulu"
    res = requests.get(url)
    assert res.ok is False


def test_download_filepath_as_dir():
    url = f"{cfg['server']['url']}/C2/ansarun/raw/branch/master/ansarun.sh"
    filename: Path = utls.download(url, Path('/tmp'))
    print(f">>> filename: {filename}")
    filename.unlink()
    assert filename == Path('/tmp/ansarun.sh')


def test_download_filepath_as_filename():
    url = f"{cfg['server']['url']}/C2/ansarun/raw/branch/master/ansarun.sh"
    filename: Path = utls.download(url, Path('/tmp/result.py'))
    filename.unlink()
    assert filename == Path('/tmp/result.py')
