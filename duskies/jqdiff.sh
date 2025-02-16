#!/bin/bash

# Diff of pretty-print (jq .) of two JSON files, put options to diff *after* the two file names

# Fail loudly
set -euo pipefail
trap 'rc=$?;set +ex;if [[ $rc -ne 0 ]];then trap - ERR EXIT;echo 1>&2;echo "*** fail *** : code $rc : $DIR/$SCRIPT $ARGS" 1>&2;echo 1>&2;exit $rc;fi' ERR EXIT
ARGS="$*"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$(basename "${BASH_SOURCE[0]}")"

left=$1
shift
right=$1
shift


diff "$@"  <(jq . $left)  <(jq . $right)  || true
