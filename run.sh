#!/bin/bash

# configFileName='${configFileName}'
configFileName='deploy.conf'

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

# Load variables from ${configFileName}
VENV_NAME=$(grep venv_name ${SCRIPTDIR}/${configFileName} | awk -F '[:=]' '{print $2}' | tr -d " ")
MAIN_FILE=$(grep main_file ${SCRIPTDIR}/${configFileName} | awk -F '[:=]' '{print $2}' | tr -d " ")
if [[ $VENV_NAME == "" || $MAIN_FILE == "" ]]; then
    echo "[ ERROR ] Can't load either venv_name: '$VENV_NAME' or main_file: '$MAIN_FILE' from '${SCRIPTDIR}/${configFileName}'..."
    exit 1
fi

# Add custom LD_LIBRARY_PATH if set in ${configFileName}
CUSTOM_LD_LIBRARY=$(grep ld_lib ${SCRIPTDIR}/${configFileName} | awk -F '[:=]' '{print $2}' | tr -d " ")
if [[ CUSTOM_LD_LIBRARY != "" ]]; then
    # echo "[ DEBUG ] Adding '${CUSTOM_LD_LIBRARY}' to \$LD_LIBRARY_PATH"
    export LD_LIBRARY_PATH=${CUSTOM_LD_LIBRARY}:$LD_LIBRARY_PATH
fi

## ACTIVATE VIRTUAL ENVIRONMENT
source "$SCRIPTDIR"/${VENV_NAME}/bin/activate

## RUN APP
if [ -f "$SCRIPTDIR/${MAIN_FILE}" ]; then
    python "$SCRIPTDIR"/${MAIN_FILE} "$@"
elif [ -f "$SCRIPTDIR/$(basename $SCRIPTDIR)/${MAIN_FILE}" ]; then
    python "$SCRIPTDIR/$(basename $SCRIPTDIR)/${MAIN_FILE}" "$@"
else
    echo "[ ERROR ] run.sh couldn't find ${MAIN_FILE} neiter in base dir or in module dir"
fi
