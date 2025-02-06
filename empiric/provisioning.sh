#!/bin/bash

# Fail loudly
set -euo pipefail
trap 'rc=$?;set +ex;if [[ $rc -ne 0 ]];then trap - ERR EXIT;echo 1>&2;echo "*** fail *** : code $rc : $DIR/$SCRIPT $ARGS" 1>&2;echo 1>&2;exit $rc;fi' ERR EXIT
ARGS="$*"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$(basename "${BASH_SOURCE[0]}")"

name_tag=provisioning

timestamp=$(date '+%Y-%m-%d-%H%M-%S')
log_dir=${DIR}/$name_tag.logs
log_base=${log_dir}/${name_tag}_${timestamp}
log_file=${log_base}.log
json_file=${log_base}.json

mkdir -p $log_dir

{

    echo "{\"timestamp\": \"$timestamp\", \"provisioners\": "
    curl -sSL -X POST 'https://nodes.dusk.network/on/node/provisioners'
    echo "}"

    #echo "{\"timestamp\": \"$timestamp\"}"
    #curl -sSL -X POST 'https://nodes.dusk.network/on/node/provisioners' | jq .
    #curl -sSL -X POST 'https://dusk03.alley.network/on/node/provisioners' | jq .

} > $log_file 2>&1 

jq . < $log_file > $json_file 2>&1
