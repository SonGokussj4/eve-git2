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

    server = "http://gitea.avalon.konstru.evektor.cz"
    GITEA_TOKEN = "9ef1c72e6b4c21ebbc5c6864207b27b7615d9205"

    reponame = input('Repository name: ')
    description = input('Repository description: ')
    private = False
    print("Server: ", server)
    print("TOKEN: ", GITEA_TOKEN)

    command = f"""curl -X POST "${server}/api/v1/user/repos?access_token=${GITEA_TOKEN}" \
        -H "accept: application/json" \
        -H "content-type: application/json" \
        -d "\"name\":\"${reponame}\", \
            \"description\": \"${description}\", \
            \"private":${private}"
            """

    # command = f"""echo ${GITEA_TOKEN}"""

    os.system(command)


def transfer_repo():
    """To tranfer repo to some organization """
    print("Transfer")

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

    user = Person()
    user.name = 'Jan Verner'
    user.age = 99
    print("DEBUG: user:", user)

    user2 = Person('Petr Tinka', 99)
    print("DEBUG: user2:", user2)
