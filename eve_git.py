#!/usr/bin/env python
"""<DESCRIPTION OF THE PROGRAM>"""

# TODO Prepracovat toto vsechno (dlouhodoby TODO) do Classy...

# =================================
# =           LIBRARIES           =
# =================================
# System Libs
import os
import sys
import json
import getpass
from pathlib import Path
# from dataclasses import dataclass
import requests

# User Libs
import cli
try:
    import settings as cfg
except ModuleNotFoundError:
    print("[ ERROR ] No 'settings.py' file in root directory. Rename/Modify 'settings.py.example'")
    sys.exit()

# Pip Libs
from git import Repo, RemoteProgress  # https://gitpython.readthedocs.io/en/stable/tutorial.html#tutorial-label
from columnar import columnar  # https://pypi.org/project/Columnar/
from colorama import Fore  # https://pypi.org/project/colorama/
from tqdm import tqdm  # https://pypi.org/project/tqdm/
from click import style  # https://pypi.org/project/click/

# You have to run this script with python >= 3.7
if sys.version_info.major != 3:
    print("[ ERROR ] Hell NO! You're using Python2!! That's not cool man...")
    sys.exit()
if sys.version_info.minor <= 6:
    print("[ ERROR ] Nah... Your Python version have to be at least 3.7. Sorry")
    sys.exit()


# =================================
# =           CONSTANTS           =
# =================================
SCRIPTDIR = Path(__file__).resolve().parent
CURDIR = Path('.')
SERVER = cfg.Server.url
GITEA_TOKEN = cfg.Server.gitea_token


# ===============================
# =           CLASSES           =
# ===============================
class Progress(RemoteProgress):
    """Show ProgressBar when clonning remote repo.

    Original code:
        https://github.com/hooyao/github-org-backup-tool/blob/master/utils.py
    """

    pbar_dict = dict()
    last_pbar = None

    last_op_code = None
    last_pos = None
    op_names = {RemoteProgress.COUNTING: 'Counting objects',
                RemoteProgress.COMPRESSING: 'Compressing objects',
                RemoteProgress.WRITING: 'Writing objects',
                RemoteProgress.RECEIVING: 'Receiving objects',
                RemoteProgress.RESOLVING: 'Resolving deltas',
                RemoteProgress.FINDING_SOURCES: 'Finding sources',
                RemoteProgress.CHECKING_OUT: 'Checking out files'}
    max_msg_len = 0
    for i, (key, value) in enumerate(op_names.items()):
        if len(value) > max_msg_len:
            max_msg_len = len(value)
    for i, (key, value) in enumerate(op_names.items()):
        if len(value) < max_msg_len:
            appended_value = value + (' ' * (max_msg_len - len(value)))
            op_names[key] = appended_value

    def update(self, op_code, cur_count, max_count=None, message=''):
        if op_code in self.op_names:
            op_name = self.op_names[op_code]
            if self.last_op_code is None or self.last_op_code != op_code:
                if self.last_pbar is not None:
                    self.last_pbar.close()
                self.last_pbar = tqdm(total=max_count, unit='item', desc=op_name,
                                      bar_format="%s{l_bar}%s%s{bar}%s{r_bar}" %
                                                 (Fore.GREEN, Fore.RESET, Fore.BLUE, Fore.RESET))
                self.last_pos = 0
                self.last_op_code = op_code
            pbar = self.last_pbar
            last_pos = self.last_pos
            diff = cur_count - last_pos
            pbar.update(diff)
            self.last_pbar = pbar
            self.last_op_code = op_code
            self.last_pos = cur_count


# TODO: Priklad decoratoru

# def authenticated_only(method):
#     def decorated(*args, **kwargs):
#         if check_authenticated(kwargs['user']):
#             return method(*args, **kwargs)
#         else:
#             raise UnauthenticatedError
#     return decorated

# def authorized_only(method):
#     def decorated(*args, **kwargs):
#         if check_authorized(kwargs['user'], kwargs['action']):
#             return method(*args, **kwargs)
#         else:
#             raise UnauthorizedError
#     return decorated


# @authorized_only
# @authenticated_only
# def execute(action, *args, **kwargs):
#     return action()


# =================================
# =           FUNCTIONS           =
# =================================
def create_org(args):
    """Function Description."""
    # Default parameters
    org_name_input, description, = '', ''
    if args == 'empty':
        pass
    elif len(args) == 1:
        org_name_input = args[0]
    elif len(args) == 2:
        org_name_input, description = args

    org_name = input(f'Organization name [{org_name_input}]: ')
    org_name = org_name_input if not org_name else org_name
    if not org_name:
        print(f"[ ERROR ] You have to enter the name of the organization.")
        sys.exit(1)

    desc = input(f'Organization description [{description}]: ')
    desc = description if not desc else desc
    if not desc:
        print(f"[ ERROR ] You have to specify organization description.")
        sys.exit(1)

    # Try to create the org_name
    repo_headers = {'accept': 'application/json', 'content-type': 'application/json'}
    repo_data = {
        "description": desc,
        # "full_name": full_name,  # TODO moznost zadani?
        "repo_admin_change_team_access": True,
        "username": org_name,  # Org name
        "visibility": "public",
    }

    res = requests.post(url=f"{SERVER}/api/v1/orgs/?access_token={GITEA_TOKEN}",
                        headers=repo_headers,
                        json=repo_data)

    # Viable responses
    if res.status_code == 401:
        print(f"[ ERROR ] Something went wrong. Check your GITEA_TOKEN or internet connection.")
        sys.exit(1)

    elif res.status_code == 422:
        print(f"[ ERROR ] Repository '{org_name}' with the same name already exists.")
        sys.exit(1)

    elif res.status_code == 422:
        print(f"[ ERROR ] Validation Error... Can't create repository with this name. Details bellow.")
        print(f"[ ERROR ] {json.loads(res.content)}")
        sys.exit(1)

    elif res.status_code == 201:
        print("[ INFO ] Done. Organization created.")

    sys.exit(0)


def create_repo(args_create):

    # Default parameters
    reponame, description, username = '', '', getpass.getuser()
    if args_create == 'empty':
        pass
    elif len(args_create) == 1:
        reponame = args_create[0]
    elif len(args_create) == 2:
        reponame, description = args_create
    else:
        reponame, description, username = args_create

    repo = input(f'Repository name [{reponame}]: ')
    repo = reponame if not repo else repo
    if not repo:
        print(f"[ ERROR ] You have to enter the name of your repository.")
        sys.exit(1)

    desc = input(f'Repository description [{description}]: ')
    desc = description if not desc else desc
    if not desc:
        print(f"[ ERROR ] You have to write a small description for your project.")
        sys.exit(1)

    # Try to create the repo
    repo_headers = {'accept': 'application/json', 'content-type': 'application/json'}
    # TODO toto mel ptinka - zjistit, co delat ACCESS_TOKEN
    # repo_headers = {'content-type': 'application/json', 'Authorization': 'token ACCESS_TOKEN'}
    repo_data = {
        'auto_init': True,
        'name': repo,
        'readme': 'Default',
        'description': desc,
        # 'gitignores': 'Evektor',
        'private': False
    }
    # print("DEBUG: username:", username)
    # print("DEBUG: repo:", repo)

    # User entered third argument: username. Only users with admin right can create repos anywhere
    if type(args_create) == 'list' and len(args_create) == 3:
        res = requests.post(url=f"{SERVER}/api/v1/user/repos?access_token={GITEA_TOKEN}",
                            headers=repo_headers,
                            json=repo_data)
    else:
        res = requests.post(url=f"{SERVER}/api/v1/admin/users/{username}/repos?access_token={GITEA_TOKEN}",
                            headers=repo_headers,
                            json=repo_data)

    # Viable responses
    if res.status_code == 409:
        print(f"[ ERROR ] Repository '{repo}' with the same name under '{username}' already exists.")
        sys.exit(1)

    elif res.status_code == 401:
        print(f"[ ERROR ] Unauthorized... Something wrong with you GITEA_TOKEN...")
        sys.exit(1)

    elif res.status_code == 422:
        print(f"[ ERROR ] Validation Error... Can't create repository with this name. Details bellow.")
        print(f"[ ERROR ] {json.loads(res.content)}")
        sys.exit(1)

    elif res.status_code == 201:
        print("[ INFO ] Done. Repository created.")
        answer = input("Clone into current folder? [Y/n]: ")
        if answer.lower() in ['y', 'yes']:
            Repo.clone_from(url=f"{SERVER}/{username}/{repo}",
                           to_path=Path(CURDIR.resolve() / repo).resolve(),
                           branch='master',
                           progress=Progress())

        print("[ INFO ] DONE")
        sys.exit(0)


# TODO: trnasfer chybel v lokalni gitea (https://gitea.avalon.konstru.evektor.cz/api/swagger)
# TODO: bude ve verzi 1.12.0
# def transfer_repo():
#     """To tranfer repo to some organization """

#     reponame = "Test"
#     description = "Test3"
#     private = False
#     organization = "P135"
#     print("Server: ", SERVER)
#     print("TOKEN: ", GITEA_TOKEN)

#     repo_data = {'new_owner': organization}
#     # repo_headers = {'accept': 'application/json', 'content-type': 'application/json',
#     #                 'Authorization': 'token ACCESS_TOKEN'}
#     res = requests.post(
#         f"{SERVER}/api/v1/repos/ptinka/{reponame}/transfer?access_token={GITEA_TOKEN}",
#         headers=repo_headers, json=repo_data)
#     print(res)
#     print(f"{SERVER}/api/v1/repos/ptinka/{reponame}/transfer?access_token={GITEA_TOKEN}")


def list_org():
    """Function for listing organizations."""
    res = requests.get(f"{SERVER}/api/v1/admin/orgs?access_token={GITEA_TOKEN}")
    data = json.loads(res.content)
    if res.status_code == 403:
        print(f"[ ERROR ] Forbidden. You don't have enough access rights...")
        # TODO mozna to udelat tak, ze vezmu vsechny repositare a vytahnu z nich do setu vsechny org
        # TODO pak je accessnu a vypisu zde bez nutnosti GITEA_TOKEN
        return 1
    elif res.status_code == 200:
        print(f"[ INFO ] All ok. Here is the list.")

    # Data acquired, list all found repos in nice table
    headers = ('Organization', 'description')
    results = [[item['username'], item['description']] for item in data]
    tbl = columnar(results, headers, no_borders=True)
    print(tbl)

    return 0

def list_repo(args):
    """Function for listing directories."""
    res = requests.get(f"{SERVER}/api/v1/repos/search")
    data = json.loads(res.content)
    
    # TODO duplicate functionality, make a function
    # Check if there was a good response
    if not data.get('ok'):
        print(f"[ ERROR ] Shit... Data not acquired... {data}")
        sys.exit(1)
    elif not data.get('data'):
        print(f"[ ERROR ] Search for repository '{reponame}' returned 0 results... Try something different.")
        sys.exit(1)

    # Data acquired, list all found repos in nice table
    headers = ('id', 'repository', 'user', 'description')
    if len(args) == 1:
        results = [[item['id'], item['name'], item['owner']['login'], item['description']]
                    for item in data.get('data') if item['owner']['login'].lower() == args[0].lower()]
    else:
        results = [[item['id'], item['name'], item['owner']['login'], item['description']]
                    for item in data.get('data')]
    tbl = columnar(results, headers, no_borders=True)
    print(tbl)
    
    # for dat in data:
    #     print(dat["html_url"])
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
            print(f"[ ERROR ] User '{username}' doesn't exist!")
            sys.exit(1)

        # Does the <repository> of <user> exist?
        res = requests.get(f"{SERVER}/api/v1/repos/{username}/{reponame}")
        if res.status_code != 200:
            print(f"[ ERROR ] Repository '{SERVER}/{username}/{reponame}' does not exist.")
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
        # print(f"[ DEBUG ] res: {res}")

        data = json.loads(res.content)

        # Check if there was a good response
        if not data.get('ok'):
            print(f"[ ERROR ] Shit... Data not acquired... {data}")
            sys.exit(1)
        elif not data.get('data'):
            print(f"[ ERROR ] Search for repository '{reponame}' returned 0 results... Try something different.")
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
            print("[ ERROR ] You have to write an ID")
            sys.exit(1)
        elif not answer.isdigit():
            print("[ ERROR ] What you entered is not a number... You have to write one of the IDs.")
            sys.exit(1)

        # Get the right repo by it's ID
        repo_id = int(answer)
        selected_repository = [ls for ls in results if ls[0] == repo_id]

        # User made a mistake and entered number is not one of the listed repo IDs
        if len(selected_repository) == 0:
            print(f"[ ERROR ] Not a valid answer. You have to select one of the IDs.")
            sys.exit(1)

        # Something went wrong. There should not be len > 1... Where's the mistake in the code?
        elif len(selected_repository) > 1:
            print(f"[ ERROR ] Beware! len(selected_repository) > 1... That's weird... "
                  f"Like really... Len is: {len(selected_repository)}")
            sys.exit(1)

        print(f"[ INFO ] Clonning ID: {repo_id}")
        reponame, username = selected_repository[0][1], selected_repository[0][2]
        clone_repo([reponame, username])
        return 0


def remove_repo(args_remove):
    """Remove repository from gitea"""
    # print(f"[ DEBUG ] reponame: {args_remove}")

    # User specified both arguments: --clone <reponame> <username>
    if len(args_remove) == 2:
        reponame, username = args_remove

        # Does the username exist?
        res = requests.get(f"{SERVER}/api/v1/users/{username}")
        if res.status_code != 200:
            print(f"[ ERROR ] User '{username}' doesn't exist!")
            sys.exit(1)

        # Does the <repository> of <user> exist?
        res = requests.get(f"{SERVER}/api/v1/repos/{username}/{reponame}")
        if res.status_code != 200:
            print(f"[ ERROR ] Repository '{SERVER}/{username}/{reponame}' does not exist.")
            sys.exit(1)

        # Everything OK, delete the repository
        print(f"[ INFO ] You are about to REMOVE repository: '{SERVER}/{username}/{reponame}'")
        answer = input(f"Are you SURE you want to do this??? This operation CANNOT be undone [y/N]: ")
        if answer.lower() not in ['y', 'yes']:
            print(f"[ INFO ] Cancelling... Nothing removed.")
            sys.exit(0)

        answer = input(f"Enter the repository NAME as confirmation [{reponame}]: ")
        if not answer == reponame:
            print(f"[ ERROR ] Entered reponame '{answer}' is not the same as '{reponame}'. Cancelling...")
            sys.exit(1)

        print(f"[ INFO ] Removing '{SERVER}/{username}/{reponame}'")
        res = requests.delete(url=f"{SERVER}/api/v1/repos/{username}/{reponame}?access_token={GITEA_TOKEN}")

        # Case when something is wrong with GITEA_TOKEN...
        if res.status_code == 401:
            print("[ ERROR ] Unauthorized... Something wrong with you GITEA_TOKEN...")
            sys.exit()

        # Case when normal user tries to remove repository of another user and doesn't have authorization for that
        elif res.status_code == 403:
            print("[ ERROR ] Forbidden... You don't have enough permissinons to delete this repository...")
            sys.exit()

        print("[ INFO ] DONE")

        return 0

    # User didn't specify <username>: --remove <reponame>
    elif len(args_remove) == 1:
        reponame = args_remove[0]
        res = requests.get(f"{SERVER}/api/v1/repos/search?q={reponame}&sort=created&order=desc")

        data = json.loads(res.content)

        # Check if there was a good response
        if not data.get('ok'):
            print(f"[ ERROR ] Shit... Data not acquired... {data}")
            sys.exit(1)
        elif not data.get('data'):
            print(f"[ ERROR ] Search for repository '{reponame}' returned 0 results... Try something different.")
            sys.exit(1)

        # Data acquired, list all found repos in nice table
        headers = ('id', 'repository', 'user', 'description')
        results = [[item['id'], item['name'], item['owner']['login'], item['description']]
                   for item in data.get('data')]
        patterns = [
            (getpass.getuser(), lambda text: style(text, fg='green')),
        ]
        tbl = columnar(results, headers, no_borders=True, patterns=patterns, wrap_max=0)
        print(tbl)

        # Ask for repo ID
        answer = input("Enter repo ID: ")
        if not answer:
            print("[ ERROR ] You have to write an ID")
            sys.exit(1)
        elif not answer.isdigit():
            print("[ ERROR ] What you entered is not a number... You have to write one of the IDs.")
            sys.exit(1)

        # Get the right repo by it's ID
        repo_id = int(answer)
        selected_repository = [ls for ls in results if ls[0] == repo_id]

        # User made a mistake and entered number is not one of the listed repo IDs
        if len(selected_repository) == 0:
            print(f"[ ERROR ] Not a valid answer. You have to select one of the IDs.")
            sys.exit(1)

        # Something went wrong. There should not be len > 1... Where's the mistake in the code?
        elif len(selected_repository) > 1:
            print(f"[ ERROR ] Beware! len(selected_repository) > 1... That's weird... "
                  f"Like really... Len is: {len(selected_repository)}")
            sys.exit(1)

        print(f"[ INFO ] Selected ID: {repo_id}")
        reponame, username = selected_repository[0][1], selected_repository[0][2]
        remove_repo([reponame, username])
        return 0


def remove_org(args_remove):
    """Remove repository from gitea"""

    # User specified both arguments: --clone <reponame> <username>
    if len(args_remove) == 1:
        orgname = args_remove[0]

        # Get the repository
        res = requests.get(f"{SERVER}/api/v1/orgs/{orgname}")

        # Case repo does not exist
        if res.status_code == 404:
            print(f"[ ERROR ] Organization '{orgname}' not found...")
            
            # Get all organizations
            res = requests.get(f"{SERVER}/api/v1/admin/orgs?access_token={GITEA_TOKEN}")
            data = json.loads(res.content)
            
            # TODO Duplicate Data....
            # Check if there was a good response
            if not data:
                print(f"[ ERROR ] Search for organizations returned 0 results... Try something different.")
                sys.exit(1)

            print("Which Organization you want to delete?")
            # Data acquired, list all found repos in nice table
            headers = ('id', 'org', 'description')
            results = [[item['id'], item['username'], item['description']]
                    for item in data]
            tbl = columnar(results, headers, no_borders=True, wrap_max=0)
            print(tbl)

            # Ask for org ID
            answer = input("Enter org ID: ")
            if not answer:
                print("[ ERROR ] You have to write an ID")
                sys.exit(1)
            elif not answer.isdigit():
                print("[ ERROR ] What you entered is not a number... You have to write one of the IDs.")
                sys.exit(1)

            # Get the right org by it's ID
            org_id = int(answer)
            selected_organization = [ls for ls in results if ls[0] == org_id]

            # User made a mistake and entered number is not one of the listed repo IDs
            if len(selected_organization) == 0:
                print(f"[ ERROR ] Not a valid answer. You have to select one of the IDs.")
                sys.exit(1)

            # Something went wrong. There should not be len > 1... Where's the mistake in the code?
            elif len(selected_organization) > 1:
                print(f"[ ERROR ] Beware! len(selected_organization) > 1... That's weird... "
                    f"Like really... Len is: {len(selected_organization)}")
                sys.exit(1)

            print(f"[ INFO ] Selected ID: {org_id}")
            orgname = selected_organization[0][1]

            remove_org([orgname])

        # Case repo exists, ask if you are really sure to remove it
        elif res.status_code == 200:

            # Everything OK, delete the repository
            print(f"[ INFO ] You are about to REMOVE organization: '{SERVER}/{orgname}'")
            answer = input(f"Are you SURE you want to do this??? This operation CANNOT be undone [y/N]: ")
            # TODO mam pocit, ze kdyz se smaze organizace, tak se jen repo v nich nekam premisti, zkusit
            if answer.lower() not in ['y', 'yes']:
                print(f"[ INFO ] Cancelling... Nothing removed.")
                sys.exit(0)

            answer = input(f"Enter the organization NAME as confirmation [{orgname}]: ")
            if not answer == orgname:
                print(f"[ ERROR ] Entered orgname '{answer}' is not the same as '{orgname}'. Cancelling...")
                sys.exit(1)

            print(f"[ INFO ] Deleting organization '{orgname}'")
            res = requests.delete(f"{SERVER}/api/v1/orgs/{orgname}?access_token={GITEA_TOKEN}")

            # All ok
            if res.status_code == 204:
                print("[ INFO ] Done. Organization removed.")
                return 0

            elif res.status_code == 401:
                print("[ ERROR ] Unauthorized. You don't have enough rights to delete this repository.")
                sys.exit(1)

    elif args_remove == 'empty':
        # Get all organizations
        res = requests.get(f"{SERVER}/api/v1/admin/orgs?access_token={GITEA_TOKEN}")
        data = json.loads(res.content)

        # Check if there was a good response
        if not data:
            print(f"[ ERROR ] Search for organizations returned 0 results... Try something different.")
            sys.exit(1)

        print("Which Organization you want to delete?")
        # Data acquired, list all found repos in nice table
        headers = ('id', 'org', 'description')
        results = [[item['id'], item['username'], item['description']]
                   for item in data]
        tbl = columnar(results, headers, no_borders=True, wrap_max=0)
        print(tbl)

        # Ask for org ID
        answer = input("Enter org ID: ")
        if not answer:
            print("[ ERROR ] You have to write an ID")
            sys.exit(1)
        elif not answer.isdigit():
            print("[ ERROR ] What you entered is not a number... You have to write one of the IDs.")
            sys.exit(1)

        # Get the right org by it's ID
        org_id = int(answer)
        selected_organization = [ls for ls in results if ls[0] == org_id]

        # User made a mistake and entered number is not one of the listed repo IDs
        if len(selected_organization) == 0:
            print(f"[ ERROR ] Not a valid answer. You have to select one of the IDs.")
            sys.exit(1)

        # Something went wrong. There should not be len > 1... Where's the mistake in the code?
        elif len(selected_organization) > 1:
            print(f"[ ERROR ] Beware! len(selected_organization) > 1... That's weird... "
                  f"Like really... Len is: {len(selected_organization)}")
            sys.exit(1)

        print(f"[ INFO ] Selected ID: {org_id}")
        orgname = selected_organization[0][1]

        remove_org([orgname])

    return 0


# ====================================
# =           MAIN PROGRAM           =
# ====================================
if __name__ == '__main__':

    parser = cli.get_parser()
    args = parser.parse_args()

    print("--------------------------------------------------------------------------------")
    print(f"[ DEBUG ] args: {args}")
    print("--------------------------------------------------------------------------------")

    # In case of no input, show help
    # if not any(vars(args).values()):
    if not len(sys.argv) > 1:
        print("[ ERROR ] No arguments... Showing help.")
        print()
        parser.print_help()
        sys.exit()

    if args.create:
        create_repo(args.create)
        sys.exit()

    elif args.create_org:
        create_org(args.create_org)
        sys.exit()

    elif args.clone:
        clone_repo(args.clone)
        sys.exit()

    elif args.remove:
        remove_repo(args.remove)
        sys.exit()

    elif args.remove_org:
        remove_org(args.remove_org)
        sys.exit()

    # elif args.transfer:
    #     print("[ WARNING ] Transfer is not yet done. Because the API is broken in Gitea. For now...")
    #     print("[ INFO ] Exitting now...")
    #     # transfer_repo()
    #     sys.exit()

    # # elif args.transfer:
    # #     transfer_repo()
    # #     sys.exit()

    elif args.list_repo:
        list_repo(args.list_repo)
        sys.exit()

    # elif args.create_org_repo:
    #     create_repo_org(args.create_org_repo)
    #     sys.exit()

    elif args.list_org is True:
        list_org()
        sys.exit()

    # user = Person()
    # user.name = 'Jan Verner'
    # user.age = 99
    # print("DEBUG: user:", user)

    # user2 = Person('Petr Tinka', 99)
    # print("DEBUG: user2:", user2)
