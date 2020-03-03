#!/bin/bash

ENV_NAME=".env"
PRG_NAME="eve_git.py"

## FIND DIRECTORY OF THE SCRIPT
SOURCE="${BASH_SOURCE[0]}"

# Resolve $SOURCE until the file is no longer a symlink
while [ -h "$SOURCE" ]; do
  SCRIPTDIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  # If $SOURCE was a relative symlink, we need to resolve it relative
  # to the path where the symlink file was located
  [[ $SOURCE != /* ]] && SOURCE="$SCRIPTDIR/$SOURCE"
done
# Real script directory found
SCRIPTDIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null && pwd )"

## ACTIVATE VIRTUAL ENVIRONMENT AND RUN APP
source "$SCRIPTDIR"/${ENV_NAME}/bin/activate
python "$SCRIPTDIR"/${PRG_NAME} "$@"
