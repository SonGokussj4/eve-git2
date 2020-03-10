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
# import fileinput
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
    print(f"[ INFO ] Deploying...")

    lineno(f"args.repository: {args.repository}")
    lineno(f"args.username: {args.username}")
    lineno(f"args.branch: {args.branch}")

    selected = select_repo_from_list(args.session, SERVER, args.repository, args.username,
                                     'Select repository to deploy')

    args.repository = selected.repository
    args.username = selected.username

    url = f"{SERVER}/{args.username}/{args.repository}"
    lineno(f"url: {url}")

    check_user_repo_exist(SERVER, args.repository, args.username, args.session)
    if not remote_repo_branch_exist(url=url, branch=args.branch):
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Remote branch [{BRed}{args.branch}{RCol}] does not exist.'"
        raise Exception(msg)

    # Local and Remove directory
    tmp_dir = Path('/tmp') / args.repository
    target_dir = SKRIPTY_DIR / args.repository

    # Remove existing /tmp/{repository} folder
    if tmp_dir.exists():
        print(f"[ {Yel}WARNING{RCol} ] '{tmp_dir}' already exists. Removing.")
        removed = remove_dir_tree(tmp_dir)
        lineno(f"removed: {removed}")

    print(f"[ INFO ] Clonning to '{tmp_dir}'...")

    tmp_repo = Repo.clone_from(url=url, to_path=tmp_dir, branch=args.branch, depth=1, progress=Progress())

    # Remove .git folder in /tmp repo
    print(f"[ INFO ] Removing '.git' folder")
    lineno(f"Removing '{tmp_repo.git_dir}'")
    remove_dir_tree(tmp_repo.git_dir)

    # Load repo.config from project root directory
    lineno(f"Checking for 'repo.config'")
    repo_cfg_filepath = tmp_dir / 'repo.config'
    ignore_venv = True

    if repo_cfg_filepath.exists():
        lineno(f"'{repo_cfg_filepath}' found. Loading config.")
        repo_cfg = configparser.ConfigParser(allow_no_value=True)
        repo_cfg.read(repo_cfg_filepath)

        # Make files executable
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

        # Check if requirements.txt / repo.config are different
        src_requirements = tmp_dir / 'requirements.txt'
        dst_requirements = target_dir / 'requirements.txt'
        ignore_venv = requirements_similar(src_requirements, dst_requirements)
        lineno(f"ignore_venv: {ignore_venv}")

        # Requirements.txt files are different. Create virtual environment
        if not ignore_venv:
            framework = repo_cfg['Repo']['Framework']
            print(f"[ INFO ] Making virtual environment...")
            cmd = f'{framework} -m venv {tmp_dir}/.env'
            lineno(f"cmd: '{cmd}'")
            os.system(cmd)

            # Upgrade pip
            print(f"[ INFO ] Upgrading Pip")
            cmd = f'{tmp_dir}/.env/bin/pip install --upgrade pip'
            lineno(f"cmd: '{cmd}'")
            os.system(cmd)

            # Pip install
            print(f"[ INFO ] Running Pip install")
            cmd = f'{tmp_dir}/.env/bin/pip install -r {tmp_dir}/requirements.txt'
            lineno(f"cmd: '{cmd}'")
            os.system(cmd)

        # Replace venv paths with sed to target project path
        print(f"[ INFO ] Changing venv paths inside files: '{tmp_dir}/.env' --> '{target_dir}/.env'")
        cmd = f'find {tmp_dir} -exec sed -i s@{tmp_dir}/.env@{target_dir}/.env@g {{}} \\; 2>/dev/null'
        lineno(f"cmd: '{cmd}'")
        os.system(cmd)

        # Check if <reponame> already exists in /expSW/SOFTWARE/skripty/<reponame>
        if not target_dir.exists():
            cmd = f'ssh {SKRIPTY_SERVER} "mkdir {target_dir}"'
            os.system(cmd)
            lineno(f"{target_dir} created.")

        # Make symbolic link(s)
        for key, val in repo_cfg.items('Link'):
            src_filepath = target_dir / key
            dst_filepath = SKRIPTY_EXE / val
            print(f"[ INFO ] Linking '{src_filepath}' --> '{dst_filepath}'")
            # make_symbolic_link(src_filepath, dst_filepath)
            if os.name != 'nt':
                cmd = f'ssh {SKRIPTY_SERVER} "ln -fs {src_filepath} {dst_filepath}"'
            else:
                cmd = f'cmd /c "mklink {link_dst} {link_src}"'
                # cmd = f'''powershell.exe new-item -ItemType SymbolicLink -path {SKRIPTY_EXE} -name {val} -value {link_src}'''  # powershell
            lineno(f"cmd: '{cmd}'")
            os.system(cmd)

    # Case repo.config file was not found in project
    else:
        print(f"[ INFO ] '{repo_cfg_filepath}' not found... Ignoring making executables, symlinks, ...")
        print(f"[ INFO ] To create a repo.config.template, use 'eve-git template repo.config'")

    # Rsync all the data
    lineno(f"ignore_venv: '{ignore_venv}'")

    print(f"[ INFO ] Deploying {BYel}{url}{RCol} [{BRed}{args.branch}{RCol}] into {BYel}{target_dir}{RCol}")
    ask_confirm(f"Are you SURE?")

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

    # Cleanup
    remove_dir_tree(tmp_dir)
    lineno(f"'{tmp_dir}' removed")

    print(f"[ INFO ] Deployment completed.")
    return 0


@traced
@logged
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


@traced
@logged
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


@traced
@logged
def list_org(args):
    """Function for listing organizations."""
    lineno(f"Listing organizations")

    tbl = get_org_list_as_table(args.session, SERVER)
    print(tbl)

    return


@traced
@logged
def list_repo(args):
    """Function for listing directories."""
    lineno(f"Listing repository.")
    tbl = get_repo_list_as_table(args.session, SERVER, args.repository, args.username)
    print(tbl)
    return


@traced
@logged
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


@traced
@logged
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


@traced
@logged
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


@traced
@logged
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

    return 0


def update_token(args):
    """Update GITEA_TOKEN in $HOME/eve-git.settings config file."""
    settings_file = Path.home() / 'eve-git.settings'
    # Don't know how to save the config back with comments too...
    config = configparser.ConfigParser()

    if not settings_file.exists():
        lineno(f"Creating new config with: {args.update_token}")
        config['server'] = {'gitea_token': args.update_token}
        config['app'] = {'debug': True}
    else:
        lineno(f"Updating value: 'config[server] = {{gitea_token = {args.update_token}}}'")
        config.read(settings_file)
        old_val = config['server']['gitea_token']
        config['server'] = {'gitea_token': args.update_token}

    ask_confirm(f"Are you sure you want to replace '{old_val}' with '{args.update_token}'?")
    lineno(f"Writing config into: {settings_file.resolve()}")

    with open(settings_file, 'w') as f:
        config.write(f)


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

    lineno("--------------------------------------------------------------------------------")
    lineno(f"args: {args}")
    lineno("--------------------------------------------------------------------------------")

    # In case of no input, show help
    # if not any(vars(args).values()):
    if not len(sys.argv) > 1:
        print(f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] No arguments... Showing help.")
        print()
        parser.print_help()
        sys.exit()

    if args.update_token:
        update_token(args)
        raise SystemExit

    # React on user inputted command/arguments
    args.func(args)
