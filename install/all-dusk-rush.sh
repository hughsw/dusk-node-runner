#!/bin/bash

# Fail loudly
set -euo pipefail
trap 'rc=$?;set +ex;if [[ $rc -ne 0 ]];then trap - ERR EXIT;echo 1>&2;echo "*** fail *** : code $rc : $DIR/$SCRIPT $ARGS" 1>&2;echo 1>&2;exit $rc;fi' ERR EXIT
ARGS="$*"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$(basename "${BASH_SOURCE[0]}")"


exclusions=""
for exclusion in "$@" ; do
    #echo $exclusion
    exclusions="$exclusions -e $exclusion"
done

if [ -n "$exclusions" ] ; then
    filter="fgrep -v $exclusions"
else
    filter=cat
fi

cmd="find / -xdev \( -iname '*dusk*' -o -iname '*rusk*' \) | $filter"
cmd="find /etc /opt/dusk /usr/bin ~ \( -iname '*dusk*' -o -iname '*rusk*' \) | $filter"
eval $cmd

rmcmd="# $cmd | sort -r | xargs rm -r ; systemctl daemon-reload"

echo
echo $rmcmd
