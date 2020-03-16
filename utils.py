"""Python utils with functions."""

import os
import sys
import git
import shutil
import filecmp
import requests
import configparser
# from collections import namedtuple
from dataclasses import dataclass
from pathlib import Path
from columnar import columnar
from colorama import Style, Fore
from types import SimpleNamespace
from autologging import logged, traced
from PyInquirer import style_from_dict, Token, prompt, Separator



# ==============================
# =           CONFIG           =
# ==============================
SCRIPTDIR = Path(__file__).resolve().parent
CURDIR = Path('.')
SETTINGS_DIRS = (SCRIPTDIR, Path.home(), CURDIR)
SETTINGS_FILENAME = 'eve-git.settings'
cfg = configparser.ConfigParser(allow_no_value=True)
cfg.read([folder / SETTINGS_FILENAME for folder in SETTINGS_DIRS])
DEBUG = cfg['app'].getboolean('debug')


# ===============================
# =           CLASSES           =
# ===============================
@dataclass
class Selected:
    repository: str = ''
    username: str = ''
    description: str = ''
    organization: str = ''


@dataclass
class SelectedFile:
    filename: str = ''
    filepath: str = ''


# ==============================
# =           COLORS           =
# ==============================
RCol = Style.RESET_ALL

Red, BRed = Fore.RED, f'{Fore.RED}{Style.BRIGHT}'
Whi, BWhi = Fore.WHITE, f'{Fore.WHITE}{Style.BRIGHT}'
Bla, BBla = Fore.BLACK, f'{Fore.BLACK}{Style.BRIGHT}'
Yel, BYel = Fore.YELLOW, f'{Fore.YELLOW}{Style.BRIGHT}'
QSTYLE = style_from_dict({
    Token.Separator: '#686868 bold',
    Token.QuestionMark: '#686868 bold',
    Token.Selected: '#cc5454',
    Token.Pointer: '#54FF54 bold',
    # Token.Instruction: '#E8CB26',
    # Token.Answer: '#F3F3F3 bold',
    Token.Answer: '#ffffff',
    # Token.Question: '#8C8C8C',
})


# ===============================
# =           CLASSES           =
# ===============================
class NestedNamespace(SimpleNamespace):
    """conf = NestedNamespace({'key': 'val', 'section': {'use': 'True'}})."""

    def __init__(self, dictionary, **kwargs):
        super().__init__(**kwargs)
        for key, value in dictionary.items():
            if isinstance(value, dict):
                self.__setattr__(key, NestedNamespace(value))
            else:
                self.__setattr__(key, value)


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


# @traced
# @logged
# def ask_with_defaults(question: str, defaults=''):
#     """Return user input with optional default argument.

#     Example:
#         >>> ask_with_defaults("Are you happy?", "yes")
#         Are you happy? [yes]: very
#         'very'
#     """
#     user_input = input(f'{question} [{BWhi}{defaults}{RCol}]: ').strip()
#     result = user_input if user_input else defaults
#     return result


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


@traced
@logged
def lineno(msg: str=None):
    if not msg:
        return sys._getframe().f_back.f_lineno
    if not DEBUG:
        return
    print(f"{sys._getframe().f_back.f_lineno: >4}.[ {BBla}DEBUG{RCol} ]: "
          f"{msg if msg is not None else ''}")


@traced
@logged
def requirements_similar(src_requirements: any, dst_requirements: any) -> bool:
    """Return True if both src_req and dst_req have the same content.
    Arguments:
        src_requirements [Path or str]: First file to compare
        dst_requirements [Path or str]: Second file to compare

    Usage:
        >>> requirements_similar('/tmp/req1.txt', '/tmp/req_same.txt')
        True
        >>> requirements_similar(Path('/tmp/req1.txt'), '/tmp/req_different.txt')
        False
    """
    src_requirements = Path(src_requirements)
    dst_requirements = Path(dst_requirements)

    if not src_requirements.exists() or not dst_requirements.exists():
        return False

    return filecmp.cmp(src_requirements, dst_requirements)


@traced
@logged
def lsremote(url):
    """Get references ('HEAD', 'refs/heads/<branch>') from remote <url> repo."""
    remote_refs = {}
    g = git.cmd.Git()
    for ref in g.ls_remote(url).split('\n'):
        hash_ref_list = ref.split('\t')
        remote_refs[hash_ref_list[1]] = hash_ref_list[0]
    return remote_refs


@traced
@logged
def list_remote_branches(url: str) -> list:
    """Return list of branches from remote repository."""
    # GITEA API: /repos/{owner}/{repo}/branches
    refs = lsremote(url)
    branches = []
    for key, val in refs.items():
        if '/' not in key:
            continue
        branches.append(key.replace('refs/heads/', ''))
    return branches


@traced
@logged
def remote_repo_branch_exist(url: str, branch: str) -> bool:
    """Return True if <branch> of remote <url> repository exists."""
    refs = lsremote(url)
    ref = refs.get(f'refs/heads/{branch}', None)
    if ref:
        return True
    return False


@traced
@logged
def check_user_repo_exist(server: str, repository: str, username: str, session) -> bool:
    """Return True if both 'user' and combination gitea 'user/repo' exists.

    Check:
        {server}/api/v1/users/{username}
        {server}/api/v1/repos/{username}/{repository}
    Usage:
        >>> check_user_repo_exist('nexus', 'planet_name', 'goku', <session>)
        True
    """
    # Does the username exist?
    res = session.get(f"{server}/api/v1/users/{username}")
    if res.status_code != 200:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] User '{username}' doesn't exist!"
        raise Exception(msg)

    # Does the <repository> of <user> exist?
    res = session.get(f"{server}/api/v1/repos/{username}/{repository}")
    if res.status_code != 200:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Repository '{server}/{username}/{repository}' does not exist."
        raise Exception(msg)

    return True


@traced
@logged
def check_org_exist(server: str, organization: str, session) -> bool:
    """Return True if gitea 'organization' exists.

    Arguments:
        - server: server address
        - organization: gitea org
        - session: requests.Session() object with updated headers with GITEA_TOKEN

    Check:
        {server}/api/v1/orgs/{organization}

    Usage:
        >>> check_org_exist('nexus', 'universe', <session>)
        True
    """
    url = f"{server}/api/v1/orgs/{organization}"
    lineno(f"url: {url}")

    res = session.get(url)
    lineno(f"res.status_code: {res.status_code}")

    # Case org does not exist
    if res.status_code == 404:
        print(f"{lineno(): >4}.[ {Yel}WARNING{RCol} ] Organization '{organization}' not found...")
        return False

    elif res.status_code != 200:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Unknown error for organization: '{organization}'"
        raise Exception(msg)

    return True


@traced
@logged
def make_symbolic_link(src_filepath: str, dst_filepath: str, remote_server: str = ''):
    if type(src_filepath) == 'str':
        src_filepath = Path(src_filepath)
    if type(dst_filepath) == 'str':
        dst_filepath = Path(dst_filepath)

    if os.name != 'nt':
        cmd = f'ssh {remote_server} "ln -fs {src_filepath} {dst_filepath}"'
    else:
        cmd = f'cmd /c "mklink {dst_filepath} {src_filepath}"'
        # powershell
        # cmd = f'''powershell.exe new-item -ItemType SymbolicLink -path {SKRIPTY_EXE} -name {val} -value {link_src}'''
    lineno(f"cmd: '{cmd}'")
    os.system(cmd)
    return True


@traced
@logged
def is_git_repo(path: any) -> bool:
    """Return True if 'path' is git repository, False otherwise."""
    try:
        _ = git.Repo(path).git_dir
        return True
    except git.exc.InvalidGitRepositoryError:
        return False


def get_files_as_table(directory: Path, hmmmm=None):
    """Docs."""
    data = [(item.name, item.resolve(), item) for item in directory.iterdir() if item.is_file()]
    lineno(f"data: {data}")

    tbl_headers = ('filename', 'path')
    results = [
        [
            item[0],
            item[1],
        ]
        for item in data]

    return columnar(results, tbl_headers, no_borders=True, wrap_max=0)


def select_files_from_list(directory: Path, hmmmm: bool = None, question: str = '') -> SelectedFile:
    """Make columnar() table selectable, return Selected().
    """
    tbl = get_files_as_table(directory, hmmmm)
    tbl_as_string = tbl.split('\n')
    table_header, table_body = tbl_as_string[1], tbl_as_string[3:-1]
    # PyInquirer BUG - when selecting by mouse, it's ignoring 'value'
    # repo_list = [
    #     {'name': item, 'value': [val.strip() for val in item.split(maxsplit=2)]}
    #     for item in table_body
    # ]
    ls = [
        {
            'name': item
        }
        for item in table_body
    ]
    choices = [Separator(f"\n   {table_header}\n")]
    choices.extend(ls)
    choices.append(Separator('\n'))

    questions = [{
        'message': question,
        'name': 'selected',
        'type': 'list',
        'choices': choices,
        'pageSize': 50,
    }]

    answers = prompt(questions, style=QSTYLE)

    if not answers:
        raise SystemExit
    answers = [val.strip() for val in answers.get('selected').split()]
    lineno(f"answers: {answers}")

    selected = SelectedFile()
    selected.filename = answers[0]
    selected.filepath = Path(answers[1])

    return selected


@traced
@logged
def get_repo_list_as_table(session: requests.Session(), server: str,
                           repository: str, username: str='') -> columnar:
    """Return columnar() table object with list of repositories using gitea api.

    Sorted by: 'created' descending.
    Limit: 50 items

    Arguments:
        - session: requests.Session() object with updated headers with GITEA_TOKEN
        - server, repository ... used in url:
            - url = {server}/api/v1/repos/search?q={repository}&sort=created&order=desc
        - Optional 'username', when entered, filter through 'USER' column

    Example:
        REPOSITORY      USER     DESCRIPTION

        dochazka2       jverner  Toto je testovaci dochazka, ktera bude... Casem smaz.
        CMM             ptinka   Tool to changing xml files
        eve-git2        C2       Updated version of eve-git working with Gitea
        alic_stats      ptinka   Staty pro alici
    """
    url: str = f"{server}/api/v1/repos/search?q={repository}&sort=created&order=desc&limit=50"
    data = session.get(url).json()
    lineno(f"data.get('ok'): {data.get('ok')}")

    # Check if there was a good response
    if not data.get('ok'):
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Shit... Data not acquired... {data}"
        raise Exception(msg)

    if not data.get('data'):
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Search for repository '{repository}' returned 0 results... Try something different."
        raise Exception(msg)

    # Data acquired, list all found repos in nice table
    tbl_headers = ('repository', 'user', 'description')

    results = []
    if username:
        results = [
            [
                item['name'],
                item['owner']['login'],
                item['description']
            ]
            for item in data.get('data')
            if username.lower() in item['owner']['login'].lower()]

        if len(results) == 0:
            print(f"[ {Yel}WARNING{RCol} ] No repository with += username: '{username}' found. "
                  f"Listing for all users.")

    if len(results) == 0 or not username:
        results = [
            [
                item['name'],
                item['owner']['login'],
                item['description']
            ]
            for item in data.get('data')]

    return columnar(results, tbl_headers, no_borders=True, wrap_max=0)


@traced
@logged
def select_repo_from_list(session: str, server: str, repository: str,
                          username: str = '', question: str = '') -> Selected:
    """Make columnar() table selectable, return Selected().

    Return:
        - Selected('repository', 'username', 'description') object.

    Arguments:
        - session: requests.Session() object with updated headers with GITEA_TOKEN
        - server, repository used in get_repo_list_as_table()
        - question: what will be the user asked, see example bellow

    Example:
    ? Select repo to connect to:    (User arrow keys)

        REPOSITORY      USER     DESCRIPTION

        dochazka2       jverner  Toto je testovaci dochazka, ktera bude... Casem smaz.
    >   CMM             ptinka   Tool to changing xml files
        eve-git2        C2       Updated version of eve-git working with Gitea
        alic_stats      ptinka   Staty pro alici

        >>> <enter>
        Selected(repository='CMM', username='ptinka', description='Tool to ...')
    """
    tbl = get_repo_list_as_table(session, server, repository, username)

    tbl_as_string = tbl.split('\n')
    table_header, table_body = tbl_as_string[1], tbl_as_string[3:-1]
    # PyInquirer BUG - when selecting by mouse, it's ignoring 'value'
    # repo_list = [
    #     {'name': item, 'value': [val.strip() for val in item.split(maxsplit=2)]}
    #     for item in table_body
    # ]
    repo_list = [
        {
            'name': item
        }
        for item in table_body
    ]
    choices = [Separator(f"\n   {table_header}\n")]
    choices.extend(repo_list)
    choices.append(Separator('\n'))

    questions = [{
        'message': question,
        'name': 'selected',
        'type': 'list',
        'choices': choices,
        'pageSize': 50,
    }]

    answers = prompt(questions, style=QSTYLE)

    if not answers:
        raise SystemExit
    answers = [val.strip() for val in answers.get('selected').split(maxsplit=2)]
    lineno(f"answers: {answers}")

    return Selected(*answers)


@traced
@logged
def get_org_list_as_table(session, server):
    """Return columnar() table object with list of organizations using gitea api.

    Admin GITEA_TOKEN needed!!!

    Sorted by 'name' ascending.

    Arguments:
        - session: requests.Session() object with updated headers with GITEA_TOKEN
        - server, ... used in url:
            - url = {server}/api/v1/admin/orgs

    Example:
        ORGANIZATION  NUM REPOS  DESCRIPTION

        C1            1
        C2            4
        P135          4
    """
    url = f"{server}/api/v1/admin/orgs"
    lineno(f"url: '{url}'")

    res = session.get(url)
    if res.status_code == 403:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Forbidden. You don't have enough access rights..."
        raise Exception(msg)

    elif res.status_code == 404:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] 404 - url page not found: '{url}'"
        raise Exception(msg)

    elif res.status_code == 401:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] 401 - Wrong GITEA_TOKEN or some other problem"
        raise Exception(msg)

    if res.status_code != 200:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Unknown error. Status Code: {res.status_code}"
        raise Exception(msg)

    lineno(f"All ok. Here is the list.")
    data = res.json()

    # Data acquired, list all found repos in nice table
    headers = ('Organization', 'Num Repos', 'description')
    results = [
        [
            item['username'],
            len(session.get(f"{server}/api/v1/orgs/{item['username']}/repos").json()),
            item['description']
        ]
        for item in data]

    return columnar(results, headers, no_borders=True)


@traced
@logged
def select_org_from_list(session, server, question):
    """Make columnar() table selectable, return Selected('organization') object.

    Arguments:
        - session: requests.Session() object with updated headers with GITEA_TOKEN
        - server, repository used in get_org_list_as_table()
        - question: what will be the user asked, see example bellow

    Example:
    ? Select organization to remove:    (User arrow keys)

        ORGANIZATION  NUM REPOS  DESCRIPTION

        C1            1
    >   C2            4
        P135          4

        >>> <enter>
        Selected(organization='C2')
    """
    tbl = get_org_list_as_table(session, server)

    tbl_as_string = tbl.split('\n')
    table_header, table_body = tbl_as_string[1], tbl_as_string[3:-1]
    repo_list = [
        {'name': item, 'value': item.split()[0]}
        for item in table_body
    ]

    choices = [Separator(f"\n   {table_header}\n")]
    choices.extend(repo_list)
    choices.append(Separator('\n'))

    questions = [{
        'message': question,
        'name': 'selected',
        'type': 'list',
        'choices': choices,
        'pageSize': 50,
    }]

    answers = prompt(questions, style=QSTYLE)
    if not answers:
        raise SystemExit
    lineno(f"answers: {answers}")

    selected = Selected()
    selected.organization = answers.get('selected')
    return selected


@traced
@logged
def ask_confirm(msg):
    questions = [
        {
            'message': msg,
            'name': 'continue',
            'type': 'confirm',
        }
    ]
    answers = prompt(questions, style=QSTYLE)

    if not answers:
        raise SystemExit

    lineno(f"answers: {answers}")

    if not answers.get('continue'):
        raise SystemExit(f"[ INFO ] Aborting...")

    return True


@traced
@logged
def ask_confirm_data(msg, comp_str):
    questions = [
        {
            'message': msg,
            'name': 'result',
            'type': 'input',
        }
    ]
    answers = prompt(questions, style=QSTYLE)

    if not answers:
        raise SystemExit

    lineno(f"answers: {answers}")

    if not answers.get('result'):
        raise SystemExit(f"[ INFO ] Aborting...")

    answer = answers.get('result')
    if not answer == comp_str:
        msg = (f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] "
               f"Entered orgname '{answer}' is not the same as '{comp_str}'. Aborting...")
        raise Exception(msg)

    return True


@traced
@logged
def ask_confirm_from_list(msg, comp_str):
    questions = [
        {
            'message': msg,
            'name': 'result',
            'type': 'input',
        }
    ]
    answers = prompt(questions, style=QSTYLE)

    if not answers:
        raise SystemExit

    lineno(f"answers: {answers}")

    if not answers.get('result'):
        raise SystemExit(f"[ INFO ] Aborting...")

    answer = answers.get('result')
    if not answer == comp_str:
        msg = (f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] "
               f"Entered orgname '{answer}' is not the same as '{comp_str}'. Aborting...")
        raise Exception(msg)

    return True
