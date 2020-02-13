#!/usr/bin/env python
"""<DESCRIPTION OF THE PROGRAM>"""

# =================================
# =           LIBRARIES           =
# =================================
# User Libs
import cli

# System Libs
import os
import sys
import json
import getpass
from pathlib import Path
from dataclasses import dataclass
import requests
from columnar import columnar

# =================================
# =           CONSTANTS           =
# =================================
CURDIR = str(Path(__file__).resolve().parent)
SERVER = "http://gitea.avalon.konstru.evektor.cz"
GITEA_TOKEN = os.environ['GITEA_TOKEN']


# ===============================
# =           CLASSES           =
# ===============================
@dataclass
class Person:
    name: str = ''
    age: int = 0


# =================================
# =           FUNCTIONS           =
# =================================

def create_repo():

    # reponame = input('Repository name: ')
    # description = input('Repository description: ')
    reponame = "Test"
    description = "For testing..."
    private = False
    print("Server: ", SERVER)
    print("TOKEN: ", GITEA_TOKEN)

    repo_data = {'name': reponame,
                 'description': description, 'private': private}
    repo_headers = {'accept': 'application/json',
                    'content-type': 'application/json'}

    res = requests.post(
        f"{SERVER}/api/v1/user/repos?access_token={GITEA_TOKEN}",
        headers=repo_headers, json=repo_data)
    print(res)


def create_repo_org():
    # Create repository in organization

    # reponame = input('Repository name: ')
    # description = input('Repository description: ')
    # descriporganizationtion = input('Organization: ')
    reponame = "Test"
    organization = "P135"
    description = "Test"
    private = False
    repo_data = {'name': reponame,
                 'description': description, 'private': private}
    repo_headers = {'content-type': 'application/json',
                    'Authorization': 'token ACCESS_TOKEN'}
    res = requests.post(
        f"{SERVER}/api/v1/org/{organization}/repos?access_token={GITEA_TOKEN}",
        headers=repo_headers, json=repo_data)
    # print(f"{SERVER}/api/v1/org/{organization}/repos?access_token={GITEA_TOKEN}")
    print(res)

# TODO: trnasfer chybel v lokalni gitea (https://gitea.avalon.konstru.evektor.cz/api/swagger)
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


def list_org_repo(organization):
    # List of organization repositories
    res = requests.get(f"{SERVER}/api/v1/orgs/{organization}/repos")
    print(res)
    data = json.loads(res.content)
    for dat in data:
        print(dat["html_url"])
    # print(f"{SERVER}/api/v1/orgs/{organization}/repos")


def list_repo():
    """ Function for listing directories."""

    res = requests.get(f"{SERVER}/api/v1/users/{getpass.getuser()}/repos")
    data = json.loads(res.content)
    for dat in data:
        print(dat["html_url"])


def remove_repo(reponame, user=None):
    """Remove repository from gitea """
    repo_headers = {'accept': 'application/json'}
    res = requests.get(f"{SERVER}/api/v1/users/search", headers=repo_headers)
    data = json.loads(res.content)['data']
    users = [login['login'] for login in data]

    # If user give two values(reponame, user), remove this
    if user:
        if user not in users:
            print(f'User "{user}" not found.')
            return
        res = requests.delete(
            f"{SERVER}/api/v1/repos/{user}/{reponame}?access_token={GITEA_TOKEN}")
        # print(res)
    else:
        # Search repositories
        res = requests.get(f"{SERVER}/api/v1/repos/search?q={reponame}",
                           headers=repo_headers)
        data = json.loads(res.content)
        # get list of dicts
        for key, value in data.items():
            list_of_dict = value
        if list_of_dict == []:
            print("Searching repository doesn't exist.")
            return
        list_to_table = []
        for char in list_of_dict:
            repository = char["name"]
            username = (char["owner"])["login"]
            description = char["description"]
            list_to_table.append([repository, username, description])
        # create table
        headers = ['repository', 'user', 'description']
        table = columnar(list_to_table, headers, no_borders=True)
        print(table)

        values = input("Specify [repo] [user]: ").split(' ')
        user = values[1]
        repository = values[0]
        res = requests.delete(
            f"{SERVER}/api/v1/repos/{user}/{repository}?access_token={GITEA_TOKEN}")
        # print(res)

    if res.ok:
        print('Removing repository was successfull.')
    else:
        print('Repository not found.')


# ====================================
# =           MAIN PROGRAM           =
# ====================================


if __name__ == '__main__':

    parser = cli.get_parser()
    args = parser.parse_args()

    if args.create:
        create_repo()
        sys.exit()
    # elif args.transfer:
    #     transfer_repo()
    #     sys.exit()
    elif args.list_repo:
        list_repo()
        sys.exit()
    elif args.remove:
        if len(args.remove) == 2:
            remove_repo(args.remove[0], args.remove[1])
        else:
            remove_repo(args.remove[0])

        sys.exit()
    elif args.create_org_repo:
        create_repo_org()
        sys.exit()
    elif args.list_org_repo:
        list_org_repo(args.list_org_repo)
        sys.exit()

    user = Person()
    user.name = 'Jan Verner'
    user.age = 99
    print("DEBUG: user:", user)

    user2 = Person('Petr Tinka', 99)
    print("DEBUG: user2:", user2)
