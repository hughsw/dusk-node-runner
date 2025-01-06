#!/bin/bash

# Fail loudly
set -euo pipefail
trap 'rc=$?;set +ex;if [[ $rc -ne 0 ]];then trap - ERR EXIT;echo 1>&2;echo "*** fail *** : code $rc : $DIR/$SCRIPT $ARGS" 1>&2;echo 1>&2;exit $rc;fi' ERR EXIT
ARGS="$*"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$(basename "${BASH_SOURCE[0]}")"


# one of: mainnet testnet devnet
network=${1:-mainnet}
# one of: default archive
feature=${2:-default}


timestamp=$(date '+%Y-%m-%d-%H%M-%S')

log_dir=${DIR}/logs
log_file=${log_dir}/node-installer_${timestamp}.log
log_file_raw=$log_file.raw
installer=${log_dir}/node-installer_${timestamp}.sh

mkdir -p $log_dir

{
    echo DIR: $DIR
    echo SCRIPT: $SCRIPT
    echo ARGS: $ARGS
    echo timestamp: $timestamp

    set -x

    curl --proto '=https' --tlsv1.2 -sSfL https://github.com/dusk-network/node-installer/releases/latest/download/node-installer.sh > $installer
    #curl --proto '=https' --tlsv1.2 -sSfL https://github.com/dusk-network/node-installer/releases/download/v0.5.1/node-installer.sh > $installer

    FEATURE=$feature sudo bash -x $installer $network

} 2>&1 | tee $log_file_raw | grep --line-buffered -v -e '^+\+ ' | tee $log_file
