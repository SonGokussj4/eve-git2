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
import filecmp
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
import click  # https://pypi.org/project/click/
import requests
from git import Repo, exc  # https://gitpython.readthedocs.io/en/stable/tutorial.html#tutorial-label
from columnar import columnar  # https://pypi.org/project/Columnar/
from colorama import init, Fore, Back, Style
from PyInquirer import style_from_dict, Token, prompt, Separator  # https://pypi.org/project/PyInquirer/
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
        format="[ %(levelname)s ] %(funcName)s: %(message)s")


def lineno(msg=None):
    if not msg:
        return sys._getframe().f_back.f_lineno
    print(f"{lineno(): >4}.[ {BBla}Debug{RCol} ] {sys._getframe().f_back.f_lineno}: {msg if msg is not None else ''}")


@traced
@logged
def deploy(args):
    print(f"[ {BWhi}INFO{RCol}  ] Deploying... args: '{args}'")
    # User specified both arguments: --clone <reponame> <username>
    if len(args) >= 2:
        branch = 'master'
        if len(args) == 3:
            reponame, username, branch = args
        else:
            reponame, username = args

        # ==================================================
        # =           CHECK IF <username> EXISTS           =
        # ==================================================
        # Does the username exist?
        res = requests.get(f"{SERVER}/api/v1/users/{username}")
        if res.status_code != 200:
            raise Exception(f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] User '{username}' doesn't exist!")
        print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] Checking if <username> exists: {res.ok}")

        # ================================================================
        # =           CHECK FOR <repository> AND <user> EXISTS           =
        # ================================================================
        # Does the <repository> of <user> exist?
        res = requests.get(f"{SERVER}/api/v1/repos/{username}/{reponame}")
        if res.status_code != 200:
            print(f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Repository '{SERVER}/{username}/{reponame}' does not exist.")
            # sys.exit(1)
            raise Exception(f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Repository '{SERVER}/{username}/{reponame}' does not exist.")
        print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] Checking if <username>/<reponame> exists: {res.ok}")

        # Everything OK, clone the repository to /tmp/<reponame>
        tmp_dir = Path('/tmp') / reponame
        target_dir = SKRIPTY_DIR / reponame

        # ==============================================================
        # =           REMOVE EXISTING /tmp/{reponame} FOLDER           =
        # ==============================================================
        if tmp_dir.exists():
            print(f"[ {Yel}WARNING{RCol} ] '{tmp_dir}' already exists. Removing.")
            # res = shutil.rmtree(tmp_dir, ignore_errors=True)
            try:
                res = shutil.rmtree(tmp_dir)
            except Exception as e:
                print(f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Can't use shutil.rmtree(). Error msg bellow. Trying 'rmdir /S /Q'")
                print(f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] +-- Message: '{e}'")
                os.system(f'rmdir /S /Q "{tmp_dir}"')

        # ================================================
        # =           CLONE GIT REPO INTO /tmp           =
        # ================================================
        print(f"[ {BWhi}INFO{RCol}  ] Clonning to '{tmp_dir}' DONE")
        Repo.clone_from(url=f"{SERVER}/{username}/{reponame}",
                        to_path=tmp_dir.resolve(),
                        branch=branch,
                        depth=1,
                        progress=Progress())

        # ==========================================
        # =           REMOVE .GIT FOLDER           =
        # ==========================================
        print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] Removing '.git' folder")
        git_folder = tmp_dir / '.git'
        try:
            res = shutil.rmtree(git_folder)
        except Exception as e:
            print(f"[ {BYel}WARNING{RCol} ] Can't use shutil.rmtree(). Error msg bellow. Trying 'rmdir /S /Q'")
            print(f"[ {BYel}WARNING{RCol} ] +-- Message: '{e}'")
            os.system(f'rmdir /S /Q "{git_folder}"')

        # ========================================
        # =           LOAD REPO.CONFIG           =
        # ========================================
        print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] Checking 'repo.config'")
        repoini = tmp_dir / 'repo.config'
        # repoini = Path('/ST/Evektor/UZIV/JVERNER/PROJEKTY/GIT/jverner/dochazka2/repo.config')
        if not repoini.exists():
            print(f"[ {BWhi}INFO{RCol}  ] '{repoini}' not found... Ignoring making executables, symlinks, ...")
            print(f"[ {BWhi}INFO{RCol}  ] To create a repo.config.template, use 'eve-git template repo.config'")
        else:
            print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] '{repoini}' found. Loading config.")
            con = configparser.ConfigParser(allow_no_value=True)
            con.read(repoini)
            # print(f">>> con['repo']['framework']: {con['repo']['framework']}")

            # =============================================
            # =           MAKE FILES EXECUTABLE           =
            # =============================================
            print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] Changing all FILE permissions in '{tmp_dir}' to 664")
            for item in tmp_dir.iterdir():
                item: Path
                if not item.is_file():
                    continue
                os.chmod(item, 0o664)

            for key, val in con.items('Executable'):
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
            dst_requirements = target_dir / 'requirements.txt'

            venv_update = False
            if src_requirements.exists():
                print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] '{src_requirements}' exists.")
                dst_requirements = target_dir / 'requirements.txt'
                if not dst_requirements.exists():
                    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] '{dst_requirements}' does not exists.")
                    print(f"[ {BWhi}INFO{RCol}  ] Missing '{dst_requirements}' --> Installing '.env' and all 'PIP libs'.")
                    venv_update = True
                else:
                    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] '{dst_requirements}' exists.")
                    similar = filecmp.cmp(src_requirements, dst_requirements)
                    if similar:
                        print(f"[ {BWhi}INFO{RCol}  ] '{src_requirements}' and '{dst_requirements}' are the same. No need to update .env")
                    else:
                        print(f"[ {BWhi}INFO{RCol}  ] '{src_requirements}' and '{dst_requirements}' are different.")
                        print(f"[ {BWhi}INFO{RCol}  ] Venv '.env' would be created and PIP libraries installed/updated.")
                        venv_update = True

            # ==================================================
            # =           CREATE VIRTUAL ENVIRONMENT           =
            # ==================================================
            if venv_update:
                framework = con['Repo']['Framework']
                print(f"[ {BWhi}INFO{RCol}  ] Making virtual environment...")
                cmd = f'{framework} -m venv {tmp_dir}/.env'
                print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] cmd: '{cmd}'")
                os.system(cmd)

                # ===================================
                # =           UPGRADE PIP           =
                # ===================================
                print(f"[ {BWhi}INFO{RCol}  ] Upgrading Pip")
                cmd = f'{tmp_dir}/.env/bin/pip install --upgrade pip'
                os.system(cmd)

                # ===================================
                # =           PIP INSTALL           =
                # ===================================
                print(f"[ {BWhi}INFO{RCol}  ] Running Pip install")
                cmd = f'{tmp_dir}/.env/bin/pip install -r {tmp_dir}/requirements.txt'
                os.system(cmd)

            # =========================================
            # =           CHANGE VENV PATHS           =
            # =========================================
            target_dir = SKRIPTY_DIR / reponame
            print(f"[ {BWhi}INFO{RCol}  ] Changing venv paths '{tmp_dir}/.env' --> '{target_dir}/.env'")
            cmd = f'find {tmp_dir} -exec sed -i s@{tmp_dir}/.env@{target_dir}/.env@g {{}} \\; 2>/dev/null'
            print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] cmd: '{cmd}'")
            os.system(cmd)

            # ===================================================
            # =           REPLACE MAIN_FILE IN run.sh           =
            # ===================================================
            runsh_file = tmp_dir / 'run.sh'
            print(f"[ {BWhi}INFO{RCol}  ] In '{runsh_file}' ... Replacing 'MAIN_FILE_PLACEHOLDER' --> '{con['Repo']['main_file']}'")
            with fileinput.FileInput(runsh_file, inplace=True) as f:
                for line in f:
                    print(line.replace('MAIN_FILE_PLACEHOLDER', con['Repo']['main_file']), end='')

            # =====================================================
            # =           CREATE REMOTE reponame FOLDER           =
            # =====================================================
            # Check if <reponame> already exists in /expSW/SOFTWARE/skripty/<reponame>
            if not target_dir.exists():
                cmd = f'ssh {SKRIPTY_SERVER} "mkdir {target_dir}"'
                os.system(cmd)
                print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] {target_dir} created.")

            # ==========================================
            # =           RSYNC ALL THE DATA           =
            # ==========================================
            # Rsync all the data
            env_dir = tmp_dir / '.env'
            if env_dir.exists():
                # cmd = (f'rsync -avh --delete --progress {tmp_dir} {SKRIPTY_SERVER}:{target_dir.parent}')
                cmd = (f'rsync -ah --delete {tmp_dir} {SKRIPTY_SERVER}:{target_dir.parent}')
            else:
                # cmd = (f'rsync -avh --delete --exclude-from={SCRIPTDIR}/rsync-directory-exclusions.txt '
                cmd = (f'rsync -ah --delete --exclude-from={SCRIPTDIR}/rsync-directory-exclusions.txt '
                       f'{tmp_dir} {SKRIPTY_SERVER}:{target_dir.parent}')
            print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] Rsync cmd: '{cmd}'")
            res = os.system(cmd)

            # =============================================
            # =           MAKE SYMBOLIC LINK(S)           =
            # =============================================
            for key, val in con.items('Link'):
                src_filepath = target_dir / key
                link_filpath = SKRIPTY_EXE / val
                print(f"[ {BWhi}INFO{RCol}  ] Linking '{src_filepath}' --> '{link_filpath}'")
                cmd = f'ssh {SKRIPTY_SERVER} "ln -fs {src_filepath} {link_filpath}"'
                print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] cmd: '{cmd}'")
                os.system(cmd)

        # ===============================
        # =           CLEANUP           =
        # ===============================
        shutil.rmtree(tmp_dir, ignore_errors=True)
        print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] '{tmp_dir}' removed")

        # ==============================
        # =           FINISH           =
        # ==============================

        print(f"[ {BWhi}INFO{RCol}  ] Deployment completed.")

        # ========================================
        # =           WINDOWS THINGIES           =
        # ========================================
        # # Rsync all the things
        # # --delete ... for files that are not present in the current...
        # cmd = f'rsync -avh --progress --remove-source-files {tmp_dir}/ {SKRIPTY_SERVER}{SKRIPTY_DIR}/{reponame}'
        # print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] shlex.split(cmd): {shlex.split(cmd)}")
        # try:
        #     res = sp.call(shlex.split(cmd))
        #     if res != 0:
        #         print(f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Something went wrong with rsync...")
        #         return 1
        # except Exception as e:
        #     print(f"[ WARNING ] rsync failed... Trying shutil.copy. Error msg bellow")
        #     print(f"[ WARNING ] +-- Message: {e}")

        #     print(f"[ INFO ] Removing '{SKRIPTY_DIR}\\{reponame}'... ")
        #     os.system(f'rmdir /S /Q "{SKRIPTY_DIR}\\{reponame}"')

        #     print(f"[ INFO ] Copying '{tmp_dir}' --> '{SKRIPTY_DIR}\\{reponame}'")
        #     # dirs_exist_ok from Python3.8!!!
        #     res = shutil.copytree(tmp_dir, f'{SKRIPTY_DIR}\\{reponame}', dirs_exist_ok=True)

        # # Cleanup
        # print(f"[ INFO ] Cleanup. Removing '{tmp_dir}'")
        # try:
        #     res = shutil.rmtree(tmp_dir)
        # except Exception as e:
        #     print(f"[ WARNING ] Can't use shutil.rmtree(). Error msg bellow. Trying 'rmdir /S /Q'")
        #     print(f"[ WARNING ] +-- Message: '{e}'")
        #     os.system(f'rmdir /S /Q "{tmp_dir}"')

        # print("[ INFO ] Trying to load 'config.ini'")
        # # Load up 'config.ini'
        # config = configparser.ConfigParser(allow_no_value=True)
        # config_ini = SKRIPTY_DIR / reponame / 'config.ini'
        # res = config.read(config_ini)
        # if res:
        #     print("[ INFO ] Loading Key/Val pairs, creating links and executables.")
        #     # Make links
        #     for section in config.sections():
        #         for key, val in config[section].items():
        #             if section == 'link':
        #                 link_src = SKRIPTY_DIR / reponame / key  # /expSW/SOFTWARE/skripty/{reponame}/{exefile}
        #                 link_dst = SKRIPTY_EXE / val  # /expSw/SOFTWARE/bin/{linkname}
        #                 if os.name == 'nt':
        #                     print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] Doing: 'mklink {link_src} {link_dst}'")
        #                     cmd = f'cmd /c "mklink {link_dst} {link_src}"'  # cmd
        #                     # cmd = f'''powershell.exe new-item -ItemType SymbolicLink -path {SKRIPTY_EXE} -name {val} -value {link_src}'''  # powershell
        #                     print(f">>> cmd: {cmd}")
        #                     res = sp.call(cmd)
        #                     # print(f">>> res: {res}")
        #                 else:
        #                     print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] Doing: 'ln -s {link_src} {link_dst}'")
        #                     cmd = f'ln -s {link_src} {link_dst}'
        #                     print(f">>> cmd: {cmd}")
        #                     res = sp.call(shlex.split(cmd))
        #                 pass
        #             elif section == 'executable':
        #                 executable_file = SKRIPTY_DIR / reponame / key
        #                 print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] Doing: chmod +x {executable_file}")
        #                 pass
        # else:
        #     print('[ INFO ] config.ini not found. Ignoring.')

        # print("{lineno(): >4}.[ {BBla}DEBUG{RCol} ] config['other']['files'].strip().split(newline):", config['other']['files'].strip().split('\n'))
        # # Check the description for 'what to do with .executable files and so on...'
        # print(f'[ INFO ] DONE')

        return 0

    # User didn't specify <username>: --clone <reponame>
    elif len(args) == 1:
        reponame = args[0]
        res = requests.get(f"{SERVER}/api/v1/repos/search?q={reponame}&sort=created&order=desc")
        # print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] res: {res}")

        data = json.loads(res.content)

        # Check if there was a good response
        if not data.get('ok'):
            print(f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Shit... Data not acquired... {data}")
            return 1
        elif not data.get('data'):
            print(f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Search for repository '{reponame}' returned 0 results... Try something different.")
            return 1

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
            return 1
        elif not answer.isdigit():
            print(f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] What you entered is not a number... You have to write one of the IDs.")
            return 1

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

        print(f"[ INFO ] Deploying ID: {repo_id}")
        reponame, username = selected_repository[0][1], selected_repository[0][2]
        deploy([reponame, username])
        return 0

    # PYTHON
    # Pokud skript obsahuje testy, tak napred udelat TESTY a pokracovat jen v pripade, ze jsou zelene
    # mozna --ignore-tests
    #
    # BASH
    # Proste jen hodi na misto, smaze .git a udela link

    return 0


@traced
@logged
def create_org(args):
    """Function Description."""
    args.organization = ask_with_defaults('Organization name', defaults=args.organization)
    args.description = ask_with_defaults('Description', defaults=args.description)
    args.fullname = ask_with_defaults('Full Name', defaults=args.fullname)
    args.visibility = ask_with_defaults('Visibility (public|private)', defaults=args.visibility)

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
    args.reponame = ask_with_defaults('Repository name', defaults=args.reponame)
    args.description = ask_with_defaults('Description', defaults=args.description)

    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] args.reponame: {args.reponame}")
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] args.description: {args.description}")
    # log.debug(f"args.description: {args.description}")

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

    url = f"{SERVER}/api/v1/admin/orgs?access_token={GITEA_TOKEN}"
    print(f"[{lineno()}] {lineno(): >4}.[ {BBla}DEBUG{RCol} ] url: '{url}'")

    res = requests.get(url)
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
    headers = ('Organization', 'description')
    results = [[item['username'], item['description']] for item in data]
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

    res = requests.get(url)
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

        res = requests.get(f"{SERVER}/api/v1/repos/search?q={args.repository}&sort=created&order=desc")
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

        qstyle = style_from_dict({
            Token.Separator: '#cc5454',
            Token.QuestionMark: '#673ab7 bold',
            Token.Selected: '#cc5454 bold',
            Token.Pointer: '#673ab7 bold',
            Token.Instruction: '',
            Token.Answer: '#f44336 bold',
            Token.Question: 'bold',
        })

        questions = [{
            'type': 'list',
            'choices': choices,
            'pageSize': 50,
            'name': 'repo_id',
            'message': "Select repo to remove: ",
        }]

        answers = prompt(questions, style=qstyle)
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
    res = requests.get(f"{SERVER}/api/v1/users/{args.username}")
    if res.status_code != 200:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] User '{args.username}' doesn't exist!"
        raise Exception(msg)

    # Does the <repository> of <user> exist?
    res = requests.get(f"{SERVER}/api/v1/repos/{args.username}/{args.repository}")
    if res.status_code != 200:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Repository '{SERVER}/{args.username}/{args.repository}' does not exist."
        raise Exception(msg)

    # Everything OK, delete the repository
    print(f"[ {BWhi}INFO{RCol} ] You are about to REMOVE repository: '{SERVER}/{args.username}/{args.repository}'")
    answer = input(f"Are you SURE you want to do this??? This operation CANNOT be undone [y/N]: ")
    if answer.lower() not in ['y', 'yes']:
        print(f"[ {BWhi}INFO{RCol} ] Cancelling... Nothing removed.")
        return 0

    answer = input(f"Enter the repository NAME as confirmation [{args.repository}]: ")
    if not answer == args.repository:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Entered reponame '{answer}' is not the same as '{args.repository}'. Cancelling..."
        raise Exception(msg)

    print(f"[ {BWhi}INFO{RCol} ] Removing '{SERVER}/{args.username}/{args.repository}'")

    res = requests.delete(url=f"{SERVER}/api/v1/repos/{args.username}/{args.repository}?access_token={GITEA_TOKEN}")

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
        res = requests.get(f"{SERVER}/api/v1/admin/orgs?access_token={GITEA_TOKEN}")
        print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] res: {res}")

        data = json.loads(res.content)
        if not data:
            msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Search for organizations returned 0 results... Try something different."
            raise Exception(msg)

        headers = ('id', 'org', 'description')
        results = [[item['id'], item['username'], item['description']]
                   for item in data]
        tbl = columnar(results, headers, no_borders=True, wrap_max=0)
        # print(tbl)
        tbl_as_string = str(tbl).split('\n')

        # Ask for repo to remove
        choices = [Separator(f"\n   {tbl_as_string[1]}\n")]
        choices.extend([{'name': item, 'value': item.split()[0]} for item in tbl_as_string[3:-1]])
        choices.append(Separator('\n'))

        qstyle = style_from_dict({
            Token.Separator: '#cc5454',
            Token.QuestionMark: '#673ab7 bold',
            Token.Selected: '#cc5454 bold',
            Token.Pointer: '#673ab7 bold',
            Token.Instruction: '',
            Token.Answer: '#f44336 bold',
            Token.Question: 'bold',
        })

        questions = [{
            'type': 'list',
            'choices': choices,
            'pageSize': 50,
            'name': 'org_id',
            'message': "Select org to remove: ",
        }]

        answers = prompt(questions, style=qstyle)
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
    url = f"{SERVER}/api/v1/orgs/{args.organization}?access_token={GITEA_TOKEN}"
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] url: {url}")

    res = requests.get(url)
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] res.status_code: {res.status_code}")

    data = json.loads(res.content)
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] data: {data}")

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

    # TODO mam pocit, ze kdyz se smaze organizace, tak se jen repo v nich nekam premisti, zkusit
    if answer.lower() not in ['y', 'yes']:
        print(f"[ INFO ] Cancelling... Nothing removed.")
        return 0

    answer = input(f"Enter the organization NAME as confirmation [{args.organization}]: ")
    if not answer == args.organization:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Entered orgname '{answer}' is not the same as '{args.organization}'. Cancelling..."
        raise Exception(msg)

    print(f"[ INFO ] Deleting organization '{args.organization}'")
    res = requests.delete(f"{SERVER}/api/v1/orgs/{args.organization}?access_token={GITEA_TOKEN}")

    if res.status_code == 401:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Unauthorized. You don't have enough rights to delete this repository."
        raise Exception(msg)

    if res.status_code != 204:
        msg = f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] Unknown error for organization: '{args.organization}'"
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

        repo_data = {
            'description': description}

        res = requests.patch(url=f"{SERVER}/api/v1/repos/{username}/{reponame}?access_token={GITEA_TOKEN}",
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

    print("--------------------------------------------------------------------------------")
    print(f"{lineno(): >4}.[ {BBla}DEBUG{RCol} ] args: {args}")
    print("--------------------------------------------------------------------------------")

    # Initialize logger depending on the -v, -vv, -vvv arguments
    init_logging(args)

    # In case of no input, show help
    # if not any(vars(args).values()):
    if not len(sys.argv) > 1:
        print(f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] No arguments... Showing help.")
        print()
        parser.print_help()
        sys.exit()

    try:
        args.func(args)
    except Exception as e:
        print(f"{lineno(): >4}.[ {BRed}ERROR{RCol} ] args.func(args) Exception bellow: \n{e}")

    if args.clone:
        clone_repo(args.clone)
        sys.exit()

    elif args.edit:
        edit_desc(args.edit)
        sys.exit()
