#!/bin/bash

set -euo pipefail

dusk_src_dir=/opt/dusk.install
wallet_src_dir=/home/duskadmin/.dusk.install
#wallet_src_dir=/root/.dusk.install

dusk_target_dir=/opt/dusk
wallet_target_dir=/home/duskadmin/.dusk
#wallet_target_dir=/root/.dusk

#mount

# copy the stateful trees, create the same nonce in each tree
if [ \( ! -e $dusk_target_dir -o -z "$(ls -A $dusk_target_dir)" \) -a \( ! -e $wallet_target_dir  -o -z "$(ls -A $wallet_target_dir)" \) ] ; then
    timestamp=$(date '+%Y-%m-%d-%H%M-%S')
    echo timestamp: $timestamp
    tag=$RANDOM$RANDOM$RANDOM$RANDOM$RANDOM$RANDOM
    echo tag: $tag

    nonce=${timestamp}_${tag}
    echo nonce: $nonce

    # we don't change the owner of the nonce because:
    # - more complexity
    # - perhaps leaving as root is one more barrier to accidental corruption
    cp -a $dusk_src_dir/. $dusk_target_dir
    echo $nonce | tee $dusk_target_dir/nonce

    cp -a $wallet_src_dir/. $wallet_target_dir
    echo $nonce | tee $wallet_target_dir/nonce
fi

set -x

# we don't try to dissect possible reasons for failure...
cmp $dusk_target_dir/nonce $wallet_target_dir/nonce

#echo RUSK_PUBLIC_ADDRESS: $RUSK_PUBLIC_ADDRESS

sed -i \
    -e "s/# log_type = 'json'/log_type = 'json'/" \
    $dusk_target_dir/conf/rusk.toml

#    -e "s/ *public_address *=.*/public_address = '$RUSK_PUBLIC_ADDRESS'/" \
