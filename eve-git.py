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
import subprocess as sp
import shlex
import requests


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
    description = "Test"
    private = False
    print("Server: ", SERVER)
    print("TOKEN: ", GITEA_TOKEN)

    repo_data = {'name': reponame,
                 'description': description, 'private': private}
    repo_headers = {'accept': 'application/json',
                    'content-type': 'application/json'}

    res = requests.post(
        f"{SERVER}/api/v1/user/repos?access_token={GITEA_TOKEN}", headers=repo_headers, json=repo_data)
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

    # reponame = "Test"
    # description = "Test3"
    # private = False
    # organization = "P135"
    # print("Server: ", SERVER)
    # print("TOKEN: ", GITEA_TOKEN)

    # repo_data = {'new_owner': organization}
    # # repo_headers = {'accept': 'application/json', 'content-type': 'application/json',
    # #                 'Authorization': 'token ACCESS_TOKEN'}
    # res = requests.post(
    #     f"{SERVER}/api/v1/repos/ptinka/{reponame}/transfer?access_token={GITEA_TOKEN}",
    #     headers=repo_headers, json=repo_data)
    # print(res)
    # print(f"{SERVER}/api/v1/repos/ptinka/{reponame}/transfer?access_token={GITEA_TOKEN}")


def list_org_repo(organization):
    # List of organization repositories
    # organization = "P135"
    res = requests.get(f"{SERVER}/api/v1/orgs/{organization}/repos")
    print(res)
    data = json.loads(res.content)
    for dat in data:
        print(dat["html_url"])
    # print(f"{SERVER}/api/v1/orgs/{organization}/repos")


def list_repo():
    """ Function for listing directories."""

    # res = requests.get(f"{SERVER}/api/v1/users/{getpass.getuser()}/repos")
    res = requests.get(f"{SERVER}/api/v1/users/jverner/repos")
    data = json.loads(res.content)
    for dat in data:
        print(dat["html_url"])


def remove_repo(reponame, user=None):
    # reponame = "Test"
    # If user:
    #   requests delete repo
    # If not:
    #
    #   Find all repositories with the same name, return in format:
    #        test jverner   description (max 80 chars)
    #        test ptinka    description (max 80 chars)
    # Clovek pak zada:
    # Specify [repo] [user]: test ptinka
    # DELETE

    # Ask which repo to delete

    res = requests.delete(
        f"{SERVER}/api/v1/repos/ptinka/{reponame}?access_token={GITEA_TOKEN}")
    print(res)


# ====================================
# =           MAIN PROGRAM           =
# ====================================


if __name__ == '__main__':

    parser = cli.get_parser()
    args = parser.parse_args()

    print("DEBUG: args:", args)

    # In case of no input, show help
    if not any(vars(args).values()):
        print("ERROR: No arguments... Showing help.")
        print()
        parser.print_help()
        sys.exit()

    if args.create:
        create_repo()
        sys.exit()
    elif args.transfer:
        transfer_repo()
        sys.exit()
    elif args.list_repo:
        list_repo()
        sys.exit()
    elif args.remove:
        remove_repo()
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
