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
import re
import sys
import json
# import shlex
# import shutil
import copy
import getpass
import logging
import logging.handlers
import colorama
# import fileinput
import configparser
# import subprocess as sp
from pathlib import Path
# from dataclasses import dataclass
import validate


# Pip Libs
#==========
# from profilehooks import profile, timecall, coverage
# import click  # https://pypi.org/project/click/
import requests
from git import Repo, exc  # https://gitpython.readthedocs.io/en/stable/tutorial.html#tutorial-label
from columnar import columnar  # https://pypi.org/project/Columnar/
from colorama import init, Fore, Back, Style
from PyInquirer import style_from_dict, Token, prompt, Separator, print_json  # https://pypi.org/project/PyInquirer/
# from PyInquirer import Validator, ValidationError
# from autologging import logged, TRACE, traced  # https://pypi.org/project/Autologging/
from configobj import ConfigObj  # http://www.voidspace.org.uk/python/articles/configobj.shtml


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
Mag, BMag = Fore.MAGENTA, f'{Fore.MAGENTA}{Style.BRIGHT}'
Cya, BCya = Fore.CYAN, f'{Fore.CYAN}{Style.BRIGHT}'


# You have to run this script with python >= 3.7
if sys.version_info.major != 3:
    print(f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Hell NO! You're using Python2!! That's not cool man...")
    raise SystemExit
if sys.version_info.minor <= 6:
    print(f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Nah... Your Python version have to be at least 3.7. Sorry")
    raise SystemExit


# =================================
# =           CONSTANTS           =
# =================================
SCRIPTDIR = Path(__file__).resolve().parent
CURDIR = Path('.')
SETTINGS_DIR = Path.home() / '.eve_git'
SETTINGS_DIRS = (SCRIPTDIR, SETTINGS_DIR, CURDIR)
SETTINGS_FILENAME = 'eve-git.settings'
LOG_DIR = SETTINGS_DIR / 'logs'


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

LOG_COLORS = {
    # logging.TRACE: BBla,
    logging.DEBUG: Fore.LIGHTBLACK_EX,
    logging.INFO: Style.RESET_ALL,
    logging.WARNING: Fore.YELLOW,
    logging.ERROR: Fore.RED,
    logging.CRITICAL: Fore.RED + Style.BRIGHT,
    # logging.SUCCESS: BGre,
    # logging.OK: BGre,
}


class ColorFormatter(logging.Formatter):
    def format(self, record, *args, **kwargs):
        # if the corresponding logger has children, they may receive modified
        # record, so we want to keep it intact
        new_record = copy.copy(record)
        if new_record.levelno in LOG_COLORS:
            # we want levelname to be in different color, so let's modify it
            new_record.levelname = "{color_begin}{level: <8}{color_end}".format(
                level=new_record.levelname,
                color_begin=LOG_COLORS[new_record.levelno],
                color_end=colorama.Style.RESET_ALL,
            )
            # new_record.lineno = "{color_begin}{lineno}{color_end}".format(
            #     lineno=new_record.lineno,
            #     color_begin=LOG_COLORS[new_record.levelno],
            #     color_end=colorama.Style.RESET_ALL,
            # )
            # if new_record.levelno == 10:  # DEBUG - Even MSG colored
            #     new_record.msg = "{color_begin}{msg}{color_end}".format(
            #         msg=new_record.msg,
            #         color_begin=LOG_COLORS[new_record.levelno],
            #         color_end=colorama.Style.RESET_ALL,
            #     )
        # now we can let standart formatting take care of the rest
        return super(ColorFormatter, self).format(new_record, *args, **kwargs)


class NoColorFormatter(logging.Formatter):
    def format(self, record):
        ansi_escape = re.compile(r'''
            \x1B  # ESC
            (?:   # 7-bit C1 Fe (except CSI)
                [@-Z\\-_]
            |     # or [ for CSI, followed by a control sequence
                \[
                [0-?]*  # Parameter bytes
                [ -/]*  # Intermediate bytes
                [@-~]   # Final byte
            )
        ''', re.VERBOSE)
        new_record = copy.copy(record)
        new_record.msg = ansi_escape.sub("", new_record.msg)
        # record.msg = record.msg
        return super(NoColorFormatter, self).format(new_record)


# ===============================
# =           LOGGING           =
# ===============================
logging.getLogger().setLevel(logging.NOTSET)
log = logging.getLogger()

# Create logs dir if not exists
if not LOG_DIR.exists():
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def init_file_handlers(args):
    # FILE HANDLER - LAST RUN
    fhandler = logging.FileHandler(LOG_DIR / 'last_run.log', 'w')
    fhandler.setLevel(logging.NOTSET)
    formatter = NoColorFormatter(
        fmt='%(asctime)s - %(levelname)-8s | %(message)s [%(filename)s:%(funcName)s:%(lineno)s]',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    fhandler.setFormatter(formatter)
    logging.root.addHandler(fhandler)

    # FILE HANDLER - ALL - Rotating
    rotatingHandler = logging.handlers.RotatingFileHandler(
        filename=LOG_DIR / 'eve-git_rotating.log',
        maxBytes=1000000,
        backupCount=5
    )
    rotatingHandler.setLevel(logging.NOTSET)
    formatter = NoColorFormatter(
        fmt='%(asctime)s - %(levelname)-8s | %(message)s [%(filename)s:%(funcName)s:%(lineno)s]',
        datefmt='%Y-%m-%d %H:%M:%S')
    rotatingHandler.setFormatter(formatter)
    logging.getLogger().addHandler(rotatingHandler)

    # FILE HANDLER - ALL - Timed Rotating
    timedRotatingHandler = logging.handlers.TimedRotatingFileHandler(
        filename=LOG_DIR / 'eve-git_timed_rotating.log',
        when='midnight',
        backupCount=10
    )
    timedRotatingHandler.setLevel(logging.NOTSET)
    formatter = NoColorFormatter(
        fmt='%(asctime)s - %(levelname)-8s | %(message)s [%(filename)s:%(funcName)s:%(lineno)s]',
        datefmt='%Y-%m-%d %H:%M:%S')
    timedRotatingHandler.setFormatter(formatter)
    logging.getLogger().addHandler(timedRotatingHandler)


def init_logging(args):
    console = logging.StreamHandler(sys.stdout)
    # if args.v == 4:
    #     console.setLevel(logging.NOTSET)
    #     fmt = ColorFormatter('[%(levelname)s]: %(message)s (%(filename)s:%(lineno)s)')
    if args.v == 3:
        console.setLevel(logging.DEBUG)
        fmt = ColorFormatter('[%(levelname)s]: %(message)s (%(pathname)s:%(lineno)s)')
    elif args.v == 2:
        console.setLevel(logging.DEBUG)
        fmt = ColorFormatter('[%(levelname)s]: %(message)s (%(filename)s:%(lineno)s)')
    elif args.v == 1:
        console.setLevel(logging.DEBUG)
        fmt = ColorFormatter('[%(levelname)s]: %(message)s')
    else:
        console.setLevel(logging.INFO)
        fmt = ColorFormatter('[%(levelname)s]: %(message)s')
    console.setFormatter(fmt)
    logging.getLogger().addHandler(console)  # add to root logger


# =================================
# =           FUNCTIONS           =
# =================================
def init_session(args):
    session = requests.Session()

    session.headers.update({
        'accept': 'application/json',
        'content-type': 'application/json',
        'Authorization': f'token {GITEA_TOKEN}',
    })
    return session


def deploy(args):
    log.info(f"Deploying...")

    log.debug(f"args.repository: {args.repository}")
    log.debug(f"args.username: {args.username}")
    log.debug(f"args.branch: {args.branch}")

    selected = select_repo_from_list(args.session, SERVER, args.repository, args.username,
                                     'Select repository to deploy')

    args.repository = selected.repository
    args.username = selected.username

    url = f"{SERVER}/{args.username}/{args.repository}"
    log.debug(f"url: {url}")

    # TODO: This is not needed now because user select from interactive list but will be used in the future
    # when user enters all args: deploy reponame username [branch]
    # check_user_repo_exist(SERVER, args.repository, args.username, args.session)

    remote_branches = list_remote_branches(url)

    if args.branch not in remote_branches:
        msg = f"Remote branch [{BRed}{args.branch}{RCol}] does not exist.'"
        log.critical(msg)
        raise Exception(msg)

    questions = [
        {
            'message': f"Repository:",
            'default': args.repository,
            'name': 'repository',
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
        {
            'message': "Branch:",
            'default': args.branch,
            'name': 'branch',
            'type': 'input',
            'validate': lambda answer: f"Wrong choice. Choose from: {remote_branches}"
            if answer not in remote_branches else True
        },
    ]

    answers = prompt(questions, style=QSTYLE)
    if not answers:
        raise SystemExit

    args.branch = answers.get('branch')

    # Local and Remove directory
    tmp_dir = Path('/tmp') / args.repository
    target_dir = SKRIPTY_DIR / args.repository

    log.info(f"Deploying {BYel}{url}{RCol} [{BRed}{args.branch}{RCol}] into {BYel}{target_dir}{RCol}")
    ask_confirm(f"Are you SURE?")

    # Remove existing /tmp/{repository} folder
    if tmp_dir.exists():
        log.warning(f"'{tmp_dir}' already exists. Removing.")
        removed = remove_dir_tree(tmp_dir)
        log.debug(f"removed: {removed}")

    log.info(f"Clonning to '{tmp_dir}'...")

    tmp_repo = Repo.clone_from(url=url, to_path=tmp_dir, branch=args.branch, depth=1, progress=Progress())

    # Remove .git folder in /tmp repo
    log.info(f"Removing '.git' folder")
    log.debug(f"Removing '{tmp_repo.git_dir}'")
    remove_dir_tree(tmp_repo.git_dir)

    # Load app.conf from project root directory
    log.debug(f"Checking for 'app.conf'")
    app_conf_filepath = tmp_dir / 'app.conf'
    ignore_venv = True

    if app_conf_filepath.exists():
        log.debug(f"'{app_conf_filepath}' found. Loading config.")
        app_conf = configparser.ConfigParser(allow_no_value=True)
        app_conf.read(app_conf_filepath)

        # Make files executable
        log.debug(f"Changing permissions for all files in '{tmp_dir}' to 664")
        for item in tmp_dir.iterdir():
            item: Path
            if not item.is_file():
                continue
            os.chmod(item, 0o664)

        for key, val in app_conf.items('Executable'):
            exe_file = tmp_dir / key
            if not exe_file.exists():
                log.warning(f"File '{exe_file}' does not exist. Check your config in 'app.conf'.")
                continue
            log.debug(f"Making '{exe_file}' executable... Permissions: 774")
            os.chmod(exe_file, 0o774)

        src_requirements = tmp_dir / 'requirements.txt'
        if src_requirements.exists():
            dst_requirements = target_dir / 'requirements.txt'
            # Check if requirements.txt / app.conf are different
            ignore_venv = requirements_similar(src_requirements, dst_requirements)
            log.debug(f"ignore_venv: {ignore_venv}")

        # Requirements.txt files are different. Create virtual environment
        if not ignore_venv:
            framework = app_conf['Repo']['Framework']
            log.info(f"Making virtual environment...")
            cmd = f'{framework} -m venv {tmp_dir}/.env'
            log.debug(f"cmd: '{cmd}'")
            os.system(cmd)

            # Upgrade pip
            log.info(f"Upgrading Pip")
            cmd = f'{tmp_dir}/.env/bin/pip install --upgrade pip'
            log.debug(f"cmd: '{cmd}'")
            os.system(cmd)

            # Pip install
            log.info(f"Running Pip install")
            cmd = f'{tmp_dir}/.env/bin/pip install -r {tmp_dir}/requirements.txt'
            log.debug(f"cmd: '{cmd}'")
            os.system(cmd)

            # Replace venv paths with sed to target project path
            log.info(f"Changing venv paths inside files: '{tmp_dir}/.env' --> '{target_dir}/.env'")
            cmd = f'find {tmp_dir} -exec sed -i s@{tmp_dir}/.env@{target_dir}/.env@g {{}} \\; 2>/dev/null'
            log.debug(f"cmd: '{cmd}'")
            os.system(cmd)

        # Check if <reponame> already exists in /expSW/SOFTWARE/skripty/<reponame>
        if not target_dir.exists():
            cmd = f'ssh {SKRIPTY_SERVER} "mkdir {target_dir}"'
            os.system(cmd)
            log.debug(f"{target_dir} created.")

        # Make symbolic link(s)
        for key, val in app_conf.items('Link'):
            src_filepath = target_dir / key
            dst_filepath = SKRIPTY_EXE / val
            log.info(f"Linking '{src_filepath}' --> '{dst_filepath}'")
            make_symbolic_link(src_filepath, dst_filepath, SKRIPTY_SERVER)

    # Case app.conf file was not found in project
    else:
        log.info(f"'{app_conf_filepath}' not found... Ignoring making executables, symlinks, ...")
        log.info(f"To create a app.conf.template, use 'eve-git template app.conf'")

    # Rsync all the data
    log.debug(f"ignore_venv: '{ignore_venv}'")

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

    log.debug(f"Copy cmd: '{cmd}'")
    os.system(cmd)

    # Cleanup
    remove_dir_tree(tmp_dir)
    log.debug(f"'{tmp_dir}' removed")

    log.info(f"Deployment completed.")
    return 0


def connect_here(args):
    print(f"[ INFO ] Connecting remote repository with this one (local)")
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

    new_url = f'{SERVER}/{selected.username}/{selected.repository}'
    print(f"[ INFO ] Connecting '{new_url}'")

    repo = Repo(CURDIR)

    # Case repo is missing remote, add 'gitea'
    if len(repo.remotes) == 0:
        repo.create_remote('gitea', new_url)
        print(f"[ DONE ] Done (Created new 'gitea' remote)")
        return

    # Case repo has already some remotes. Go through them, if any 'gitea', ask for rewrite. Add otherwise.
    for remote in repo.remotes:
        if remote.name != 'gitea':
            continue
        print(f"[ {Yel}WARNING{RCol} ] 'gitea' remote already exists: {remote.url}")
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
        lineno(f"answers: {answers}")

        if answers.get('continue'):
            remote.set_url(f'{new_url}')
            print(f"[ DONE ] Remote 'gitea' changed from '{remote.url}' --> '{new_url}'")
            return
        else:
            print("[ INFO ] Modifying url canceled.")
            raise SystemExit

    lineno(f"Neither of the repositories was named 'gitea', adding a new one.")
    repo.create_remote('gitea', new_url)
    print(f"[ DONE ] Done (Added new 'gitea' remote)")
    return


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
        raise SystemExit

    lineno(f"answers: {answers}")

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


def create_repo(args):
    questions = [
        {
            'message': "Repository name:",
            'name': 'reponame',
            'default': args.reponame,
            'type': 'input',
            'validate': lambda answer: "Cannot be empty."
            if not answer else True
        },
        {
            'message': "Description:",
            'name': 'description',
            'default': args.description,
            'type': 'input',
            'validate': lambda answer: "Cannot be empty."
            if not answer else True
        },
        {
            'message': "User/Org:",
            'name': 'username',
            'default': args.username,
            'type': 'input',
            'validate': lambda answer: "Cannot be empty."
            if not answer else True
        },
    ]

    answers = prompt(questions, style=QSTYLE)
    if not answers:
        raise SystemExit

    lineno(f"answers: {answers}")

    args.reponame = answers.get('reponame')
    args.description = answers.get('description')
    args.username = answers.get('username')

    lineno(f"args.reponame: {args.reponame}")
    lineno(f"args.description: {args.description}")
    lineno(f"args.username: {args.username}")

    repo_data = {
        "name": args.reponame,
        "description": args.description,
        "auto_init": True,
        "private": False,
        # "gitignores": 'Evektor',
        # "issue_labels": "string",
        # "license": "string",
        # "readme": "string"
    }

    lineno(f"repo_data: {repo_data}")


    if args.username == getpass.getuser():
        # Creating new repo as normal user
        url = f"{SERVER}/api/v1/user/repos"
    else:
        # User specified different user/org. Only users with admin right can create repos anywhere
        lineno(f"Using admin args.username: {args.username}")
        url = f"{SERVER}/api/v1/admin/users/{args.username}/repos"

    lineno(f"url: {url}")

    # Post the repo
    res = args.session.post(url=url, json=repo_data)
    lineno(f"res: {res}")

    # Viable responses
    if res.status_code == 401:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Unauthorized... Missing, wrong or weak (non-admin) GITEA_TOKEN..."
        raise Exception(msg)

    elif res.status_code == 403:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Status code: {res.status_code}. Something wrong with GITEA_TOKEN. Using admin-command with non-admin token?"
        raise Exception(msg)

    elif res.status_code == 409:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Repository '{args.reponame}' under '{args.username}' already exists."
        raise Exception(msg)

    elif res.status_code == 422:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Validation Error... Can't create repository with this name. Details bellow."
        msg += f"\n{res.json()}"
        raise Exception(msg)

    elif res.status_code != 201:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Something went wrong. Don't know what. Status_code: {res.status_code}"
        raise Exception(msg)

    print(f"[ INFO ] Repository created.")

    answer = input("Clone into current folder? [Y/n]: ")
    if answer.lower() in ['y', 'yes']:
        target_path = Path(CURDIR.resolve() / args.reponame).resolve()
        url = f"{SERVER}/{args.username}/{args.reponame}"
        lineno(f"target_path: {target_path}")
        lineno(f"url: {url}")
        Repo.clone_from(url=url, to_path=target_path, branch='master', progress=Progress())

    print(f"[ INFO ] DONE")
    return 0


def transfer_repo():
    """To tranfer repo to some organization"""
    # TODO: bude ve verzi 1.12.0
    pass


def list_org(args):
    """Function for listing organizations."""
    lineno(f"Listing organizations")

    tbl = get_org_list_as_table(args.session, SERVER)
    print(tbl)

    return


def list_repo(args):
    """Function for listing directories."""
    lineno(f"Listing repository.")
    tbl = get_repo_list_as_table(args.session, SERVER, args.repository, args.username)
    print(tbl)
    return


def clone_repo(args):
    """Clone repo into current directory."""
    lineno(f"Cloning repository.")

    if not args.username:
        lineno(f"User didn't specify <username>")

        selected = select_repo_from_list(args.session, SERVER, args.repository, "Select repo to clone: ")
        lineno(f"selected.repository: {selected.repository}")
        lineno(f"selected.username: {selected.username}")

        args.repository = selected.repository
        args.username = selected.username

    # Check if 'user' and combination of 'user/repo' exist
    check_user_repo_exist(SERVER, args.repository, args.username, args.session)

    # Everything OK, clone the repository
    print(f"[ INFO ] Cloning '{SERVER}/{args.username}/{args.repository}'")

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

    print(f"[ INFO ] DONE")


def remove_repo(args):
    """Remove repository from gitea"""
    lineno(f"Removing repo.")

    if not args.username:
        lineno(f"User didn't specify <username>")
        selected = select_repo_from_list(args.session, SERVER, args.repository, "Select repo to remove: ")

        args.repository = selected.repository
        args.username = selected.username

    check_user_repo_exist(SERVER, args.repository, args.username, args.session)

    print(f"[ INFO ] You are about to REMOVE repository: '{SERVER}/{args.username}/{args.repository}'")
    ask_confirm("Are you SURE you want to do this??? This operation CANNOT be undone!!!")
    ask_confirm_data(f"Enter the repository NAME as confirmation [{args.repository}]", args.repository)

    # DELETE the repo
    print(f"[ INFO ] Removing '{SERVER}/{args.username}/{args.repository}'")
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

    print(f"[ INFO ] DONE")

    return 0


def remove_org(args):
    """Remove organization from gitea"""
    lineno(f"Removing oranization")

    org_found = check_org_exist(server=SERVER, organization=args.organization, session=args.session)
    lineno(f"org_found: {org_found}")

    if not org_found:
        lineno(f"User didn't specify <organization>")

        selected = select_org_from_list(session=args.session, server=SERVER, question="Select org to remove: ")
        lineno(f"selected.organization: {selected.organization}")

        args.organization = selected.organization

    # Everything OK, delete the organization
    print(f"[ INFO ] You are about to REMOVE organization: '{SERVER}/{args.organization}'")

    ask_confirm('Are you SURE you want to do this??? This operation CANNOT be undone.')
    ask_confirm_data(f'Enter the organization NAME as confirmation [{args.organization}]',
                     comp_str=args.organization)

    print(f"[ INFO ] Deleting organization '{args.organization}'")

    url = f"{SERVER}/api/v1/orgs/{args.organization}"
    lineno(f"url: {url}")

    res = args.session.delete(url)
    lineno(f"res: {res}")

    if res.status_code == 401:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Unauthorized. You don't have enough rights to delete this repository."
        raise Exception(msg)

    elif res.status_code == 403:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Status code: {res.status_code}. Can't remove organization that is not mine. Or other unknown problem."
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
    lineno(f"Editing repository.")

    if not args.username:
        lineno(f"User didn't specify <username>")

        selected = select_repo_from_list(args.session, SERVER, args.repository, "Select repo to edit: ")
        lineno(f"selected.repository: {selected.repository}")
        lineno(f"selected.username: {selected.username}")
        lineno(f"selected.description: {selected.description}")

        args.repository = selected.repository
        args.username = selected.username
        args.description = selected.description

    check_user_repo_exist(SERVER, args.repository, args.username, args.session)

    repo = args.session.get(f"{SERVER}/api/v1/repos/{args.username}/{args.repository}")
    args.description = repo.json().get('description')

    # Everything OK, edit the repository
    print(f"[ INFO ] Editing repository: '{SERVER}/{args.username}/{args.repository}'")

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
    if not answers:
        raise SystemExit

    lineno(f"answers: {answers}")

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
        lineno(f"args.session.headers: {args.session.headers}")
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Status code: {res.status_code}"
        raise Exception(msg)

    print(f"[ INFO ] DONE")

    return


def update_token(args):
    """Update GITEA_TOKEN in $HOME/eve-git.settings config file."""
    settings_file = Path.home() / 'eve-git.settings'
    # Don't know how to save the config back with comments too...
    config = configparser.ConfigParser()

    if args.token == '':
        if not settings_file.exists():
            print(f"[ INFO ] Settings file '{settings_file}' does not exists. Use: --token YOUR_API_KEY")
            return

        config.read(settings_file)
        current_token = config['server']['gitea_token']
        print(f"[ INFO ] Current Gitea token: {current_token}")
        return

    if not settings_file.exists():
        print(f"[ INFO ] Creating new {settings_file} with Gitea token: {args.token}")
        config['server'] = {'gitea_token': args.token}
        config['app'] = {'debug': False}
    else:
        lineno(f"Updating value: 'config[server] = {{gitea_token = {args.token}}}'")
        config.read(settings_file)
        current_token = config['server']['gitea_token']
        config['server'] = {'gitea_token': args.token}
        ask_confirm(f"Replace current Gitea token '{current_token}' --> '{args.token}'?")

    lineno(f"Writing config into: {settings_file.resolve()}")

    with open(settings_file, 'w') as f:
        config.write(f)

    # In [69]: user
    # Out[69]: ConfigObj({'debug': 'True', 'main_file': 'main.py', 'venv': {'use': 'True'}})

    # In [70]: n = NestedNamespace(user)

    # In [71]: n
    # Out[71]: NestedNamespace(debug='True', main_file='main.py', venv=NestedNamespace(use='True'))

    # In [72]: n.debug
    # Out[72]: 'True'

    # In [73]: n.venv
    # Out[73]: NestedNamespace(use='True')

    # In [74]: n.venv.use
    # Out[74]: 'True'


def templates(args):
    templates_dir = SCRIPTDIR / 'templates'
    log.debug(f"templates_dir: {templates_dir.resolve()}")
    selected = select_files_from_list(
        directory=templates_dir, question="Select template file to download into current directory")
    log.debug(f"selected: {selected}")
    shutil.copy(selected.filepath, CURDIR)
    log.info(f"File {selected.filename} copied into current directory.")
    return


# ====================================
# =           MAIN PROGRAM           =
# ====================================
if __name__ == '__main__':
    parser = cli.get_parser()
    args = parser.parse_args()

    console = logging.StreamHandler(sys.stdout)

    # Initialize session with headers containing GITEA_TOKEN
    args.session = init_session(args)

    # Initialize logger depending on the -v, -vv, -vvv arguments
    init_file_handlers(args)
    init_logging(args)

    log.debug("--------------------------------------------------------------------------------")
    log.debug(f"args: {args}")
    log.debug("--------------------------------------------------------------------------------")

    # if not any(vars(args).values()):

    # In case of no input, show help
    if len(sys.argv) <= 1:
        log.error(f"No arguments... Showing help.")
        print()
        parser.print_help()
        sys.exit()

    if args.token is not None:
        update_token(args)
        raise SystemExit

    # React on user inputted command/arguments
    args.func(args)
