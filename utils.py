"""Python utils with functions."""

import requests
from pathlib import Path
from colorama import Style, Fore


# ==============================
# =           COLORS           =
# ==============================
RCol = Style.RESET_ALL
Whi, BWhi = Fore.WHITE, f'{Fore.WHITE}{Style.BRIGHT}'


# =================================
# =           FUNCTIONS           =
# =================================
def download(url: str, filepath):
    """Docu."""
    if type(filepath) == 'str':
        filepath = Path(filepath)

    if filepath.is_dir():
        filepath = filepath / url.split('/')[-1]

    res = requests.get(url, allow_redirects=True)
    if not res.ok:
        return None

    with open(filepath, 'wb') as f:
        f.write(res.content)

    return filepath


def ask_with_defaults(question: str, defaults=''):
    """Return user input with optional default argument.

    Example:
        >>> ask_with_defaults("Are you happy?", "yes")
        Are you happy? [yes]: very
        'very'
    """
    user_input = input(f'{question} [{BWhi}{defaults}{RCol}]: ').strip()
    result = user_input if user_input else defaults
    return result
