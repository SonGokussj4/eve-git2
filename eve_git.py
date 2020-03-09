#!/usr/bin/env python
"""<DESCRIPTION OF THE PROGRAM>"""

# TODO: Prepracovat toto vsechno (dlouhodoby TODO) do Classy...
# TODO: dodelat cli: --undeploy, kde to vycisti system

# =================================
# =           LIBRARIES           =
# =================================
# System Libs
#=============
import os
import sys
import json
# import shlex
import shutil
import getpass
import logging
import fileinput
import configparser
# import subprocess as sp
from pathlib import Path
# from dataclasses import dataclass

# Pip Libs
#==========
# from profilehooks import profile, timecall, coverage
# import click  # https://pypi.org/project/click/
import requests
from git import Repo, exc  # https://gitpython.readthedocs.io/en/stable/tutorial.html#tutorial-label
from columnar import columnar  # https://pypi.org/project/Columnar/
from colorama import init, Fore, Back, Style
from PyInquirer import style_from_dict, Token, prompt, Separator  # https://pypi.org/project/PyInquirer/
# from PyInquirer import Validator, ValidationError
from autologging import logged, TRACE, traced  # https://pypi.org/project/Autologging/
# Fore: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
# Back: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
# Style: DIM, NORMAL, BRIGHT, RESET_ALL

# User Libs
#===========
import cli
from utils import *


# ==============================
# =           COLORS           =
# ==============================
RCol = Style.RESET_ALL
Red, BRed = Fore.RED, f'{Fore.RED}{Style.BRIGHT}'
Blu, BBlu = Fore.BLUE, f'{Fore.BLUE}{Style.BRIGHT}'
Gre, BGre = Fore.GREEN, f'{Fore.GREEN}{Style.BRIGHT}'
Bla, BBla = Fore.BLACK, f'{Fore.BLACK}{Style.BRIGHT}'
Whi, BWhi = Fore.WHITE, f'{Fore.WHITE}{Style.BRIGHT}'
Yel, BYel = Fore.YELLOW, f'{Fore.YELLOW}{Style.BRIGHT}'


# You have to run this script with python >= 3.7
if sys.version_info.major != 3:
    print(f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Hell NO! You're using Python2!! That's not cool man...")
    sys.exit()
if sys.version_info.minor <= 6:
    print(f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Nah... Your Python version have to be at least 3.7. Sorry")
    sys.exit()


# =================================
# =           CONSTANTS           =
# =================================
SCRIPTDIR = Path(__file__).resolve().parent
CURDIR = Path('.')
SETTINGS_DIRS = (SCRIPTDIR, Path.home(), CURDIR)
SETTINGS_FILENAME = 'eve-git.settings'


# ==============================
# =           CONFIG           =
# ==============================
cfg = configparser.ConfigParser(allow_no_value=True)
cfg.read([folder / SETTINGS_FILENAME for folder in SETTINGS_DIRS])

SERVER = cfg['server']['url']
GITEA_TOKEN = cfg['server'].get('gitea_token', '')
SKRIPTY_DIR = Path(cfg['server']['skripty_dir'])
SKRIPTY_EXE = Path(cfg['server']['skripty_exe'])
SKRIPTY_SERVER = cfg['server']['skripty_server']
LD_LIB_PATH = cfg['server']['ld_lib']
DEBUG = cfg['app'].getboolean('debug')
# Style for PyInquirer
QSTYLE = style_from_dict({
    Token.Separator: '#686868 bold',
    Token.QuestionMark: '#686868 bold',
    Token.Selected: '#cc5454 bold',
    Token.Pointer: '#54FF54 bold',
    # Token.Instruction: '#E8CB26',
    # Token.Answer: '#F3F3F3 bold',
    Token.Answer: '#ffffff',
    # Token.Question: '#8C8C8C',
})


# ====================================================
# =           Exceptions without Traceback           =
# ====================================================
# def excepthook(type, value, traceback):
#     print(value)


# if not DEBUG:
#     sys.excepthook = excepthook


# ===============================
# =           CLASSES           =
# ===============================
from progress import Progress


# =================================
# =           FUNCTIONS           =
# =================================


def init_logging(args):
    log_level = logging.WARNING
    if args.v:
        if args.v == 1:
            log_level = logging.INFO
        elif args.v == 2:
            log_level = logging.DEBUG
        else:
            log_level = TRACE

    logging.basicConfig(
        level=log_level, stream=sys.stderr,
        # format="[ %(levelname)s ] :%(filename)s,%(lineno)d:%(name)s.%(funcName)s:%(message)s")
        format="[ %(levelname)s ] %(funcName)s: %(message)s")


def init_session(args):
    session = requests.Session()

    session.headers.update({
        'accept': 'application/json',
        'content-type': 'application/json',
        'Authorization': f'token {GITEA_TOKEN}',
    })
    return session




@traced
@logged
def deploy(args):
    print(f"[ {BWhi}INFO{RCol}  ] Deploying...")

    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] args.repository: {args.repository}")
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] args.username: {args.username}")
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] args.branch: {args.branch}")

    # ==================================================
    # =           CHECK IF <username> EXISTS           =
    # ==================================================
    # Does the username exist?
    res = args.session.get(f"{SERVER}/api/v1/users/{args.username}")
    if res.status_code != 200:
        raise Exception(f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] User '{args.username}' doesn't exist!")
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] Checking if <username> exists: {res.ok}")
    # lineno(f"Checking if <username> exists: {res.ok}")

    # ================================================================
    # =           CHECK FOR <repository> AND <user> EXISTS           =
    # ================================================================
    # Does the <repository> of <user> exist?
    res = args.session.get(f"{SERVER}/api/v1/repos/{args.username}/{args.repository}")
    if res.status_code != 200:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Repository '{SERVER}/{args.username}/{args.repository}' does not exist."
        raise Exception(msg)
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] Checking if <username>/<repository> exists: {res.ok}")

    # Local and Remove directory
    tmp_dir = Path('/tmp') / args.repository
    target_dir = SKRIPTY_DIR / args.repository

    # ================================================================
    # =           REMOVE EXISTING /tmp/{repository} FOLDER           =
    # ================================================================
    if tmp_dir.exists():
        print(f"[ {Yel}WARNING{RCol} ] '{tmp_dir}' already exists. Removing.")
        removed = remove_dir_tree(tmp_dir)
        print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] removed: {removed}")

    # ================================================
    # =           CLONE GIT REPO INTO /tmp           =
    # ================================================
    print(f"[ {BWhi}INFO{RCol}  ] Clonning to '{tmp_dir}' DONE")

    url = f"{SERVER}/{args.username}/{args.repository}"
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] Clonning url: {url}")

    Repo.clone_from(url=url, to_path=tmp_dir, branch=args.branch, depth=1, progress=Progress())

    # ==========================================
    # =           REMOVE .GIT FOLDER           =
    # ==========================================
    print(f"[ {BWhi}INFO{RCol} ] Removing '.git' folder")
    git_folder = tmp_dir / '.git'
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] Removing '{git_folder}'")
    res = remove_dir_tree(git_folder)

    # ========================================
    # =           LOAD REPO.CONFIG           =
    # ========================================
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] Checking 'repo.config'")
    repo_cfg_filepath = tmp_dir / 'repo.config'

    if repo_cfg_filepath.exists():
        print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] '{repo_cfg_filepath}' found. Loading config.")
        repo_cfg = configparser.ConfigParser(allow_no_value=True)
        repo_cfg.read(repo_cfg_filepath)

        # =============================================
        # =           MAKE FILES EXECUTABLE           =
        # =============================================
        print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] Changing permissions for all files in '{tmp_dir}' to 664")
        for item in tmp_dir.iterdir():
            item: Path
            if not item.is_file():
                continue
            os.chmod(item, 0o664)

        for key, val in repo_cfg.items('Executable'):
            exe_file = tmp_dir / key
            if not exe_file.exists():
                print(f"[ WARNING ] file '{exe_file}' does not exist. Check your config in 'repo.config'.")
                continue
            print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] Making '{exe_file}' executable... Permissions: 774")
            os.chmod(exe_file, 0o774)

        # ================================================================================
        # =           CHECK IF REQUIREMENTS.TXT / REPO.CONFIG ARE DIFFERENT           =
        # ================================================================================
        src_requirements = tmp_dir / 'requirements.txt'
        print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] src_requirements: {src_requirements}")
        dst_requirements = target_dir / 'requirements.txt'
        print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] dst_requirements: {dst_requirements}")
        ignore_venv = requirements_similar(src_requirements, dst_requirements)
        print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] ignore_venv: {ignore_venv}")

        # ==================================================
        # =           CREATE VIRTUAL ENVIRONMENT           =
        # ==================================================
        if not ignore_venv:
            framework = repo_cfg['Repo']['Framework']
            print(f"[ {BWhi}INFO{RCol}  ] Making virtual environment...")
            cmd = f'{framework} -m venv {tmp_dir}/.env'
            print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] cmd: '{cmd}'")
            os.system(cmd)

            # ===================================
            # =           UPGRADE PIP           =
            # ===================================
            print(f"[ {BWhi}INFO{RCol}  ] Upgrading Pip")
            cmd = f'{tmp_dir}/.env/bin/pip install --upgrade pip'
            print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] cmd: '{cmd}'")
            os.system(cmd)

            # ===================================
            # =           PIP INSTALL           =
            # ===================================
            print(f"[ {BWhi}INFO{RCol}  ] Running Pip install")
            cmd = f'{tmp_dir}/.env/bin/pip install -r {tmp_dir}/requirements.txt'
            print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] cmd: '{cmd}'")
            os.system(cmd)

        # ==================================================
        # =           CHANGE VENV PATHS with SED           =
        # ==================================================
        print(f"[ {BWhi}INFO{RCol}  ] Changing venv paths '{tmp_dir}/.env' --> '{target_dir}/.env'")
        cmd = f'find {tmp_dir} -exec sed -i s@{tmp_dir}/.env@{target_dir}/.env@g {{}} \\; 2>/dev/null'
        print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] cmd: '{cmd}'")
        os.system(cmd)

        # ===================================================
        # =           REPLACE MAIN_FILE IN run.sh           =
        # ===================================================
        runsh_file = tmp_dir / 'run.sh'
        print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] runsh_file: '{runsh_file}'")
        main_file = repo_cfg['venv']['main_file']
        print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] main_file: '{main_file}'")

        print(f"[ {BWhi}INFO{RCol}  ] Replacing 'MAIN_FILE_PLACEHOLDER' --> '{main_file}' within '{runsh_file}'")
        with fileinput.FileInput(runsh_file, inplace=True) as f:
            for line in f:
                print(line.replace('MAIN_FILE_PLACEHOLDER', main_file), end='')

        # =====================================================
        # =           CREATE REMOTE reponame FOLDER           =
        # =====================================================
        # Check if <reponame> already exists in /expSW/SOFTWARE/skripty/<reponame>
        if not target_dir.exists():
            cmd = f'ssh {SKRIPTY_SERVER} "mkdir {target_dir}"'
            os.system(cmd)
            print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] {target_dir} created.")

        # =============================================
        # =           MAKE SYMBOLIC LINK(S)           =
        # =============================================
        for key, val in repo_cfg.items('Link'):
            src_filepath = target_dir / key
            dst_filepath = SKRIPTY_EXE / val
            print(f"[ {BWhi}INFO{RCol}  ] Linking '{src_filepath}' --> '{dst_filepath}'")
            # make_symbolic_link(src_filepath, dst_filepath)
            if os.name != 'nt':
                cmd = f'ssh {SKRIPTY_SERVER} "ln -fs {src_filepath} {dst_filepath}"'
            else:
                cmd = f'cmd /c "mklink {link_dst} {link_src}"'
                # cmd = f'''powershell.exe new-item -ItemType SymbolicLink -path {SKRIPTY_EXE} -name {val} -value {link_src}'''  # powershell
            print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] cmd: '{cmd}'")
            os.system(cmd)

    else:
        print(f"[ {BWhi}INFO{RCol}  ] '{repo_cfg_filepath}' not found... Ignoring making executables, symlinks, ...")
        print(f"[ {BWhi}INFO{RCol}  ] To create a repo.config.template, use 'eve-git template repo.config'")

    # ==========================================
    # =           RSYNC ALL THE DATA           =
    # ==========================================
    # Rsync all the data
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] ignore_venv: '{ignore_venv}'")
    # Case venv was created, copy all the data, even venv, because something was updated
    if not ignore_venv:
        cmd = f'rsync -ah --delete {tmp_dir} {SKRIPTY_SERVER}:{target_dir.parent}'
    # Case venv wasn't created locally, ignore venv folders so that they will not be deleted in target_dir
    else:
        cmd = (f'rsync -ah --delete --exclude-from={SCRIPTDIR}/rsync-directory-exclusions.txt '
               f'{tmp_dir} {SKRIPTY_SERVER}:{target_dir.parent}')
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] Rsync cmd: '{cmd}'")
    os.system(cmd)

    # ===============================
    # =           CLEANUP           =
    # ===============================
    remove_dir_tree(tmp_dir)
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] '{tmp_dir}' removed")

    print(f"[ {BWhi}INFO{RCol}  ] Deployment completed.")
    return 0


@traced
@logged
def create_org(args):
    """Function Description."""
    questions = [
        {
            'message': f"Organization name:",
            'default': args.organization,
            'name': 'organization',
            'type': 'input',
            'validate': lambda answer: "Cannot be empty."
            if not answer else True
        },
        {
            'message': "Description:",
            'default': args.description,
            'name': 'description',
            'type': 'input',
            'validate': lambda answer: "Cannot be empty."
            if not answer else True
        },
        {
            'message': "Full Name:",
            'default': args.fullname,
            'name': 'fullname',
            'type': 'input',
        },
        {
            'message': "Visibility (public|private):",
            'default': args.visibility,
            'name': 'visibility',
            'type': 'input',
            'validate': lambda answer: "Wrong choice. Choose from 'public' or 'private'."
            if answer not in ['public', 'private'] else True
        },
    ]

    answers = prompt(questions, style=QSTYLE)
    if len(answers) == 0:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] No answers... Exitting."
        raise Exception(msg)

    args.organization = answers.get('organization')
    args.description = answers.get('description')
    args.fullname = answers.get('fullname')
    args.visibility = answers.get('visibility')

    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] args.reponame: {args.organization}")
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] args.description: {args.description}")
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] args.fullname: {args.fullname}")
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] args.visibility: {args.visibility}")

    # Construct Headers and Data
    repo_headers = {
        'accept': 'application/json',
        'content-type': 'application/json',
        'Authorization': f'token {GITEA_TOKEN}'
    }
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] repo_headers: {repo_headers}")

    repo_data = {
        "description": args.description,
        "full_name": args.fullname,
        "repo_admin_change_team_access": True,
        "username": args.organization,  # THIS is Organization name
        "visibility": args.visibility,
    }
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] repo_data: {repo_data}")

    # Create organization
    res = requests.post(url=f"{SERVER}/api/v1/orgs", headers=repo_headers, json=repo_data)
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] res: {res}")

    # Viable responses
    if res.status_code == 401:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Something went wrong. Check your GITEA_TOKEN or internet connection."
        raise Exception(msg)

    elif res.status_code == 422:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Repository '{args.organization}' with the same name already exists."
        raise Exception(msg)

    elif res.status_code == 422:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Validation Error... Can't create repository with this name. Details bellow."
        msg += f"\n{lineno(): >4}.[ {BRed}ERROR{RCol} ] {json.loads(res.content)}"
        raise Exception(msg)

    elif res.status_code != 201:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Unknown error when trying to create new organization. Status_code: {res.status_code}"
        raise Exception(msg)

    print(f"[ {BGre}INFO{RCol} ] Done. Organization created.")

    return 0


@traced
@logged
def create_repo(args):
    # args.reponame = ask_with_defaults('Repository name', defaults=args.reponame)
    # args.description = ask_with_defaults('Description', defaults=args.description)

    questions = [
        {
            'message': "Repository name:",
            'default': args.reponame,
            'name': 'reponame',
            'type': 'input',
            'validate': lambda answer: "Cannot be empty."
            if not answer else True
        },
        {
            'message': "Description:",
            'default': args.description,
            'name': 'description',
            'type': 'input',
            'validate': lambda answer: "Cannot be empty."
            if not answer else True
        },
        {
            'message': "User/Org:",
            'default': args.username,
            'name': 'username',
            'type': 'input',
            'validate': lambda answer: "Cannot be empty."
            if not answer else True
        },
    ]

    answers = prompt(questions, style=QSTYLE)

    args.reponame = answers.get('reponame')
    args.description = answers.get('description')
    args.username = answers.get('username')

    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] args.reponame: {args.reponame}")
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] args.description: {args.description}")
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] args.username: {args.username}")

    # Try to create the repo
    repo_headers = {
        'accept': 'application/json',
        'content-type': 'application/json',
        'Authorization': f'token {GITEA_TOKEN}'
    }
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] repo_headers: {repo_headers}")

    repo_data = {
        'auto_init': True,
        'name': args.reponame,
        'readme': 'Default',
        'description': args.description,
        # 'gitignores': 'Evektor',
        'private': False
    }
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] repo_data: {repo_data}")

    # User specified different user/org. Only users with admin right can create repos anywhere
    url = f"{SERVER}/api/v1/user/repos"
    if args.username != getpass.getuser():
        print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] args.username: {args.username}")
        url = f"{SERVER}/api/v1/admin/users/{args.username}/repos"
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] url: {url}")

    # Post the repo
    res = requests.post(url=url, headers=repo_headers, json=repo_data)
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] res: {res}")

    # Viable responses
    if res.status_code == 409:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Repository '{args.reponame}' under '{args.username}' already exists."
        raise Exception(msg)

    elif res.status_code == 401:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Unauthorized... Something wrong with you GITEA_TOKEN..."
        raise Exception(msg)

    elif res.status_code == 422:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Validation Error... Can't create repository with this name. Details bellow."
        msg += f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] {json.loads(res.content)}"
        raise Exception(msg)

    elif res.status_code != 201:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Something went wrong. Don't know what. Status_code: {res.status_code}"
        raise Exception(msg)

    print(f"[ {BWhi}INFO{RCol} ] Repository created.")

    answer = input("Clone into current folder? [Y/n]: ")
    if answer.lower() in ['y', 'yes']:
        Repo.clone_from(url=f"{SERVER}/{args.username}/{args.reponame}",
                        to_path=Path(CURDIR.resolve() / args.reponame).resolve(),
                        branch='master',
                        progress=Progress())

    print(f"[ {BWhi}INFO{RCol} ] DONE")
    return 0


def transfer_repo():
    """To tranfer repo to some organization"""
    # TODO: bude ve verzi 1.12.0
    # TODO: trnasfer chybel v lokalni gitea (https://gitea.avalon.konstru.evektor.cz/api/swagger)
    pass


@traced
@logged
def list_org(args):
    """Function for listing organizations."""
    print(f"[{lineno()}] {lineno(): >4}.[ {BBla}DEBUG{RCol} ] Listing organizations")

    url = f"{SERVER}/api/v1/admin/orgs"
    print(f"[{lineno()}] {lineno(): >4}.[ {BBla}DEBUG{RCol} ] url: '{url}'")

    res = args.session.get(url)
    if res.status_code == 403:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Forbidden. You don't have enough access rights..."
        raise Exception(msg)

    elif res.status_code == 404:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] 404 - url page not found: '{url}'"
        raise Exception(msg)

    elif res.status_code == 200:
        print(f"[{lineno()}] {lineno(): >4}.[ {BBla}DEBUG{RCol} ] All ok. Here is the list.")
        data = json.loads(res.content)

    else:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Unknown error"
        raise Exception(msg)

    # Data acquired, list all found repos in nice table
    headers = ('Organization', 'Num Repos', 'description')
    results = [
        [
            item['username'],
            len(args.session.get(f"{SERVER}/api/v1/orgs/{item['username']}/repos").json()),
            item['description']
        ]
        for item in data]
    tbl = columnar(results, headers, no_borders=True)
    print(tbl)

    return 0


@traced
@logged
def list_repo(args):
    """Function for listing directories."""
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] Listing repo.")

    url = f"{SERVER}/api/v1/repos/search?q={args.repository}&sort=created&order=desc&limit=50"
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] url: {url}")

    repo_headers = {
        'accept': 'application/json',
        'content-type': 'application/json',
        'Authorization': f'token {GITEA_TOKEN}',
    }
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] repo_headers: {repo_headers}")

    res = requests.get(url, headers=repo_headers)
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] res: {res}")

    data = json.loads(res.content)
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] data.get('ok'): {data.get('ok')}")

    # Check if there was a good response
    if not data.get('ok'):
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Shit... Data not acquired... {data}"
        raise Exception(msg)

    if not data.get('data'):
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Search for repository '{args.repository}' returned 0 results... Try something different."
        raise Exception(msg)

    # Data acquired, list all found repos in nice table
    headers = ('id', 'repository', 'user', 'description')
    results = []
    if args.repository is not None and args.username:
        results = [[item['id'], item['name'], item['owner']['login'], item['description']]
                   for item in data.get('data') if args.username.lower() in item['owner']['login'].lower()]

        if len(results) == 0:
            print(f"[ {BYel}WARNING{RCol} ] No repository with += username: '{args.username}' found. Listing for all users.")

    if len(results) == 0 or not any([args.repository, args.username]):
        results = [[item['id'], item['name'], item['owner']['login'], item['description']]
                   for item in data.get('data')]

    tbl = columnar(results, headers, no_borders=True, wrap_max=5)
    print(tbl)

    return 0


def clone_repo(args_clone):
    """Clone repo into current directory."""
    target_dir = CURDIR.resolve()

    # User specified both arguments: --clone <reponame> <username>
    if len(args_clone) == 2:
        reponame, username = args_clone

        # Does the username exist?
        res = requests.get(f"{SERVER}/api/v1/users/{username}")
        if res.status_code != 200:
            print(f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] User '{username}' doesn't exist!")
            sys.exit(1)

        # Does the <repository> of <user> exist?
        res = requests.get(f"{SERVER}/api/v1/repos/{username}/{reponame}")
        if res.status_code != 200:
            print(f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Repository '{SERVER}/{username}/{reponame}' does not exist.")
            sys.exit(1)

        # Everything OK, clone the repository
        repo = Repo.clone_from(url=f"{SERVER}/{username}/{reponame}",
                                   to_path=Path(target_dir / reponame).resolve(),
                                   progress=Progress())
        print("[ INFO ] DONE")
        return repo

    # User didn't specify <username>: --clone <reponame>
    elif len(args_clone) == 1:
        reponame = args_clone[0]
        res = requests.get(f"{SERVER}/api/v1/repos/search?q={reponame}&sort=created&order=desc")
        # print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] res: {res}")

        data = json.loads(res.content)

        # Check if there was a good response
        if not data.get('ok'):
            print(f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Shit... Data not acquired... {data}")
            sys.exit(1)
        elif not data.get('data'):
            print(f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Search for repository '{reponame}' returned 0 results... Try something different.")
            sys.exit(1)

        # Data acquired, list all found repos in nice table
        headers = ('id', 'repository', 'user', 'description')
        results = [[item['id'], item['name'], item['owner']['login'], item['description']]
                   for item in data.get('data')]
        tbl = columnar(results, headers, no_borders=True)
        print(tbl)

        # Ask for repo ID
        answer = input("Enter repo ID: ")
        if not answer:
            print(f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] You have to write an ID")
            sys.exit(1)
        elif not answer.isdigit():
            print(f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] What you entered is not a number... You have to write one of the IDs.")
            sys.exit(1)

        # Get the right repo by it's ID
        repo_id = int(answer)
        selected_repository = [ls for ls in results if ls[0] == repo_id]

        # User made a mistake and entered number is not one of the listed repo IDs
        if len(selected_repository) == 0:
            print(f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Not a valid answer. You have to select one of the IDs.")
            sys.exit(1)

        # Something went wrong. There should not be len > 1... Where's the mistake in the code?
        elif len(selected_repository) > 1:
            print(f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Beware! len(selected_repository) > 1... That's weird... "
                  f"Like really... Len is: {len(selected_repository)}")
            sys.exit(1)

        print(f"[ INFO ] Clonning ID: {repo_id}")
        reponame, username = selected_repository[0][1], selected_repository[0][2]
        clone_repo([reponame, username])
        return 0


@traced
@logged
def remove_repo(args):
    """Remove repository from gitea"""
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] Removing repo.")

    if not args.username:
        print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] User didn't specify <username>")

        url = f"{SERVER}/api/v1/repos/search?q={args.repository}&sort=created&order=desc"
        print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] url: {url}")

        res = args.session.get(url)
        print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] res: {res}")

        data = json.loads(res.content)
        print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] data.get('ok'): {data.get('ok')}")

        # Check if there was a good response
        if not data.get('ok'):
            msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Shit... Data not acquired... {data}"
            raise Exception(msg)

        if not data.get('data'):
            msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Search for repository '{args.repository}' returned 0 results... Try something different."
            raise Exception(msg)

        # Data acquired, list all found repos in nice table
        headers = ('id', 'repository', 'user', 'description')
        results = [[item['id'], item['name'], item['owner']['login'], item['description']]
                   for item in data.get('data')]
        tbl = columnar(results, headers, no_borders=True, wrap_max=0)
        # print(tbl)
        tbl_as_string = str(tbl).split('\n')

        # Ask for repo to remove
        choices = [Separator(f"\n   {tbl_as_string[1]}\n")]
        choices.extend([{'name': item, 'value': item.split()[0]} for item in tbl_as_string[3:-1]])
        choices.append(Separator('\n'))

        questions = [{
            'type': 'list',
            'choices': choices,
            'pageSize': 50,
            'name': 'repo_id',
            'message': "Select repo to remove: ",
        }]

        answers = prompt(questions, style=QSTYLE)
        print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] answers: {answers}")

        if not answers.get('repo_id'):
            msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] You have to select an ID"
            raise Exception(msg)

        repo_id = int(answers.get('repo_id'))
        selected_repository = [ls for ls in results if ls[0] == repo_id]
        print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] selected_repository: {selected_repository[0]}")

        args.repository = selected_repository[0][1]
        print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] args.repository: {args.repository}")

        args.username = selected_repository[0][2]
        print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] args.username: {args.username}")

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

    # Everything OK, delete the repository
    print(f"[ {BWhi}INFO{RCol} ] You are about to REMOVE repository: '{SERVER}/{args.username}/{args.repository}'")
    answer = input(f"Are you SURE you want to do this??? This operation CANNOT be undone [y/N]: ")
    if answer.lower() not in ['y', 'yes']:
        print(f"[ {BWhi}INFO{RCol} ] Aborting... Nothing removed.")
        return 0

    answer = input(f"Enter the repository NAME as confirmation [{args.repository}]: ")
    if not answer == args.repository:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Entered reponame '{answer}' is not the same as '{args.repository}'. Aborting..."
        raise Exception(msg)

    print(f"[ {BWhi}INFO{RCol} ] Removing '{SERVER}/{args.username}/{args.repository}'")

    res = args.session.delete(url=f"{SERVER}/api/v1/repos/{args.username}/{args.repository}")
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] res: {res}")

    # Case when something is wrong with GITEA_TOKEN...
    if res.status_code == 401:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Unauthorized... Something wrong with you GITEA_TOKEN..."
        raise Exception(msg)

    # Case when normal user tries to remove repository of another user and doesn't have authorization for that
    elif res.status_code == 403:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Forbidden... You don't have enough permissinons to delete this repository..."
        raise Exception(msg)

    print(f"[ {BWhi}INFO{RCol} ] DONE")

    return 0


def remove_org(args):
    """Remove organization from gitea"""
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] Removing org.")

    if not args.organization:
        print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] User didn't specify <organization>")

        # Get all organizations
        res = args.session.get(f"{SERVER}/api/v1/admin/orgs")
        print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] res: {res}")

        data = json.loads(res.content)
        if not data:
            msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Search for organizations returned 0 results... Try something different."
            raise Exception(msg)

        headers = ['id', 'org', 'num repos', 'description']
        results = [
            [
                item['id'],
                item['username'],
                len(args.session.get(f"{SERVER}/api/v1/orgs/{item['username']}/repos").json()),
                item['description']
            ]
            for item in data
        ]
        tbl = columnar(results, headers, no_borders=True, wrap_max=0)
        # print(tbl)
        tbl_as_string = str(tbl).split('\n')

        # Ask for repo to remove
        choices = [Separator(f"\n   {tbl_as_string[1]}\n")]
        choices.extend([{'name': item, 'value': item.split()[0]} for item in tbl_as_string[3:-1]])
        choices.append(Separator('\n'))

        questions = [{
            'type': 'list',
            'choices': choices,
            'pageSize': 50,
            'name': 'org_id',
            'message': "Select org to remove: ",
        }]

        answers = prompt(questions, style=QSTYLE)
        print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] answers: {answers}")

        if not answers.get('org_id'):
            msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] You have to select an ID"
            raise Exception(msg)

        org_id = int(answers.get('org_id'))
        selected_org = [ls for ls in results if ls[0] == org_id]
        print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] selected_org: {selected_org[0]}")

        args.organization = selected_org[0][1]
        print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] args.organization: {args.organization}")

    # Get the org
    url = f"{SERVER}/api/v1/orgs/{args.organization}"
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] url: {url}")

    res = args.session.get(url)
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] res.status_code: {res.status_code}")

    data = json.loads(res.content)

    # Case org does not exist
    if res.status_code == 404:
        print(f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Organization '{args.organization}' not found...")
        args.organization = None
        remove_org(args)

    elif res.status_code != 200:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Unknown error for organization: '{args.organization}'"
        raise Exception(msg)

    # Everything OK, delete the repository
    print(f"[ INFO ] You are about to REMOVE organization: '{SERVER}/{args.organization}'")
    answer = input(f"Are you SURE you want to do this??? This operation CANNOT be undone [y/N]: ")

    if answer.lower() not in ['y', 'yes']:
        print(f"[ INFO ] Aborting... Nothing removed.")
        return 0

    answer = input(f"Enter the organization NAME as confirmation [{args.organization}]: ")
    if not answer == args.organization:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Entered orgname '{answer}' is not the same as '{args.organization}'. Aborting..."
        raise Exception(msg)

    print(f"[ INFO ] Deleting organization '{args.organization}'")

    url = f"{SERVER}/api/v1/orgs/{args.organization}"
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] url: {url}")

    res = args.session.delete(url)
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] res: {res}")

    if res.status_code == 401:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Unauthorized. You don't have enough rights to delete this repository."
        raise Exception(msg)

    elif res.status_code == 500:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] This organization still owns one or more repositories; delete or transfer them first."
        raise Exception(msg)

    if res.status_code != 204:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Unknown error for org: '{args.organization}'. Status code: {res.status_code}"
        raise Exception(msg)

    # All ok
    print(f"[ {BGre}OK{RCol} ] Done. Organization removed.")
    return 0


def edit_desc(args_clone):
    """Edit description in repo."""
    # User specified both arguments: --clone <reponame> <username>
    if len(args_clone) == 2:
        reponame, username = args_clone

        # Does the username exist?
        res = requests.get(f"{SERVER}/api/v1/users/{username}")
        if res.status_code != 200:
            print(f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] User '{username}' doesn't exist!")
            sys.exit(1)

        # Does the <repository> of <user> exist?
        res = requests.get(f"{SERVER}/api/v1/repos/{username}/{reponame}")
        if res.status_code != 200:
            print(f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Repository '{SERVER}/{username}/{reponame}' does not exist.")
            sys.exit(1)

        # Everything OK, edit description
        description = input(f"Write a description for {reponame}: ")
        repo_headers = {'Authorization': GITEA_TOKEN,
                        'accept': 'application/json',
                        'Content-Type': 'application/json'}

        repo_data = {'description': description}

        # res = requests.patch(url=f"{SERVER}/api/v1/repos/{username}/{reponame}?access_token={GITEA_TOKEN}",
        res = requests.patch(url=f"{SERVER}/api/v1/repos/{username}/{reponame}",
                             headers=repo_headers,
                             json=repo_data)
        if res.status_code != 200:
            print(f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] ")
            sys.exit(1)

        print("[ INFO ] DONE")
        return res

        # User didn't specify <username>: --clone <reponame>
    elif len(args_clone) == 1:
        reponame = args_clone[0]
        res = requests.get(
            f"{SERVER}/api/v1/repos/search?q={reponame}&sort=created&order=desc")
        # print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] res: {res}")

        data = json.loads(res.content)

        # Check if there was a good response
        if not data.get('ok'):
            print(f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Shit... Data not acquired... {data}")
            sys.exit(1)
        elif not data.get('data'):
            print(
                f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Search for repository '{reponame}' returned 0 results... Try something different.")
            sys.exit(1)

        # Data acquired, list all found repos in nice table
        headers = ('id', 'repository', 'user', 'description')
        results = [[item['id'], item['name'], item['owner']['login'], item['description']]
                   for item in data.get('data')]
        tbl = columnar(results, headers, no_borders=True)
        print(tbl)

        # Ask for repo ID
        answer = input("Enter repo ID: ")
        if not answer:
            print(f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] You have to write an ID")
            sys.exit(1)
        elif not answer.isdigit():
            print(
                f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] What you entered is not a number... You have to write one of the IDs.")
            sys.exit(1)

        # Get the right repo by it's ID
        repo_id = int(answer)
        selected_repository = [ls for ls in results if ls[0] == repo_id]

        # User made a mistake and entered number is not one of the listed repo IDs
        if len(selected_repository) == 0:
            print(f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Not a valid answer. You have to select one of the IDs.")
            sys.exit(1)

        # Something went wrong. There should not be len > 1... Where's the mistake in the code?
        elif len(selected_repository) > 1:
            print(f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Beware! len(selected_repository) > 1... That's weird... "
                  f"Like really... Len is: {len(selected_repository)}")
            sys.exit(1)

        print(f"[ INFO ] Editing ID: {repo_id}")
        reponame, username = selected_repository[0][1], selected_repository[0][2]
        edit_desc([reponame, username])
        return 0


# ====================================
# =           MAIN PROGRAM           =
# ====================================
if __name__ == '__main__':

    parser = cli.get_parser()
    args = parser.parse_args()

    # Initialize logger depending on the -v, -vv, -vvv arguments
    init_logging(args)

    # Initialize session with headers containing GITEA_TOKEN
    args.session = init_session(args)

    print("--------------------------------------------------------------------------------")
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] args: {args}")
    print("--------------------------------------------------------------------------------")

    # In case of no input, show help
    # if not any(vars(args).values()):
    if not len(sys.argv) > 1:
        print(f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] No arguments... Showing help.")
        print()
        parser.print_help()
        sys.exit()


    # React on user inputted command/arguments
    args.func(args)
    # try:
    #     args.func(args)
    # except Exception as e:
    #     raise Exception(f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] args.func(args) Exception bellow: \n{e}")


    if args.clone:
        clone_repo(args.clone)
        sys.exit()

    elif args.edit:
        edit_desc(args.edit)
        sys.exit()
