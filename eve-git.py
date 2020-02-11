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
server = "http://gitea.avalon.konstru.evektor.cz"
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
    print("Server: ", server)
    print("TOKEN: ", GITEA_TOKEN)

    command = f"""curl -X post "{server}/api/v1/user/repos?access_token={GITEA_TOKEN}" \
        -H "accept: application/json" \
        -H "content-type: application/json" \
        -d "\"name\":\"{reponame}\", \
            \"description\": \"{description}\", \
            \"private":{private}"
            """

    os.system(command)


def transfer_repo():
    """To tranfer repo to some organization """
    print("Transfer")


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

    res = requests.get(f"{server}/api/v1/users/ptinka/repos")
    data = json.loads(res.content)
    for dat in data:
        print(dat["html_url"])




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
        sys.exit
    elif args.list_repo:
        list_repo()
        sys.exit()

    user = Person()
    user.name = 'Jan Verner'
    user.age = 99
    print("DEBUG: user:", user)

    user2 = Person('Petr Tinka', 99)
    print("DEBUG: user2:", user2)
