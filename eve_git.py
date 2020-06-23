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
# import validate


# Pip Libs
#==========
# from profilehooks import profile, timecall, coverage
# import click  # https://pypi.org/project/click/
import requests
from git import Repo, exc  # https://gitpython.readthedocs.io/en/stable/tutorial.html#tutorial-label
# from columnar import columnar  # https://pypi.org/project/Columnar/
from colorama import init, Fore, Back, Style
from PyInquirer import style_from_dict, Token, prompt, Separator, print_json  # https://pypi.org/project/PyInquirer/
# from PyInquirer import Validator, ValidationError
# from autologging import logged, TRACE, traced  # https://pypi.org/project/Autologging/
# from configobj import ConfigObj  # http://www.voidspace.org.uk/python/articles/configobj.shtml


# User Libs
#===========
import cli
import utils as utl
from utils import *  # FIXME Predelat na import utils jen


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


# def addLogLevel(levelName, level):
#     """
#     Add a new log level.

#     :param levelName: name for the new level
#     :param level:     integer defining the level
#     """
#     n, N = levelName, levelName.upper()
#     setattr(logging, N, level)
#     # setattr(logging, N + "_COLOR", color)
#     logging.addLevelName(level, N)
#     def display(self, message, *args, **kwargs):
#         if self.isEnabledFor(level):
#             self._log(level, message, args, **kwargs)
#     display.__name__ = n
#     setattr(logging.Logger, n, display)
#     logging._levelToName[level] = N
#     logging._nameToLevel[N] = level
#     logging.addLogLevel = addLogLevel


addLogLevel('trace', 1)

LOG_COLORS = {
    logging.TRACE: Fore.LIGHTBLACK_EX,
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
            if new_record.levelno == 1:  # TRACE - MSG colored
                new_record.msg = "{color_begin}{msg}{color_end}".format(
                    msg=new_record.msg,
                    color_begin=LOG_COLORS[new_record.levelno],
                    color_end=colorama.Style.RESET_ALL,
                )
        # now we can let standart formatting take care of the rest
        return super(ColorFormatter, self).format(new_record, *args, **kwargs)


class NoColorFormatter(logging.Formatter):
    """More info: https://stackoverflow.com/a/14693789/4574809."""
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
        console.setLevel(logging.TRACE)
        fmt = ColorFormatter('[%(levelname)s] %(message)s (%(pathname)s:%(lineno)s)')
    elif args.v == 2:
        console.setLevel(logging.DEBUG)
        fmt = ColorFormatter('[%(levelname)s] %(message)s (%(filename)s:%(lineno)s)')
    elif args.v == 1:
        console.setLevel(logging.DEBUG)
        fmt = ColorFormatter('[%(levelname)s] %(message)s')
    else:
        console.setLevel(logging.INFO)
        fmt = ColorFormatter('%(message)s')
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
    selected = utl.select_repo_from_list(args.session, SERVER, args.repository, args.username,
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

    # Load deploy.conf from project root directory
    log.debug(f"Checking for 'deploy.conf'")
    app_conf_filepath = tmp_dir / 'deploy.conf'
    # app_conf_filepath = Path('/ST/Evektor/UZIV/JVERNER/PROJEKTY/GIT/jverner/dochazka2/deploy.conf')
    ignore_venv = True

    log.debug(f"'{app_conf_filepath}' found. Loading config.")
    app_conf = app_conf_params(app_conf_filepath)
    if app_conf:
        log.info("========== deploy.conf parameters ==========")
        log.info(f"  Program framework:      {app_conf.framework}")
        log.info(f"  Make these as links:    {app_conf.links}")
        log.info(f"  Make these executable:  {app_conf.executables}")

        log.info(f"  Create venv:            {app_conf.create_venv}")
        log.info(f"  Venv folder name:       {app_conf.venv_name}")
        log.info(f"  Main script file:       {app_conf.main_file}")
        log.info(f"  LD_LIBRARY path:        {app_conf.ld_lib}")
        log.info("========== deploy.conf parameters ==========")

    # Ask user if he's certain to deploy
    log.info(f"Deploying {BYel}{url}{RCol} [{BRed}{args.branch}{RCol}] into {BYel}{target_dir}{RCol}")
    ask_confirm(f"Are you SURE?")

    # Make all files in root folder non-executable
    log.debug(f"Changing permissions for all files in '{tmp_dir}' to 664")
    # for item in tmp_dir.glob('**/*'):  # recursive search
    for item in tmp_dir.iterdir():  # current dir
        item: Path
        if not item.is_file():
            continue
        os.chmod(item, 0o664)

    # Make certain files executable
    for file in app_conf.executables:
        exe_file = tmp_dir / file
        if not exe_file.exists():
            log.warning(f"File '{exe_file}' does not exist. Check your config in 'deploy.conf'.")
            continue
        log.debug(f"Making '{exe_file}' executable... Permissions: 774")
        os.chmod(exe_file, 0o774)

    raise SystemExit

    if app_conf_filepath.exists():
        # log.debug(f"'{app_conf_filepath}' found. Loading config.")
        # app_conf = configparser.ConfigParser(allow_no_value=True)
        # app_conf.read(app_conf_filepath)

        src_requirements = tmp_dir / 'requirements.txt'
        if src_requirements.exists():
            dst_requirements = target_dir / 'requirements.txt'
            # Check if requirements.txt / deploy.conf are different
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

    # Case deploy.conf file was not found in project
    else:
        log.info(f"'{app_conf_filepath}' not found... Ignoring making executables, symlinks, ...")
        log.info(f"To get a deploy.conf.template, use 'eve-git template deploy.conf'")

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
    log.info(f"Connecting remote repository with this one (local)")
    if not is_git_repo(CURDIR):
        msg = f"Current location is not git repository: '{CURDIR.resolve()}'"
        log.critical(msg)
        raise Exception(msg)

    selected = select_repo_from_list(
        session=args.session,
        server=SERVER,
        repository=args.repository,
        question="Select repo to connect to: ",
    )
    log.debug(f"selected: {selected}")

    check_user_repo_exist(SERVER, selected.repository, selected.username, args.session)

    new_url = f'{SERVER}/{selected.username}/{selected.repository}'
    log.info(f"Connecting '{new_url}'")

    repo = Repo(CURDIR)

    # Case repo is missing remote, add 'gitea'
    if len(repo.remotes) == 0:
        repo.create_remote('gitea', new_url)
        log.info(f"Done (Created new 'gitea' remote)")
        return

    # Case repo has already some remotes. Go through them, if any 'gitea', ask for rewrite. Add otherwise.
    for remote in repo.remotes:
        if remote.name != 'gitea':
            continue
        log.warning(f"'gitea' remote already exists: {remote.url}")
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
        log.debug(f"answers: {answers}")

        if answers.get('continue'):
            remote.set_url(f'{new_url}')
            log.info(f"Remote 'gitea' changed from '{remote.url}' --> '{new_url}'")
            return
        else:
            log.info("Modifying url canceled.")
            raise SystemExit

    log.debug(f"Neither of the repositories was named 'gitea', adding a new one.")
    repo.create_remote('gitea', new_url)
    log.info(f"Done (Added new 'gitea' remote)")
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

    log.debug(f"answers: {answers}")

    args.organization = answers.get('organization')
    args.description = answers.get('description')
    args.fullname = answers.get('fullname')
    args.visibility = answers.get('visibility')

    log.debug(f"args.reponame: {args.organization}")
    log.debug(f"args.description: {args.description}")
    log.debug(f"args.fullname: {args.fullname}")
    log.debug(f"args.visibility: {args.visibility}")

    repo_data = {
        "description": args.description,
        "full_name": args.fullname,
        "repo_admin_change_team_access": True,
        "username": args.organization,  # THIS is Organization name
        "visibility": args.visibility,
    }
    log.debug(f"repo_data: {repo_data}")

    # Create organization
    res = args.session.post(url=f"{SERVER}/api/v1/orgs", json=repo_data)
    log.debug(f"res: {res}")

    # Viable responses
    if res.status_code == 401:
        msg = f"Something went wrong. Check your GITEA_TOKEN or internet connection."
        log.critical(msg)
        raise Exception(msg)

    elif res.status_code == 422:
        msg = f"Repository '{args.organization}' with the same name already exists."
        log.critical(msg)
        raise Exception(msg)

    elif res.status_code == 422:
        msg = f"Validation Error... Can't create repository with this name. Details bellow."
        log.critical(msg)
        msg += f"\n{json.loads(res.content)}"
        raise Exception(msg)

    elif res.status_code != 201:
        msg = f"Unknown error when trying to create new organization. Status_code: {res.status_code}"
        log.critical(msg)
        raise Exception(msg)

    log.info(f"Done. Organization created.")

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

    log.debug(f"answers: {answers}")

    args.reponame = answers.get('reponame')
    args.description = answers.get('description')
    args.username = answers.get('username')

    log.debug(f"args.reponame: {args.reponame}")
    log.debug(f"args.description: {args.description}")
    log.debug(f"args.username: {args.username}")

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

    log.debug(f"repo_data: {repo_data}")

    if args.username == getpass.getuser():
        # Creating new repo as normal user
        url = f"{SERVER}/api/v1/user/repos"
    else:
        # User specified different user/org. Only users with admin right can create repos anywhere
        log.debug(f"Using admin args.username: {args.username}")
        url = f"{SERVER}/api/v1/admin/users/{args.username}/repos"

    log.debug(f"url: {url}")

    # Post the repo
    res = args.session.post(url=url, json=repo_data)
    log.debug(f"res: {res}")

    # Viable responses
    if res.status_code == 401:
        msg = f"Unauthorized... Missing, wrong or weak (non-admin) GITEA_TOKEN..."
        log.critical(msg)
        raise Exception(msg)

    elif res.status_code == 403:
        msg = (f"Status code: {res.status_code}. Something wrong with GITEA_TOKEN. "
               "Using admin-command with non-admin token?")
        log.critical(msg)
        raise Exception(msg)

    elif res.status_code == 409:
        msg = f"Repository '{args.reponame}' under '{args.username}' already exists."
        log.critical(msg)
        raise Exception(msg)

    elif res.status_code == 422:
        msg = f"Validation Error... Can't create repository with this name. Details bellow."
        log.critical(msg)
        msg += f"\n{res.json()}"
        raise Exception(msg)

    elif res.status_code != 201:
        msg = f"Something went wrong. Don't know what. Status_code: {res.status_code}"
        log.critical(msg)
        raise Exception(msg)

    url = f"{SERVER}/{args.username}/{args.reponame}"
    log.info(f"Remote Repository created in '{url}'")

    answer = input("Clone into current folder? [Y/n]: ")
    if answer.lower() in ['y', 'yes']:
        target_path = Path(CURDIR.resolve() / args.reponame).resolve()
        log.debug(f"target_path: {target_path}")
        log.debug(f"url: {url}")
        Repo.clone_from(url=url, to_path=target_path, branch='master', progress=Progress())

    log.info(f"DONE")
    return 0


def transfer_repo(args):
    """To transfer repo to different user/organization."""
    # TODO zkontrolovat user/reponame/targetname

    if not args.repository:
        log.debug(f"User didn't specify <repository>")

        selected = select_repo_from_list(args.session, SERVER, args.repository, "Select repo to transfer: ")
        log.debug(f"selected.repository: {selected.repository}")

        args.repository = selected.repository
        args.username = selected.username

    if not args.target:
        log.debug(f"User didn't specify <target>")

        selected = select_org_from_list(args.session, SERVER, "Select Organization")
        log.debug(f"selected.repository: {selected.repository}")

        args.target = selected.organization

    else:
        if not check_org_exist(SERVER, args.target, args.session):
            log.critical("Entered org/user not found. Exitting app")
            raise SystemExit()

    # # Check if 'user' and combination of 'user/repo' exist
    # check_user_repo_exist(SERVER, args.repository, args.username, args.session)

    # Everything OK, transfer the repository
    log.info(f"Transfering '{SERVER}/api/v1/repos/{args.username}/{args.repository}/transfer'")
    url = f"{SERVER}/api/v1/repos/{args.username}/{args.repository}/transfer"
    repo_data = {
        "new_owner": args.target,
        # "team_ids": [
        #     0
        # ]
    }
    res = args.session.post(url=url, json=repo_data)
    log.debug(f"res: {res}")
    return 0


def list_org(args):
    """Function for listing organizations."""
    log.debug(f"Listing organizations")

    tbl = get_org_list_as_table(args.session, SERVER)
    print(tbl)

    return


def list_repo(args):
    """Function for listing directories."""
    log.debug(f"Listing repository.")
    tbl = utl.get_repo_list_as_table(args.session, SERVER, args.repository, args.username)
    print(tbl)
    return


def clone_repo(args):
    """Clone repo into current directory."""
    log.debug(f"Cloning repository.")

    if not args.username:
        log.debug(f"User didn't specify <username>")

        selected = select_repo_from_list(args.session, SERVER, args.repository, "Select repo to clone: ")
        log.debug(f"selected.repository: {selected.repository}")
        log.debug(f"selected.username: {selected.username}")

        args.repository = selected.repository
        args.username = selected.username

    # Check if 'user' and combination of 'user/repo' exist
    check_user_repo_exist(SERVER, args.repository, args.username, args.session)

    # Everything OK, clone the repository
    log.info(f"Cloning '{SERVER}/{args.username}/{args.repository}'")

    target_dir = CURDIR / args.repository
    if target_dir.exists():
        msg = (f"Folder with the same name '{args.repository}' already in target dir: '{target_dir.resolve()}'")
        log.critical(msg)
        raise Exception(msg)

    repo = Repo.clone_from(
        url=f"{SERVER}/{args.username}/{args.repository}",
        to_path=CURDIR / args.repository,
        progress=Progress())
    log.debug(f"repo: {repo}")

    log.info(f"DONE")


def remove_repo(args):
    """Remove repository from gitea"""
    log.debug(f"Removing repo.")

    if not args.username:
        log.debug(f"User didn't specify <username>")
        selected = select_repo_from_list(args.session, SERVER, args.repository, "Select repo to remove: ")

        args.repository = selected.repository
        args.username = selected.username

    check_user_repo_exist(SERVER, args.repository, args.username, args.session)

    log.info(f"You are about to REMOVE repository: '{SERVER}/{args.username}/{args.repository}'")
    ask_confirm("Are you SURE you want to do this??? This operation CANNOT be undone!!!")
    ask_confirm_data(f"Enter the repository NAME as confirmation [{args.repository}]", args.repository)

    # DELETE the repo
    log.info(f"Removing '{SERVER}/{args.username}/{args.repository}'")
    res = args.session.delete(url=f"{SERVER}/api/v1/repos/{args.username}/{args.repository}")
    log.debug(f"res: {res}")

    # Case when something is wrong with GITEA_TOKEN...
    if res.status_code == 401:
        msg = f"Unauthorized... Something wrong with you GITEA_TOKEN..."
        log.critical(msg)
        raise Exception(msg)

    # Case when normal user tries to remove repository of another user and doesn't have authorization for that
    elif res.status_code == 403:
        msg = f"Forbidden... You don't have enough permissinons to delete this repository..."
        log.critical(msg)
        raise Exception(msg)

    log.info(f"DONE")

    return 0


def remove_org(args):
    """Remove organization from gitea"""
    log.debug(f"Removing oranization")

    org_found = check_org_exist(server=SERVER, organization=args.organization, session=args.session)
    log.debug(f"org_found: {org_found}")

    if not org_found:
        log.debug(f"User didn't specify <organization>")

        selected = select_org_from_list(session=args.session, server=SERVER, question="Select org to remove: ")
        log.debug(f"selected.organization: {selected.organization}")

        args.organization = selected.ororganizationganization

    # Everything OK, delete the organization
    log.info(f"You are about to REMOVE organization: '{SERVER}/{args.organization}'")

    ask_confirm('Are you SURE you want to do this??? This operation CANNOT be undone.')
    ask_confirm_data(f'Enter the organization NAME as confirmation [{args.organization}]',
                     comp_str=args.organization)

    log.info(f"Deleting organization '{args.organization}'")

    url = f"{SERVER}/api/v1/orgs/{args.organization}"
    log.debug(f"url: {url}")

    res = args.session.delete(url)
    log.debug(f"res: {res}")

    if res.status_code == 401:
        msg = f"Unauthorized. You don't have enough rights to delete this repository."
        log.critical(msg)
        raise Exception(msg)

    elif res.status_code == 403:
        msg = f"Status code: {res.status_code}. Can't remove organization that is not mine. Or other unknown problem."
        log.critical(msg)
        raise Exception(msg)

    elif res.status_code == 500:
        msg = f"This organization still owns one or more repositories; delete or transfer them first."
        log.critical(msg)
        raise Exception(msg)

    if res.status_code != 204:
        msg = f"Unknown error for org: '{args.organization}'. Status code: {res.status_code}"
        log.critical(msg)
        raise Exception(msg)

    log.info(f"Done. Organization removed.")
    return 0


def edit_desc(args):
    """Edit description in repo."""
    log.debug(f"Editing repository.")

    if not args.username:
        log.debug(f"User didn't specify <username>")

        selected = select_repo_from_list(args.session, SERVER, args.repository, "Select repo to edit: ")
        log.debug(f"selected.repository: {selected.repository}")
        log.debug(f"selected.username: {selected.username}")
        log.debug(f"selected.description: {selected.description}")

        args.repository = selected.repository
        args.username = selected.username
        args.description = selected.description

    check_user_repo_exist(SERVER, args.repository, args.username, args.session)

    repo = args.session.get(f"{SERVER}/api/v1/repos/{args.username}/{args.repository}")
    args.description = repo.json().get('description')

    # Everything OK, edit the repository
    log.info(f"Editing repository: '{SERVER}/{args.username}/{args.repository}'")

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

    log.debug(f"answers: {answers}")

    args.description = answers.get('description')
    repo_data = {'description': args.description}
    res = args.session.patch(url=f"{SERVER}/api/v1/repos/{args.username}/{args.repository}", json=repo_data)

    # Case when normal user tries to remove repository of another user and doesn't have authorization for that
    if res.status_code == 403:
        msg = f"Forbidden... APIForbiddenError is a forbidden error response. Not authorized (weak GITEA_TOKEN)"
        log.critical(msg)
        raise Exception(msg)

    # Case when something is wrong with GITEA_TOKEN...
    elif res.status_code == 422:
        msg = f"APIValidationError is error format response related to input validation"
        log.critical(msg)
        raise Exception(msg)

    # Other cases should not come
    if res.status_code != 200:
        log.debug(f"args.session.headers: {args.session.headers}")
        msg = f"Status code: {res.status_code}"
        log.critical(msg)
        raise Exception(msg)

    log.info(f"DONE")

    return


def update_token(args):
    """Update GITEA_TOKEN in $HOME/eve-git.settings config file."""
    settings_file = Path.home() / 'eve-git.settings'
    # Don't know how to save the config back with comments too...
    config = configparser.ConfigParser()

    if args.token == '':
        if not settings_file.exists():
            log.info(f"Settings file '{settings_file}' does not exists. Use: --token YOUR_API_KEY")
            return

        config.read(settings_file)
        current_token = config['server']['gitea_token']
        log.info(f"Current Gitea token: {current_token}")
        return

    if not settings_file.exists():
        log.info(f"Creating new {settings_file} with Gitea token: {args.token}")
        config['server'] = {'gitea_token': args.token}
        config['app'] = {'debug': False}
    else:
        log.debug(f"Updating value: 'config[server] = {{gitea_token = {args.token}}}'")
        config.read(settings_file)
        current_token = config['server']['gitea_token']
        config['server'] = {'gitea_token': args.token}
        ask_confirm(f"Replace current Gitea token '{current_token}' --> '{args.token}'?")

    log.debug(f"Writing config into: {settings_file.resolve()}")

    with open(settings_file, 'w') as f:
        config.write(f)


def templates(args):
    templates_dir = SCRIPTDIR / 'templates'
    log.debug(f"templates_dir: {templates_dir.resolve()}")
    selected = select_files_from_list(
        directory=templates_dir, question="Select template file to download into current directory")
    log.debug(f"selected: {selected}")

    target_filepath = CURDIR / selected.filename
    if target_filepath.exists():
        answer = ask_confirm(f"Warning: {target_filepath.name} already exists. Overwrite???")
        if not answer:
            log.info(f"File {target_filepath.name} was NOT copied.")
            return
    # shutil.copy(selected.filepath, CURDIR)
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

    log.debug("--------------------------------------------------------------------------------------------")
    log.debug(f"args: {args}")
    log.debug("--------------------------------------------------------------------------------------------")

    # In case of no input, show help
    if len(sys.argv) <= 1:
        log.error(f"No arguments... Showing help.")
        print()
        parser.print_help()
        raise SystemExit

    if args.token is not None:
        update_token(args)
        raise SystemExit

    # React on user inputted command/arguments
    args.func(args)
