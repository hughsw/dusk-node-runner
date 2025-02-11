#!/usr/bin/env python3

# provisioning.py -- Capture timestamp and current Dusk provisioners info as JSON to stdout
#   Optional arg1 is scheme-host-port of Dusk node to queuy:
#     e.g.:     http://localhost:8080
#     default:  https://nodes.dusk.network
#
# Copyright (C) 2025  20 Octaves, LLC
# Apache License 2.0 (https://www.apache.org/licenses/LICENSE-2.0.txt)

import sys
import asyncio 
import datetime
import json
import requests
import functools


printio = functools.partial(asyncio.to_thread, print)
getio = functools.partial(asyncio.to_thread, requests.get)
postio = functools.partial(asyncio.to_thread, requests.post)

provisionomics = dict(
    # https://docs.dusk.network/learn/tokenomics/
    block_per_epoch = 2160,
    block_per_period = 12_614_400,
    dusk_lux_per_dusk = 1_000_000_000,
    )

async def get_dusk_chain_block_index(dusk_node_scheme_host_port):
    block_height_uri = f'{dusk_node_scheme_host_port}/on/graphql/query'
    block_height_query = b'query { block(height: -1) { header { height } } }'
    block_result = await postio(block_height_uri, data=block_height_query)

    return attrdict.deep(block_result.json()).block.header.height

async def get_dusk_provisioners(dusk_node_scheme_host_port):
    provisioners_uri = f'{dusk_node_scheme_host_port}/on/node/provisioners'
    provisioners_result = await postio(provisioners_uri)

    return attrdict.deep(provisioners_result.json())

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

async def dusk_provisioning(dusk_node_scheme_host_port):
    calls = (
        get_node_info(dusk_node_scheme_host_port), 
        get_dusk_chain_block_index(dusk_node_scheme_host_port),
        get_dusk_provisioners(dusk_node_scheme_host_port), 
    )

    #provisioning_thunk = functools.partial(asyncio.gather, *calls, return_exceptions=True)
    provisioning_thunk = functools.partial(asyncio.gather, *calls, return_exceptions=False)

    now_utc_sec = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    node_info, dusk_chain_block_index, provisioners = await provisioning_thunk()

    provisioners.sort(key=lambda provisioner: (600_000-(provisioner.reward+provisioner.locked_amt+provisioner.amount), provisioner.key))


    dusk_chain_active_stake_dusk = sum(provisioner.amount for provisioner in reversed(provisioners) if provisioner.eligibility <= dusk_chain_block_index) * (1 / provisionomics.dusk_lux_per_dusk)

    dusk_chain_epoch_index = dusk_chain_block_index // provisionomics.block_per_epoch
    dusk_chain_epoch_fraction = (dusk_chain_block_index % provisionomics.block_per_epoch) / provisionomics.block_per_epoch

    dusk_chain_period_index = dusk_chain_block_index // provisionomics.block_per_period
    dusk_chain_period_fraction = (dusk_chain_block_index % provisionomics.block_per_period) / provisionomics.block_per_period

    provisioning = attrdict(
        timestamp_hr = now_utc_sec.strftime('%Y-%m-%d %H:%M:%S %Z, %A'),
        timestamp_tag = now_utc_sec.strftime('%Y-%m-%d-%H%M-%S'),
        timestamp_sec = int(now_utc_sec.timestamp()),

        dusk_node_scheme_host_port = dusk_node_scheme_host_port,
        dusk_node_ip = node_info.dusk_node_ip,
        dusk_node_version = node_info.dusk_node_version,
        dusk_chain_id = node_info.dusk_chain_id,

        dusk_chain_block_index = dusk_chain_block_index,

        dusk_chain_epoch_index = dusk_chain_epoch_index,
        dusk_chain_epoch_fraction = round(dusk_chain_epoch_fraction, 4),
        dusk_chain_epoch_fraction_hr = f'{dusk_chain_epoch_fraction*100:.2f}%',

        dusk_chain_period_index = dusk_chain_period_index,
        dusk_chain_period_fraction = round(dusk_chain_period_fraction, 7),
        dusk_chain_period_fraction_hr = f'{dusk_chain_period_fraction*100:.5f}%',

        dusk_chain_active_stake_dusk = dusk_chain_active_stake_dusk,
        dusk_chain_provisioners = provisioners,
    )


    return provisioning


async def run_dusk_provisioning(dusk_node_scheme_host_port):
    block_per_interval = provisionomics.block_per_epoch // 3

    while True:
        try:
            provisioning = await dusk_provisioning(dusk_node_scheme_host_port)
            #await printio(f'{json.dumps(foon)}')
            period = provisioning.dusk_chain_period_index
            # TODO: fix me
            epoch_of_period = provisioning.dusk_chain_epoch_index
            block_of_epoch = provisioning.dusk_chain_block_index % provisionomics.block_per_epoch
            filename = f'dusk-provisioning_{provisioning.dusk_chain_block_index:07}_epoch-{epoch_of_period:04}_eplock-{block_of_epoch:04}_{provisioning.timestamp_tag}.json'
            await printio(f'filename: {filename}')
            with open(filename, 'wt') as out_file:
                print(json.dumps(provisioning), file=out_file)

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
