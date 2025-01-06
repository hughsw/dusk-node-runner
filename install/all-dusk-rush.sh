#!/bin/bash

# Helper for removing dusk and rusk from a node.
# Find and print names of dusk or rusk files and then print a command that if executed would remove all of the files.
# Arguments are prefixes of directories or files to exclude from the the find.
# Expects that you have sudo

# Fail loudly
set -euo pipefail
trap 'rc=$?;set +ex;if [[ $rc -ne 0 ]];then trap - ERR EXIT;echo 1>&2;echo "*** fail *** : code $rc : $DIR/$SCRIPT $ARGS" 1>&2;echo 1>&2;exit $rc;fi' ERR EXIT
ARGS="$*"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$(basename "${BASH_SOURCE[0]}")"


exclusions=""
for exclusion in "$@" ; do
    exclusions="$exclusions -e $exclusion"
done

if [ -n "$exclusions" ] ; then
    filter="fgrep -v $exclusions"
else
    filter=cat
fi

cmd="sudo find /etc /opt /usr/bin ~ \( -iname '*dusk*' -o -iname '*rusk*' \) | $filter"
eval $cmd

rmcmd="# $cmd | sort -r | xargs sudo rm -r ; sudo systemctl daemon-reload"

echo
echo $rmcmd
