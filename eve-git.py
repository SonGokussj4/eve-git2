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
from pathlib import Path
from dataclasses import dataclass


# =================================
# =           CONSTANTS           =
# =================================
CURDIR = str(Path(__file__).resolve().parent)
server = "http://gitea.avalon.konstru.evektor.cz"
GITEA_TOKEN = "9ef1c72e6b4c21ebbc5c6864207b27b7615d9205"


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

    # command = f"""CURL -X POST "${SERVER}/API/V1/USER/REPOS?ACCESS_TOKEN=${GITEA_TOKEN}" \
    #     -H "ACCEPT: APPLICATION/JSON" \
    #     -H "CONTENT-TYPE: APPLICATION/JSON" \
    #     -D "\"NAME\":\"${REPONAME}\", \
    #         \"DESCRIPTION\": \"${DESCRIPTION}\", \
    #         \"PRIVATE":${PRIVATE}"
    #         """

    command = f"""curl -sX GET "{server}/api/v1/users/ptinka/repos" -H "accept: application/json" \
                | python3 -m json.tool \
                | grep html_url \
                | sed -e 's#[ ",]##g' \
                      -e 's#html_url:##' \
                      -e 's#https://#http://#'"""
    os.system(command)


def transfer_repo():
    """To tranfer repo to some organization """
    print("Transfer")


def list_repo():
    """ Function for listing directories."""

    command = f"""curl -sX GET "{server}/api/v1/users/ptinka/repos" -H "accept: application/json" \
                    | python3 -m json.tool \
                    | grep html_url \
                    | sed -e 's#[ ",]##g' \
                            -e 's#html_url:##' \
                            -e 's#https://#http://#'"""
    os.system(command)


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
