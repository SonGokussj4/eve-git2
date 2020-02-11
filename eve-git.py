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
    private = True
    print("Server: ", SERVER)
    print("TOKEN: ", GITEA_TOKEN)

    repo_data = {'name': reponame, 'description': description, 'private': private}
    repo_headers = {'accept': 'application/json',
               'content-type': 'application/json'}

    res = requests.post(
        f"{SERVER}/api/v1/user/repos?access_token={GITEA_TOKEN}", headers=repo_headers, json=repo_data)
    print(res)

def transfer_repo():
    """To tranfer repo to some organization """
    print("Transfer")

    # res = requests.get(f"{SERVER}/api/v1/users/ptinka/repos")
    # data = json.loads(res.content)
    # for dat in data:
    #     print(dat["html_url"])

    # reponame = "Test2"
    # description = "Test3"
    # private = False
    # organization = "P135"
    # print("Server: ", SERVER)
    # print("TOKEN: ", GITEA_TOKEN)
    # repo_data = {'username': organization, 'name': reponame,
    #              'description': description, 'private': private}
    # repo_headers = {'accept': 'application/json',
    #                 'content-type': 'application/json'}

    # res = requests.post(
    #     f"{SERVER}/api/v1/user/repos?access_token={GITEA_TOKEN}", headers=repo_headers, json=repo_data)
    # print(res)

def list_repo():
    """ Function for listing directories."""

    # command = f"""curl -sX GET "{server}/api/v1/users/ptinka/repos" -H "accept: application/json" \
    #                 | python3 -mjson.tool \
    #                 | grep html_url \
    #                 | sed -e 's#[ ",]##g' \
    #                         -e 's#html_url:##' \
    #                         -e 's#https://#http://#'"""
    # # os.system(command)
    # # print(f"shlex output: {shlex.split(command)}")
    # res = sp.check_output(shlex.split(command))
    # print(f"res output: {res}")

    res = requests.get(f"{SERVER}/api/v1/users/ptinka/repos")
    data = json.loads(res.content)
    for dat in data:
        print(dat["html_url"])

def remove_repo():
    reponame = "Test"

    res = requests.delete(
        f"{SERVER}/api/v1/repos/ptinka/{reponame}?access_token={GITEA_TOKEN}")
    print(res)


# ====================================
# =           MAIN PROGRAM           =
# ====================================


if __name__ == '__main__':

    parser = cli.get_parser()
    args = parser.parse_args()

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

    user = Person()
    user.name = 'Jan Verner'
    user.age = 99
    print("DEBUG: user:", user)

    user2 = Person('Petr Tinka', 99)
    print("DEBUG: user2:", user2)
