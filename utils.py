"""Python utils with functions."""

import os
import sys
import git
import shutil
import filecmp
import requests
# from collections import namedtuple
from dataclasses import dataclass
from pathlib import Path
from columnar import columnar
from colorama import Style, Fore
from autologging import logged, traced
from PyInquirer import style_from_dict, Token, prompt, Separator


# ===============================
# =           CLASSES           =
# ===============================
@dataclass
class Selected:
    repository: str = ''
    username: str = ''
    organization: str = ''


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


def lineno(msg: str=None):
    if not msg:
        return sys._getframe().f_back.f_lineno
    print(f"{sys._getframe().f_back.f_lineno: >4}.[ {BBla}DEBUG{RCol} ]: "
          f"{msg if msg is not None else ''}")


def requirements_similar(src_requirements: str, dst_requirements: str) -> bool:
    """Return True if both src_req and dst_req have the same content.

    Usage:
        >>> requirements_similar('/tmp/req1.txt', '/tmp/req_same.txt')
        True
        >>> requirements_similar('/tmp/req1.txt', '/tmp/req_different.txt')
        False
    """
    if type(src_requirements) == 'str':
        src_requirements: Path = Path(src_requirements)
    if type(dst_requirements) == 'str':
        dst_requirements: Path = Path(dst_requirements)

    if not src_requirements.exists() or not dst_requirements.exists():
        return False

    return filecmp.cmp(src_requirements, dst_requirements)


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

# def make_symbolic_link(src_filepath, dst_filepath):
#     if type(src_filepath) == 'str':
#         src_filepath = Path(src_filepath)
#     if type(dst_filepath) == 'str':
#         dst_filepath = Path(dst_filepath)

#     cmd = f'ssh {SKRIPTY_SERVER} "ln -fs {src_filepath} {dst_filepath}"'
#     lineno(f"cmd: '{cmd}'")
#     os.system(cmd)


def is_git_repo(path):
    """Return True if 'path' is git repository, False otherwise."""
    try:
        _ = git.Repo(path).git_dir
        return True
    except git.exc.InvalidGitRepositoryError:
        return False


def get_repo_list_as_table(session, server, repository):
    """Return columnar() table object with list of repositories using gitea api.

    Sorted by 'created' descending.

    Arguments:
        - session: requests.Session() object with updated headers with GITEA_TOKEN
        - server, repository ... used in url:
            - url = {server}/api/v1/repos/search?q={repository}&sort=created&order=desc

    Example:
        REPOSITORY      USER     DESCRIPTION

        dochazka2       jverner  Toto je testovaci dochazka, ktera bude... Casem smaz.
        CMM             ptinka   Tool to changing xml files
        eve-git2        C2       Updated version of eve-git working with Gitea
        alic_stats      ptinka   Staty pro alici
    """
    url: str = f"{server}/api/v1/repos/search?q={repository}&sort=created&order=desc"
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
    results = [
        [
            item['name'],
            item['owner']['login'],
            item['description']
        ]
        for item in data.get('data')]

    return columnar(results, tbl_headers, no_borders=True, wrap_max=0)


def select_repo_from_list(session, server, repository, question):
    """Make columnar() table selectable, return Selected('repository', 'username') object.

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
        Selected(repository='CMM', username='ptinka')
    """
    tbl = get_repo_list_as_table(session, server, repository)

    tbl_as_string = tbl.split('\n')
    table_header, table_body = tbl_as_string[1], tbl_as_string[3:-1]
    repo_list = [
        {'name': item, 'value': (item.split()[0], item.split()[1])}
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

    return Selected(*answers.get('selected'))


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

