#!/bin/bash

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

# LOAD VARIABLES FROM REPO.CONFIG
source "${SCRIPTDIR}/repo.config" 2>/dev/null
ENV_NAME="${name}"
PRG_NAME="${main_file}"
CUSTOM_LD_LIBRARY="${ld_lib}"

## ACTIVATE VIRTUAL ENVIRONMENT AND RUN APP
source "$SCRIPTDIR"/${ENV_NAME}/bin/activate
python "$SCRIPTDIR"/${PRG_NAME} "$@"
