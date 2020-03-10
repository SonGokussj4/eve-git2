"""Python utils with functions."""

import os
import sys
import git
import shutil
import filecmp
import requests
from pathlib import Path
from colorama import Style, Fore
from autologging import logged, traced


# ==============================
# =           COLORS           =
# ==============================
RCol = Style.RESET_ALL
Whi, BWhi = Fore.WHITE, f'{Fore.WHITE}{Style.BRIGHT}'
Bla, BBla = Fore.BLACK, f'{Fore.BLACK}{Style.BRIGHT}'
Red, BRed = Fore.RED, f'{Fore.RED}{Style.BRIGHT}'


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


@traced
@logged
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


@traced
@logged
def remove_dir_tree(dirpath):
    """Remove selected directory. Linux/Windows compatible."""
    if dirpath == 'str':
        dirpath = Path(dirpath)
    if os.name != 'nt':  # Linux
        shutil.rmtree(dirpath)
    else:  # Windows
        os.system(f'rmdir /S /Q "{dirpath}"')
    return True


def lineno(msg=None):
    if not msg:
        return sys._getframe().f_back.f_lineno
    print(f"{sys._getframe().f_back.f_lineno: >4}.[ {BBla}DEBUG{RCol} ]: {msg if msg is not None else ''}")



def requirements_similar(src_requirements, dst_requirements):
    if type(src_requirements) == 'str':
        src_requirements = Path(src_requirements)
    if type(dst_requirements) == 'str':
        dst_requirements = Path(dst_requirements)

    if not src_requirements.exists() or not dst_requirements.exists():
        return False

    return filecmp.cmp(src_requirements, dst_requirements)


def check_user_repo_exist(SERVER: str, args):
    """Return True if both 'user' and combination 'user/repo' exists.

    Check:
        {SERVER}/api/v1/users/{args.username}
        {SERVER}/api/v1/repos/{args.username}/{args.repository}
    """
    # Does the username exist?
    res = args.session.get(f"{SERVER}/api/v1/users/{args.username}")
    if res.status_code != 200:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] User '{args.username}' doesn't exist!"
        raise Exception(msg)

    # Does the <repository> of <user> exist?
    res = args.session.get(f"{SERVER}/api/v1/repos/{args.username}/{args.repository}")
    if res.status_code != 200:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Repository '{SERVER}/{args.username}/{args.repository}' does not exist."
        raise Exception(msg)

    return True

# def make_symbolic_link(src_filepath, dst_filepath):
#     if type(src_filepath) == 'str':
#         src_filepath = Path(src_filepath)
#     if type(dst_filepath) == 'str':
#         dst_filepath = Path(dst_filepath)

#     cmd = f'ssh {SKRIPTY_SERVER} "ln -fs {src_filepath} {dst_filepath}"'
#     lineno(f"cmd: '{cmd}'")
#     os.system(cmd)


def is_git_repo(path):
    try:
        _ = git.Repo(path).git_dir
        return True
    except git.exc.InvalidGitRepositoryError:
        return False
