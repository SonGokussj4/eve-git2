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

# Load variables from app.conf
VENV_NAME=$(grep venv_name ${SCRIPTDIR}/app.conf | awk -F '[:=]' '{print $2}' | tr -d " ")
MAIN_FILE=$(grep main_file ${SCRIPTDIR}/app.conf | awk -F '[:=]' '{print $2}' | tr -d " ")
if [[ $VENV_NAME == "" || $MAIN_FILE == "" ]]; then
    echo "[ ERROR ] Can't load either venv_name: '$VENV_NAME' or main_file: '$MAIN_FILE' from '${SCRIPTDIR}/app.conf'..."
    exit 1
fi

# Add custom LD_LIBRARY_PATH if set in app.conf
CUSTOM_LD_LIBRARY=$(grep ld_lib ${SCRIPTDIR}/app.conf | awk -F '[:=]' '{print $2}' | tr -d " ")
if [[ CUSTOM_LD_LIBRARY != "" ]]; then
    # echo "[ DEBUG ] Adding '${CUSTOM_LD_LIBRARY}' to \$LD_LIBRARY_PATH"
    export LD_LIBRARY_PATH=${CUSTOM_LD_LIBRARY}:$LD_LIBRARY_PATH
fi

## ACTIVATE VIRTUAL ENVIRONMENT AND RUN APP
source "$SCRIPTDIR"/${VENV_NAME}/bin/activate
python "$SCRIPTDIR"/${MAIN_FILE} "$@"
