'''Python utils with functions.'''

from pathlib import Path
import requests


def download(url: str, filepath: Path):
    """Docu."""
    if filepath.is_dir():
        filepath = filepath / url.split('/')[-1]

    res = requests.get(url, allow_redirects=True)
    if not res.ok:
        return None

    with open(filepath, 'wb') as f:
        f.write(res.content)

    return filepath
