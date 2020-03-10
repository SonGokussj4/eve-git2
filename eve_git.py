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
# import shutil
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
    Token.Selected: '#cc5454',
    Token.Pointer: '#54FF54 bold',
    # Token.Instruction: '#E8CB26',
    # Token.Answer: '#F3F3F3 bold',
    Token.Answer: '#ffffff',
    # Token.Question: '#8C8C8C',
})


# ====================================================
# =           Exceptions without Traceback           =
# ====================================================
def excepthook(type, value, traceback):
    print(value)


if not DEBUG:
    sys.excepthook = excepthook


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
        format="{: >4}.[ %(levelname)s ] %(funcName)s: %(message)s".format(lineno()))


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

    lineno(f"args.repository: {args.repository}")
    lineno(f"args.username: {args.username}")
    lineno(f"args.branch: {args.branch}")

    check_user_repo_exist(SERVER, args.repository, args.username, args.session)

    # Local and Remove directory
    tmp_dir = Path('/tmp') / args.repository
    target_dir = SKRIPTY_DIR / args.repository

    # ================================================================
    # =           REMOVE EXISTING /tmp/{repository} FOLDER           =
    # ================================================================
    if tmp_dir.exists():
        print(f"[ {Yel}WARNING{RCol} ] '{tmp_dir}' already exists. Removing.")
        removed = remove_dir_tree(tmp_dir)
        lineno(f"removed: {removed}")

    # ================================================
    # =           CLONE GIT REPO INTO /tmp           =
    # ================================================
    print(f"[ {BWhi}INFO{RCol}  ] Clonning to '{tmp_dir}' DONE")

    url = f"{SERVER}/{args.username}/{args.repository}"
    lineno(f"Clonning url: {url}")

    Repo.clone_from(url=url, to_path=tmp_dir, branch=args.branch, depth=1, progress=Progress())

    # ==========================================
    # =           REMOVE .GIT FOLDER           =
    # ==========================================
    print(f"[ {BWhi}INFO{RCol} ] Removing '.git' folder")
    git_folder = tmp_dir / '.git'
    lineno(f"Removing '{git_folder}'")
    remove_dir_tree(git_folder)

    # ========================================
    # =           LOAD REPO.CONFIG           =
    # ========================================
    lineno(f"Checking 'repo.config'")
    repo_cfg_filepath = tmp_dir / 'repo.config'
    ignore_venv = True

    if repo_cfg_filepath.exists():
        lineno(f"'{repo_cfg_filepath}' found. Loading config.")
        repo_cfg = configparser.ConfigParser(allow_no_value=True)
        repo_cfg.read(repo_cfg_filepath)

        # =============================================
        # =           MAKE FILES EXECUTABLE           =
        # =============================================
        lineno(f"Changing permissions for all files in '{tmp_dir}' to 664")
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
            lineno(f"Making '{exe_file}' executable... Permissions: 774")
            os.chmod(exe_file, 0o774)

        # ================================================================================
        # =           CHECK IF REQUIREMENTS.TXT / REPO.CONFIG ARE DIFFERENT           =
        # ================================================================================
        src_requirements = tmp_dir / 'requirements.txt'
        lineno(f"src_requirements: {src_requirements}")
        dst_requirements = target_dir / 'requirements.txt'
        lineno(f"dst_requirements: {dst_requirements}")
        ignore_venv = requirements_similar(src_requirements, dst_requirements)
        lineno(f"ignore_venv: {ignore_venv}")

        # ==================================================
        # =           CREATE VIRTUAL ENVIRONMENT           =
        # ==================================================
        if not ignore_venv:
            framework = repo_cfg['Repo']['Framework']
            print(f"[ {BWhi}INFO{RCol}  ] Making virtual environment...")
            cmd = f'{framework} -m venv {tmp_dir}/.env'
            lineno(f"cmd: '{cmd}'")
            os.system(cmd)

            # ===================================
            # =           UPGRADE PIP           =
            # ===================================
            print(f"[ {BWhi}INFO{RCol}  ] Upgrading Pip")
            cmd = f'{tmp_dir}/.env/bin/pip install --upgrade pip'
            lineno(f"cmd: '{cmd}'")
            os.system(cmd)

            # ===================================
            # =           PIP INSTALL           =
            # ===================================
            print(f"[ {BWhi}INFO{RCol}  ] Running Pip install")
            cmd = f'{tmp_dir}/.env/bin/pip install -r {tmp_dir}/requirements.txt'
            lineno(f"cmd: '{cmd}'")
            os.system(cmd)

        # ==================================================
        # =           CHANGE VENV PATHS with SED           =
        # ==================================================
        print(f"[ {BWhi}INFO{RCol}  ] Changing venv paths '{tmp_dir}/.env' --> '{target_dir}/.env'")
        cmd = f'find {tmp_dir} -exec sed -i s@{tmp_dir}/.env@{target_dir}/.env@g {{}} \\; 2>/dev/null'
        lineno(f"cmd: '{cmd}'")
        os.system(cmd)

        # ===================================================
        # =           REPLACE MAIN_FILE IN run.sh           =
        # ===================================================
        runsh_file = tmp_dir / 'run.sh'
        lineno(f"runsh_file: '{runsh_file}'")
        main_file = repo_cfg['venv']['main_file']
        lineno(f"main_file: '{main_file}'")

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
            lineno(f"{target_dir} created.")

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
            lineno(f"cmd: '{cmd}'")
            os.system(cmd)

    else:
        print(f"[ {BWhi}INFO{RCol}  ] '{repo_cfg_filepath}' not found... Ignoring making executables, symlinks, ...")
        print(f"[ {BWhi}INFO{RCol}  ] To create a repo.config.template, use 'eve-git template repo.config'")

    # ==========================================
    # =           RSYNC ALL THE DATA           =
    # ==========================================
    # Rsync all the data
    lineno(f"ignore_venv: '{ignore_venv}'")
    # Case venv was created, copy all the data, even venv, because something was updated
    if not ignore_venv:
        if os.name != 'nt':
            cmd = f'rsync -ah --delete {tmp_dir} {SKRIPTY_SERVER}:{target_dir.parent}'
        else:
            cmd = f'xcopy /Y {tmp_dir} {target_dir.parent}'
    # Case venv wasn't created locally, ignore venv folders so that they will not be deleted in target_dir
    else:
        if os.name != 'nt':
            cmd = (f'rsync -ah --delete --exclude-from={SCRIPTDIR}/rsync-directory-exclusions.txt '
                   f'{tmp_dir} {SKRIPTY_SERVER}:{target_dir.parent}')
        else:
            cmd = f'xcopy /S /I /E /Y {tmp_dir} {target_dir.parent} /EXCLUDE:rsync-directory-exclusions.txt'
    lineno(f"Copy cmd: '{cmd}'")
    os.system(cmd)

    # ===============================
    # =           CLEANUP           =
    # ===============================
    remove_dir_tree(tmp_dir)
    lineno(f"'{tmp_dir}' removed")

    print(f"[ {BWhi}INFO{RCol}  ] Deployment completed.")
    return 0


@traced
@logged
def connect_here(args):
    print(f"[ {BWhi}INFO{RCol}  ] Connecting...")
    if not is_git_repo(CURDIR):
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Current location is not git repository: '{CURDIR.resolve()}'"
        raise Exception(msg)

    selected = select_repo_from_list(
        session=args.session,
        server=SERVER,
        repository=args.repository,
        question="Select repo to connect to: ",
    )
    lineno(f"selected: {selected}")

    check_user_repo_exist(SERVER, selected.repository, selected.username, args.session)

    # Everything OK, delete the repository
    print(f"[ {BWhi}INFO{RCol} ] Connecting '{SERVER}/{selected.username}/{selected.repository}'")

    repo = Repo(CURDIR)
    for remote in repo.remotes:
        if remote.name == 'gitea':
            print(f"[ {Yel}WARNING{RCol} ] 'Gitea' remote already exists: {remote.url}")
            questions = [
                {
                    'message': 'Do you want to rewrite the url?',
                    'name': 'continue',
                    'type': 'confirm',
                }
            ]
            answers = prompt(questions, style=QSTYLE)
            if not answers:
                raise SystemExit
            if answers.get('continue'):
                remote.set_url(f'{SERVER}/{selected.username}/{selected.repository}')
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
    if not answers:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] User canceled."
        raise Exception(msg)

    args.organization = answers.get('organization')
    args.description = answers.get('description')
    args.fullname = answers.get('fullname')
    args.visibility = answers.get('visibility')

    lineno(f"args.reponame: {args.organization}")
    lineno(f"args.description: {args.description}")
    lineno(f"args.fullname: {args.fullname}")
    lineno(f"args.visibility: {args.visibility}")

    repo_data = {
        "description": args.description,
        "full_name": args.fullname,
        "repo_admin_change_team_access": True,
        "username": args.organization,  # THIS is Organization name
        "visibility": args.visibility,
    }
    lineno(f"repo_data: {repo_data}")

    # Create organization
    res = args.session.post(url=f"{SERVER}/api/v1/orgs", json=repo_data)
    lineno(f"res: {res}")

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

    lineno(f"args.reponame: {args.reponame}")
    lineno(f"args.description: {args.description}")
    lineno(f"args.username: {args.username}")

    repo_data = {
        'auto_init': True,
        'name': args.reponame,
        'readme': 'Default',
        'description': args.description,
        # 'gitignores': 'Evektor',
        'private': False
    }
    lineno(f"repo_data: {repo_data}")

    # User specified different user/org. Only users with admin right can create repos anywhere
    url = f"{SERVER}/api/v1/user/repos"
    if args.username != getpass.getuser():
        lineno(f"args.username: {args.username}")
        url = f"{SERVER}/api/v1/admin/users/{args.username}/repos"
    lineno(f"url: {url}")

    # Post the repo
    res = args.session.post(url=url, json=repo_data)
    lineno(f"res: {res}")

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
    lineno(f"Listing repo.")

    url = f"{SERVER}/api/v1/repos/search?q={args.repository}&sort=created&order=desc&limit=50"
    lineno(f"url: {url}")

    res = args.session.get(url)
    lineno(f"res: {res}")

    data = json.loads(res.content)
    lineno(f"data.get('ok'): {data.get('ok')}")

    # Check if there was a good response
    if not data.get('ok'):
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Shit... Data not acquired... {data}"
        raise Exception(msg)

    if not data.get('data'):
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Search for repository '{args.repository}' returned 0 results... Try something different."
        raise Exception(msg)

    # Data acquired, list all found repos in nice table
    tbl_headers = ('id', 'repository', 'user', 'description')
    results = []
    if args.repository is not None and args.username:
        results = [[item['id'], item['name'], item['owner']['login'], item['description']]
                   for item in data.get('data') if args.username.lower() in item['owner']['login'].lower()]

        if len(results) == 0:
            print(f"[ {BYel}WARNING{RCol} ] No repository with += username: '{args.username}' found. Listing for all users.")

    if len(results) == 0 or not any([args.repository, args.username]):
        results = [[item['id'], item['name'], item['owner']['login'], item['description']]
                   for item in data.get('data')]

    tbl = columnar(results, tbl_headers, no_borders=True, wrap_max=5)
    print(tbl)

    return 0


@traced
@logged
def clone_repo(args):
    """Clone repo into current directory."""
    lineno(f"Cloning repo.")

    if not args.username:
        lineno(f"User didn't specify <username>")

        url = f"{SERVER}/api/v1/repos/search?q={args.repository}&sort=created&order=desc"
        lineno(f"url: {url}")

        res = args.session.get(url)
        lineno(f"res: {res}")

        data = json.loads(res.content)
        lineno(f"data.get('ok'): {data.get('ok')}")

        # Check if there was a good response
        if not data.get('ok'):
            msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Shit... Data not acquired... {data}"
            raise Exception(msg)

        if not data.get('data'):
            msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Search for repository '{args.repository}' returned 0 results... Try something different."
            raise Exception(msg)

        # Data acquired, list all found repos in nice table
        tbl_headers = ('id', 'repository', 'user', 'description')
        results = [[item['id'], item['name'], item['owner']['login'], item['description']]
                   for item in data.get('data')]
        tbl = columnar(results, tbl_headers, no_borders=True, wrap_max=0)
        # print(tbl)
        tbl_as_string = str(tbl).split('\n')

        # Ask for repo to clone
        choices = [Separator(f"\n   {tbl_as_string[1]}\n")]
        choices.extend([{'name': item, 'value': item.split()[0]} for item in tbl_as_string[3:-1]])
        choices.append(Separator('\n'))

        questions = [{
            'type': 'list',
            'choices': choices,
            'pageSize': 50,
            'name': 'repo_id',
            'message': "Select repo to clone: ",
        }]

        answers = prompt(questions, style=QSTYLE)
        lineno(f"answers: {answers}")
        if not answers:
            msg = f"{lineno(): >4}.[ {BWhi}INFO{RCol} ] User Canceled"
            raise Exception(msg)

        repo_id = int(answers.get('repo_id'))
        selected_repository = [ls for ls in results if ls[0] == repo_id]
        lineno(f"selected_repository: {selected_repository[0]}")

        args.repository = selected_repository[0][1]
        lineno(f"args.repository: {args.repository}")

        args.username = selected_repository[0][2]
        lineno(f"args.username: {args.username}")

    # Check if 'user' and combination of 'user/repo' exist
    check_user_repo_exist(SERVER, args.repository, args.username, args.session)

    # Everything OK, clone the repository
    print(f"[ {BWhi}INFO{RCol} ] Cloning '{SERVER}/{args.username}/{args.repository}'")

    target_dir = CURDIR / args.repository
    if target_dir.exists():
        msg = (f"[ {BRed}ERROR{RCol} ] Folder with the same name '{args.repository}' "
               f"already in target dir: '{target_dir.resolve()}'")
        raise Exception(msg)

    repo = Repo.clone_from(
        url=f"{SERVER}/{args.username}/{args.repository}",
        to_path=CURDIR / args.repository,
        progress=Progress())
    print(f"[ {BBla}DEBUG{RCol} ] repo: {repo}")

    print(f"[ {BWhi}INFO{RCol} ] DONE")


@traced
@logged
def remove_repo(args):
    """Remove repository from gitea"""
    lineno(f"Removing repo.")

    if not args.username:
        lineno(f"User didn't specify <username>")

        url = f"{SERVER}/api/v1/repos/search?q={args.repository}&sort=created&order=desc"
        lineno(f"url: {url}")

        res = args.session.get(url)
        lineno(f"res: {res}")

        data = json.loads(res.content)
        lineno(f"data.get('ok'): {data.get('ok')}")

        # Check if there was a good response
        if not data.get('ok'):
            msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Shit... Data not acquired... {data}"
            raise Exception(msg)

        if not data.get('data'):
            msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Search for repository '{args.repository}' returned 0 results... Try something different."
            raise Exception(msg)

        # Data acquired, list all found repos in nice table
        tbl_headers = ('id', 'repository', 'user', 'description')
        results = [[item['id'], item['name'], item['owner']['login'], item['description']]
                   for item in data.get('data')]
        tbl = columnar(results, tbl_headers, no_borders=True, wrap_max=0)
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
        lineno(f"answers: {answers}")

        if not answers.get('repo_id'):
            msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] You have to select an ID"
            raise Exception(msg)

        repo_id = int(answers.get('repo_id'))
        selected_repository = [ls for ls in results if ls[0] == repo_id]
        lineno(f"selected_repository: {selected_repository[0]}")

        args.repository = selected_repository[0][1]
        lineno(f"args.repository: {args.repository}")

        args.username = selected_repository[0][2]
        lineno(f"args.username: {args.username}")

    check_user_repo_exist(SERVER, args.repository, args.username, args.session)

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
    lineno(f"res: {res}")

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
    lineno(f"Removing org.")

    if not args.organization:
        lineno(f"User didn't specify <organization>")

        # Get all organizations
        res = args.session.get(f"{SERVER}/api/v1/admin/orgs")
        lineno(f"res: {res}")

        data = json.loads(res.content)
        if not data:
            msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Search for organizations returned 0 results... Try something different."
            raise Exception(msg)

        tbl_headers = ['id', 'org', 'num repos', 'description']
        results = [
            [
                item['id'],
                item['username'],
                len(args.session.get(f"{SERVER}/api/v1/orgs/{item['username']}/repos").json()),
                item['description']
            ]
            for item in data
        ]
        tbl = columnar(results, tbl_headers, no_borders=True, wrap_max=0)
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
        lineno(f"answers: {answers}")

        if not answers.get('org_id'):
            msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] You have to select an ID"
            raise Exception(msg)

        org_id = int(answers.get('org_id'))
        selected_org = [ls for ls in results if ls[0] == org_id]
        lineno(f"selected_org: {selected_org[0]}")

        args.organization = selected_org[0][1]
        lineno(f"args.organization: {args.organization}")

    # Get the org
    url = f"{SERVER}/api/v1/orgs/{args.organization}"
    lineno(f"url: {url}")

    res = args.session.get(url)
    lineno(f"res.status_code: {res.status_code}")

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
    lineno(f"url: {url}")

    res = args.session.delete(url)
    lineno(f"res: {res}")

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


def edit_desc(args):
    """Edit description in repo."""
    lineno(f"Editing repo.")

    if not args.username:
        lineno(f"User didn't specify <username>")

        url = f"{SERVER}/api/v1/repos/search?q={args.repository}&sort=created&order=desc"
        lineno(f"url: {url}")

        res = args.session.get(url)
        lineno(f"res: {res}")

        data = json.loads(res.content)
        lineno(f"data.get('ok'): {data.get('ok')}")

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
        tbl_as_string = str(tbl).split('\n')

        # Ask for repo to edit
        choices = [Separator(f"\n   {tbl_as_string[1]}\n")]
        choices.extend([{'name': item, 'value': item.split()[0]} for item in tbl_as_string[3:-1]])
        choices.append(Separator('\n'))

        questions = [{
            'type': 'list',
            'choices': choices,
            'pageSize': 50,
            'name': 'repo_id',
            'message': "Select repo to edit: ",
        }]

        answers = prompt(questions, style=QSTYLE)
        lineno(f"answers: {answers}")
        if not answers:
            msg = f"[ {BWhi}INFO{RCol} ] Canceled by user."
            raise Exception(msg)

        repo_id = int(answers.get('repo_id'))
        selected_repository = [ls for ls in results if ls[0] == repo_id]
        lineno(f"selected_repository: {selected_repository[0]}")

        _, args.repository, args.username, args.description = selected_repository[0]
        lineno(f"args.repository: {args.repository}")
        lineno(f"args.username: {args.username}")
        lineno(f"args.description: {args.description}")

    check_user_repo_exist(SERVER, args.repository, args.username, args.session)

    repo = args.session.get(f"{SERVER}/api/v1/repos/{args.username}/{args.repository}")
    args.description = repo.json().get('description')

    # Everything OK, edit the repository
    print(f"[ {BWhi}INFO{RCol} ] Editing repository: '{SERVER}/{args.username}/{args.repository}'")

    questions = [
        {
            'message': "Description:",
            'default': args.description,
            'name': 'description',
            'type': 'input',
            'validate': lambda answer: "Cannot be empty."
            if not answer else True
        },
    ]

    answers = prompt(questions, style=QSTYLE)
    lineno(f"answers: {answers}")
    if not answers:
        msg = f"[ {BWhi}INFO{RCol} ] Canceled by user."
        raise Exception(msg)

    args.description = answers.get('description')

    repo_data = {'description': args.description}

    res = args.session.patch(url=f"{SERVER}/api/v1/repos/{args.username}/{args.repository}", json=repo_data)

    # Case when normal user tries to remove repository of another user and doesn't have authorization for that
    if res.status_code == 403:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Forbidden... APIForbiddenError is a forbidden error response. Not authorized (weak GITEA_TOKEN)"
        raise Exception(msg)

    # Case when something is wrong with GITEA_TOKEN...
    elif res.status_code == 422:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] APIValidationError is error format response related to input validation"
        raise Exception(msg)

    # Other cases should not come
    if res.status_code != 200:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Status code: {res.status_code}"
        raise Exception(msg)

    print(f"[ {BWhi}INFO{RCol} ] DONE")

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
    lineno(f"args: {args}")
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
