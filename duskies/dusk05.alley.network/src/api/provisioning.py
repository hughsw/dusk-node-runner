#!/usr/bin/env python3

# provisioning.py -- Capture timestamp and current Dusk provisioners info as JSON to stdout
#   Optional arg1 is scheme-host-port of Dusk node to queuy:
#     e.g.:     http://localhost:8080
#     default:  https://nodes.dusk.network
#
# Copyright (C) 2025  20 Octaves, LLC
# Apache License 2.0 (https://www.apache.org/licenses/LICENSE-2.0.txt)

import sys, os
import asyncio
import datetime
import json
import requests
import functools
import pickle

from utils import asyncify

printio = functools.partial(asyncio.to_thread, print)
getio = functools.partial(asyncio.to_thread, requests.get)
postio = functools.partial(asyncio.to_thread, requests.post)

provisionomics = dict(
    # https://docs.dusk.network/learn/tokenomics/
    block_per_epoch = 2160,
    block_per_period = 12_614_400,
    dusk_lux_per_dusk = 1_000_000_000,
    stake_min_lux = 1_000_000_000_000,
    dusk_development_fund_address = 'o1YvWG34EBTwdskfZ7PCvWKRUWKzskVnhJNjZHdau6VaUNpgDxpoSsisK8KGF6FayUi8Lzn4taAvZcHGprQuPsqFGH66SEPDRCbTmKGVwFYX7bEp2rF4wekvoc4dS8ghnKf',
    )

if False:
    async def get_dusk_chain_block_index(dusk_node_scheme_host_port):
        block_height_uri = f'{dusk_node_scheme_host_port}/on/graphql/query'
        block_height_query = b'query { block(height: -1) { header { height } } }'
        block_result = await postio(block_height_uri, data=block_height_query)

        return attrdict.deep(block_result.json()).block.header.height

@asyncify
def get_dusk_chain_block_index(dusk_node_scheme_host_port):
    block_height_uri = f'{dusk_node_scheme_host_port}/on/graphql/query'
    block_height_query = b'query { block(height: -1) { header { height } } }'
    block_result = requests.post(block_height_uri, data=block_height_query)

    return attrdict.deep(block_result.json()).block.header.height

if False:
    async def get_dusk_provisioners(dusk_node_scheme_host_port):
        provisioners_uri = f'{dusk_node_scheme_host_port}/on/node/provisioners'
        provisioners_result = await postio(provisioners_uri)

        return attrdict.deep(provisioners_result.json())

@asyncify
def get_dusk_provisioners(dusk_node_scheme_host_port):
    provisioners_uri = f'{dusk_node_scheme_host_port}/on/node/provisioners'
    provisioners_result = requests.post(provisioners_uri)

    return attrdict.deep(provisioners_result.json())

if False:
    async def get_node_info(dusk_node_scheme_host_port):
        # OMG: https://myshell.co.uk/blog/2017/06/python-get-remote-ip-from-http-request-using-the-requests-module/
        info_uri = f'{dusk_node_scheme_host_port}/on/node/info'
        streaming_info_result = await postio(info_uri, stream=True)
        dusk_node_ip = streaming_info_result.raw._original_response.fp.raw._sock.getpeername()[0]
        result = ''.join(streaming_info_result.iter_content(None,decode_unicode=True))
        node_info = attrdict.deep(json.loads(result))

        return attrdict(
            dusk_node_ip = dusk_node_ip,
            dusk_node_version = node_info.version,
            dusk_chain_id = node_info.chain_id,
        )

@asyncify
def get_node_info(dusk_node_scheme_host_port):
    # OMG: https://myshell.co.uk/blog/2017/06/python-get-remote-ip-from-http-request-using-the-requests-module/
    info_uri = f'{dusk_node_scheme_host_port}/on/node/info'
    streaming_info_result = requests.post(info_uri, stream=True)
    dusk_node_ip = streaming_info_result.raw._original_response.fp.raw._sock.getpeername()[0]
    result = ''.join(streaming_info_result.iter_content(None,decode_unicode=True))
    node_info = attrdict.deep(json.loads(result))

    return attrdict(
        dusk_node_scheme_host_port = dusk_node_scheme_host_port,
        dusk_node_ip = dusk_node_ip,
        dusk_node_version = node_info.version,
        dusk_chain_id = node_info.chain_id,
    )


def make_provisioning_summary(now_utc_sec, node_info, dusk_chain_block_index, trigger_height, block_hash, provisioners):
    dusk_chain_epochblock_index = dusk_chain_block_index % provisionomics.block_per_epoch

    dusk_chain_epoch_index = dusk_chain_block_index // provisionomics.block_per_epoch
    dusk_chain_epoch_fraction = (dusk_chain_block_index % provisionomics.block_per_epoch) / provisionomics.block_per_epoch

    dusk_chain_period_index = dusk_chain_block_index // provisionomics.block_per_period
    dusk_chain_period_fraction = (dusk_chain_block_index % provisionomics.block_per_period) / provisionomics.block_per_period

    distinguished_keys = set((provisionomics.dusk_development_fund_address,))


    dusk_dusk_per_lux = 1 / provisionomics.dusk_lux_per_dusk

    development_fund_provisoner, = (provisioner for provisioner in provisioners if provisioner.key in distinguished_keys)
    dusk_development_fund_reward_lux = development_fund_provisoner.reward
    dusk_development_fund_reward_dusk = dusk_development_fund_reward_lux * dusk_dusk_per_lux
    #dusk_development_fund_reward_dusk_per_block = round(dusk_development_fund_reward_dusk / dusk_chain_block_index, 5)

    # remove distinguished provisioners from list we work with
    provisioners = tuple(provisioner for provisioner in provisioners if provisioner.key not in distinguished_keys)

    # this order provides slightly better numerics for the sums
    provisioners = sorted(provisioners, key=lambda provisioner: provisioner.reward + provisioner.locked_amt + provisioner.amount)

    dusk_provisioners_stake_active_dusk = sum(provisioner.amount for provisioner in provisioners if provisioner.amount >= provisionomics.stake_min_lux and dusk_chain_block_index >= provisioner.eligibility) * dusk_dusk_per_lux
    dusk_provisioners_stake_pending_dusk = sum(provisioner.amount for provisioner in provisioners if provisioner.amount >= provisionomics.stake_min_lux and dusk_chain_block_index < provisioner.eligibility) * dusk_dusk_per_lux
    dusk_provisioners_stake_low_dusk = sum(provisioner.amount for provisioner in provisioners if provisioner.amount < provisionomics.stake_min_lux) * dusk_dusk_per_lux

    dusk_provisioners_reward_lux = sum(provisioner.reward for provisioner in provisioners)
    dusk_provisioners_reward_dusk = sum(provisioner.reward for provisioner in provisioners) * dusk_dusk_per_lux
    dusk_provisioners_locked_dusk = sum(provisioner.locked_amt for provisioner in provisioners) * dusk_dusk_per_lux

    dusk_provisioners_stake_genesis_dusk = sum(provisioner.amount for provisioner in provisioners if provisioner.amount >= provisionomics.stake_min_lux and provisioner.eligibility == 0) * dusk_dusk_per_lux

    dusk_provisioners_slash_soft_slash = sum(provisioner.faults for provisioner in provisioners)
    dusk_provisioners_slash_hard_slash = sum(provisioner.hard_faults for provisioner in provisioners)

    dusk_provisioner_stake_active_count = sum(provisioner.amount >= provisionomics.stake_min_lux and dusk_chain_block_index >= provisioner.eligibility for provisioner in provisioners)
    dusk_provisioner_stake_pending_count = sum(provisioner.amount >= provisionomics.stake_min_lux and dusk_chain_block_index < provisioner.eligibility for provisioner in provisioners)
    dusk_provisioner_stake_low_count = sum(0 < provisioner.amount < provisionomics.stake_min_lux for provisioner in provisioners)
    dusk_provisioner_stake_zero_count = sum(provisioner.amount == 0 for provisioner in provisioners)

    dusk_provisioner_reward_count = sum(provisioner.reward > 0 for provisioner in provisioners)
    dusk_provisioner_locked_count = sum(provisioner.locked_amt > 0 for provisioner in provisioners)

    dusk_provisioner_stake_genesis_count = sum(provisioner.amount >= provisionomics.stake_min_lux and provisioner.eligibility == 0 for provisioner in provisioners)

    dusk_provisioner_slash_soft_count = sum(provisioner.faults > 0 for provisioner in provisioners)
    dusk_provisioner_slash_hard_count = sum(provisioner.hard_faults > 0 for provisioner in provisioners)

    dusk_provisioner_owner_same_count = sum(provisioner.key == provisioner.owner.Account for provisioner in provisioners)
    dusk_provisioner_owner_different_count = sum(provisioner.key != provisioner.owner.Account for provisioner in provisioners)

    dusk_provisioner_anomalous_keys = sorted(provisioner.key for provisioner in provisioners if provisioner.amount < provisionomics.stake_min_lux)
    #dusk_provisioner_anomalous_keys = sorted(provisioner.key for provisioner in provisioners if provisioner.amount < provisionomics.stake_min_lux and provisioner.key != development_fund_provisoner.key)

    dusk_provisioning_summary = attrdict(

        timestamp_hr = now_utc_sec.strftime('%Y-%m-%d %H:%M:%S %Z, %A'),
        timestamp_tag = now_utc_sec.strftime('%Y-%m-%d-%H%M-%S'),
        timestamp_sec = int(now_utc_sec.timestamp()),


        dusk_node_scheme_host_port = node_info.dusk_node_scheme_host_port,
        dusk_node_ip = node_info.dusk_node_ip,
        dusk_node_version = node_info.dusk_node_version,
        dusk_chain_id = node_info.dusk_chain_id,

        dusk_chain_block_hash = block_hash if block_hash is not None else 'unavailable',
        dusk_chain_block_index = dusk_chain_block_index,
        dusk_chain_trigger_index = trigger_height,

        dusk_chain_epoch_index = dusk_chain_epoch_index,
        dusk_chain_epochblock_index = dusk_chain_epochblock_index,
        dusk_chain_epochblock_percent = f'{dusk_chain_epochblock_index/provisionomics.block_per_epoch*100:.2f}%',
        #dusk_chain_epoch_fraction = round(dusk_chain_epoch_fraction, 4),
        #dusk_chain_epoch_fraction_hr = f'{dusk_chain_epoch_fraction*100:.2f}%',

        #dusk_chain_period_index = dusk_chain_period_index,
        #dusk_chain_period_fraction = round(dusk_chain_period_fraction, 7),
        #dusk_chain_period_fraction_hr = f'{dusk_chain_period_fraction*100:.5f}%',

        dusk_development_fund_reward_lux = dusk_development_fund_reward_lux,
        dusk_development_fund_reward_dusk = round(dusk_development_fund_reward_dusk, 9),
        #dusk_development_fund_reward_dusk_per_block = dusk_development_fund_reward_dusk_per_block,

        dusk_provisioners_stake_active_dusk = round(dusk_provisioners_stake_active_dusk, 9),
        dusk_provisioners_stake_pending_dusk = round(dusk_provisioners_stake_pending_dusk, 9),

        dusk_provisioners_reward_lux = dusk_provisioners_reward_lux,
        dusk_provisioners_reward_dusk = round(dusk_provisioners_reward_dusk, 9),
        dusk_provisioners_locked_dusk = round(dusk_provisioners_locked_dusk, 9),

        dusk_provisioners_stake_low_dusk = round(dusk_provisioners_stake_low_dusk, 9),
        dusk_provisioners_stake_genesis_dusk = round(dusk_provisioners_stake_genesis_dusk, 9),

        dusk_provisioners_slash_soft_slash = dusk_provisioners_slash_soft_slash,
        dusk_provisioners_slash_hard_slash = dusk_provisioners_slash_hard_slash,

        dusk_provisioner_count = len(provisioners),
        dusk_provisioner_stake_active_count = dusk_provisioner_stake_active_count,
        dusk_provisioner_stake_pending_count = dusk_provisioner_stake_pending_count,

        dusk_provisioner_reward_count = dusk_provisioner_reward_count,
        dusk_provisioner_locked_count = dusk_provisioner_locked_count,

        dusk_provisioner_stake_low_count = dusk_provisioner_stake_low_count,
        dusk_provisioner_stake_zero_count = dusk_provisioner_stake_zero_count,
        dusk_provisioner_stake_genesis_count = dusk_provisioner_stake_genesis_count,

        dusk_provisioner_slash_soft_count = dusk_provisioner_slash_soft_count,
        dusk_provisioner_slash_hard_count = dusk_provisioner_slash_hard_count,

        dusk_provisioner_owner_same_count = dusk_provisioner_owner_same_count,
        dusk_provisioner_owner_different_count = dusk_provisioner_owner_different_count,

        dusk_provisioner_anomalous_keys = dusk_provisioner_anomalous_keys,
    )

    return dusk_provisioning_summary

async def dusk_provisioning(dusk_node_scheme_host_port, *, trigger_height=None, block_hash=None):
    coros = (
        get_node_info(dusk_node_scheme_host_port),
        get_dusk_chain_block_index(dusk_node_scheme_host_port),
        get_dusk_provisioners(dusk_node_scheme_host_port),
    )

    provisioning_thunk = functools.partial(asyncio.gather, *coros, return_exceptions=False)

    now_utc_sec = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    node_info, dusk_chain_block_index, provisioners = await provisioning_thunk()

    dusk_provisioning_summary = make_provisioning_summary(now_utc_sec, node_info, dusk_chain_block_index, trigger_height, block_hash, provisioners)
    dusk_provisioner_anomalous_keys = dusk_provisioning_summary.dusk_provisioner_anomalous_keys
    del dusk_provisioning_summary.dusk_provisioner_anomalous_keys


    # reproducible ordering for emitted record
    provisioners.sort(key=lambda provisioner: provisioner.key)

    provisioning = attrdict(
        dusk_provisioning_summary = dusk_provisioning_summary,
        dusk_provisioner_anomalous_keys = dusk_provisioner_anomalous_keys,
        dusk_provisioner_list = provisioners,
    )

    return provisioning


#@asyncify
def json_dump(obj, basename_abs):
#def json_dump(obj, filename):
    filename = basename_abs + '.json'
    print(f'json_dump: start: filename: {filename}, type(obj): {type(obj)}', flush=True)
    with open(filename, 'wt') as out_file:
        print(json.dumps(obj), file=out_file)
    #print(f'json_dump: done', flush=True)

#@asyncify
def pickle_dump(obj, basename_abs):
#def pickle_dump(obj, filename):
    #filename = filename.replace('.json', '.pkl')
    filename = basename_abs + '.pkl'
    print(f'pickle_dump: start: filename: {filename}, type(obj): {type(obj)}', flush=True)
    with open(filename, 'wb') as out_file:
        pickle.dump(obj, out_file)
    #print(f'json_dump: done', flush=True)

@asyncify
def do_persist(provisioning, provisioning_dir_abs):
    summary = provisioning.dusk_provisioning_summary
    #await printio(f'{json.dumps(foon)}')
    #period = provisioning.dusk_chain_period_index
    # TODO: fix me
    #epoch_of_period = provisioning.dusk_chain_epoch_index
    epoch_name = f'epoch-{summary.dusk_chain_epoch_index:04}'
    epoch_dir_abs = os.path.join(provisioning_dir_abs, epoch_name)
    os.makedirs(epoch_dir_abs, exist_ok=True)

    basename = f'dusk-provisioning_block-{summary.dusk_chain_block_index:07}_{epoch_name}_epochblock-{summary.dusk_chain_epochblock_index:04}_{summary.timestamp_tag}'
    basename_abs = os.path.join(epoch_dir_abs, basename)
    #basename_abs = os.path.join(provisioning_dir_abs, basename)

    filename = f'dusk-provisioning_block-{summary.dusk_chain_block_index:07}_{epoch_name}_epochblock-{summary.dusk_chain_epochblock_index:04}_{summary.timestamp_tag}.json'
    filename_abs = os.path.join(epoch_dir_abs, filename)
    #filename_abs = os.path.join(provisioning_dir_abs, filename)
    #await printio(f'filename_abs: {filename_abs}')

    #json_dump(provisioning, basename_abs)
    # JSON round trip to make generic rather than attrdict
    pickle_dump(json.loads(json.dumps(provisioning)), basename_abs)
    #pickle_dump(provisioning, basename_abs)
    #json_dump(provisioning, filename_abs)
    #pickle_dump(provisioning, filename_abs)

async def do_dusk_provisioning(dusk_node_scheme_host_port, provisioning_dir_abs, *, trigger_height=None, block_hash=None):
    provisioning = await dusk_provisioning(dusk_node_scheme_host_port, trigger_height=trigger_height, block_hash=block_hash)

    await do_persist(provisioning, provisioning_dir_abs)

    return provisioning

async def run_dusk_provisioning(dusk_node_scheme_host_port):
    block_per_interval = provisionomics.block_per_epoch // 3

    while True:
        try:
            do_dusk_provisioning(dusk_node_scheme_host_port, '.')

            some_index = provisioning.dusk_chain_block_index // block_per_interval
            block_next = (some_index + 1) * block_per_interval
            sleep_sec = (block_next - provisioning.dusk_chain_block_index) * 10
            await printio(f'sleep_sec: {sleep_sec}')
            #sleep_sec = provisioning.dusk_chain_block_index + 20
            await asyncio.sleep(sleep_sec)
        except:
            raise
            await asyncio.sleep(23)

class attrdict(dict):
    # Access dict entries with dot notation. Good enough for API JSON work, but doesn't play well with introspective tools, e.g. pydantic.
    def __getattr__(self, key): return self[key]
    def __setattr__(self, key, value): self[key] = value
    def __delattr__(self, key): del self[key]

    @staticmethod
    def deep(obj):
        def obj_recurse(obj):
            if isinstance(obj, tuple): return tuple(obj_recurse(item) for item in obj)
            if isinstance(obj, list): return list(obj_recurse(item) for item in obj)
            if isinstance(obj, dict): return attrdict((key, obj_recurse(value)) for key, value in obj.items())
            return obj
        return obj_recurse(obj)

provisionomics = attrdict.deep(provisionomics)


if __name__ == "__main__":

    async def main(args):

        default_dusk_node_scheme_host_port = 'https://nodes.dusk.network'

        forever = False
        while '--forever' in args:
            forever = True
            args.remove('--forever')

        dusk_node_scheme_host_port = args[0] if len(args) > 0 else default_dusk_node_scheme_host_port

        try:
            if forever:
                await run_dusk_provisioning(dusk_node_scheme_host_port)
                assert False, str(('intended to be unreachable following call to run_dusk_provisioning'))
            else:
                provisioning = await dusk_provisioning(dusk_node_scheme_host_port)
                await printio(json.dumps(provisioning))
        except Exception as err:
            error_message = attrdict(
                script = sys.argv[0],
                args = args,
                error = f'{err}',
                usage = f'{sys.argv[0]} [--forever] [schema-host-port]',
                examples = (
                    f'{sys.argv[0]} {default_dusk_node_scheme_host_port}',
                    f'{sys.argv[0]} --forever http://localhost:8080',
                )

            )
            await printio(json.dumps(error_message))
            sys.exit(1)

    asyncio.run(main(sys.argv[1:]))
