#!/usr/bin/env python3

# dusk-reward-delta.py -- For each Dusk chain blcok, log the reward delta to provisioners as JSON to stdout
#
# Copyright (C) 2025  20 Octaves, LLC
# Apache License 2.0 (https://www.apache.org/licenses/LICENSE-2.0.txt)

import sys, os
import asyncio
import datetime
import json
import time
import requests
import functools
from functools import partial

import websockets.exceptions
from websockets.exceptions import ConnectionClosedOK, WebSocketException
from websockets.asyncio.client import connect

from utils import asyncify

printio = functools.partial(asyncio.to_thread, print)
getio = functools.partial(asyncio.to_thread, requests.get)
postio = functools.partial(asyncio.to_thread, requests.post)


provisioning_dir = os.environ.get('DUSKIES_PROVISIONING_DIR') or 'provisioning-records'
provisioning_dev_dir = os.environ.get('DUSKIES_PROVISIONING_DEV_DIR') or provisioning_dir + '-dev'

rues_host = os.environ.get('DUSKIES_RUES_HOST') or 'nodes.dusk.network'
use_tls = os.environ.get('DUSKIES_USE_TLS') or True

provisioning_dir_abs = os.path.abspath(provisioning_dir)
provisioning_dev_dir_abs = os.path.abspath(provisioning_dev_dir)

tls_maybe = 's' if use_tls else ''
WS_SCHEME = 'ws' + tls_maybe
HTTP_SCHEME = 'http' + tls_maybe



root_path = 'on'

rues_host_path = f'{rues_host}/{root_path}'

ws_uri = f'{WS_SCHEME}://{rues_host_path}'
http_uri = f'{HTTP_SCHEME}://{rues_host_path}'

dusk_node_scheme_host_port = f'{HTTP_SCHEME}://{rues_host}'

_, SCRIPT = os.path.split(__file__)

_printio = partial(asyncio.to_thread, print)
async def printio(*args, **kwargs):
    await _printio(f'{SCRIPT} :', *args, **kwargs, flush=True)

provisionomics = dict(
    # https://docs.dusk.network/learn/tokenomics/
    block_per_epoch = 2160,
    block_per_period = 12_614_400,
    dusk_lux_per_dusk = 1_000_000_000,
    stake_min_lux = 1_000_000_000_000,
    dusk_development_fund_address = 'o1YvWG34EBTwdskfZ7PCvWKRUWKzskVnhJNjZHdau6VaUNpgDxpoSsisK8KGF6FayUi8Lzn4taAvZcHGprQuPsqFGH66SEPDRCbTmKGVwFYX7bEp2rF4wekvoc4dS8ghnKf',
    default_dusk_node_scheme_host_port = 'https://nodes.dusk.network',
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


@asyncify
def json_dump(obj, filename):
    print(f'json_dump: start: filename: {filename}, type(obj): {type(obj)}', flush=True)
    with open(filename, 'wt') as out_file:
        print(json.dumps(obj), file=out_file)
    #print(f'json_dump: done', flush=True)

async def do_dusk_provisioning(dusk_node_scheme_host_port, provisioning_dir_abs, *, trigger_height=None, block_hash=None):
    provisioning = await dusk_provisioning(dusk_node_scheme_host_port, trigger_height=trigger_height, block_hash=block_hash)
    #await printio(f'{json.dumps(foon)}')
    #period = provisioning.dusk_chain_period_index
    # TODO: fix me
    #epoch_of_period = provisioning.dusk_chain_epoch_index
    summary = provisioning.dusk_provisioning_summary
    filename = f'dusk-provisioning_block-{summary.dusk_chain_block_index:07}_epoch-{summary.dusk_chain_epoch_index:04}_epochblock-{summary.dusk_chain_epochblock_index:04}_{summary.timestamp_tag}.json'
    filename_abs = os.path.join(provisioning_dir_abs, filename)
    #await printio(f'filename_abs: {filename_abs}')

    await json_dump(provisioning, filename_abs)

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

def unpack_event(event, *, json_raw_decode = json.JSONDecoder().raw_decode):
    tag = event[:1].decode()
    assert event[1:4] == b'\0\0\0', str((tag, event[1:4], event,))

    # Note: should use a raw decode?
    payload = event[4:].decode()
    offset = 0
    items = list()
    while offset < len(payload):
        try:
            item, extent = json_raw_decode(payload[offset:])
            items.append(attrdict.deep(item))
            offset += extent
        except:
            items.append(attrdict(rest=payload[offset:]))
            offset = len(payload)

    location = items[0]['Content-Location']
    parts = location.split('/')[2:]
    type = parts[0].split(':')[0]
    topic = parts[1]
    event_type = f'{type}/{topic}'

    content = attrdict(items[1])
    # grrr, separation of concerns
    if event_type == 'blocks/statechange':
        event_type += f'/{content.state}'

    return attrdict(tag=tag, event_type=event_type, location=location, content=content, items=items[2:])

async def go():
    while True:
        try:
            websocket = None
            async with connect(ws_uri) as websocket:
                connection_timestamp = time.time()
                #startup_end_timestamp = connection_timestamp + block_run * sec_per_block + block_run // 2

                address, port = websocket.remote_address
                await printio(f'rues_host_path: {rues_host_path}, address: {address}, port: {port}')

                rusk_session_id = await websocket.recv()
                await printio(f'rusk_session_id: {rusk_session_id}')

                headers = {'Rusk-Session-Id': rusk_session_id}

                events_to_watch = (
                    'blocks/accepted',
                    #'blocks/statechange',
                    )

                await printio(f'watch:')
                for event_to_watch in events_to_watch:
                    url = f'{http_uri}/{event_to_watch}'
                    await printio(f'  {url}')

                    response = await getio(url, headers=headers)
                    await printio(f'    response: {response}, response.content: {response.content}')

                ping_latency_msec = 1000 * (await (await websocket.ping()))
                await printio(f'ping_latency_msec: {ping_latency_msec:_.6}')

                await printio()
                while True:
                    event = None
                    try:
                        event = await websocket.recv()
                        client_timestamp = time.time()

                        event_type = event[0:1]
                        match event_type:
                            case b'n':
                                # block confirmed or block finalized
                                await block_stats.event(event, client_timestamp)
                                #await blocks_statechange(event, client_timestamp)
                            case b'k':
                                # block accepted
                                details = unpack_event(event)
                                block_height = details.content.header.height
                                block_hash = details.content.header.hash
                                summary = await do_dusk_provisioning(dusk_node_scheme_host_port, provisioning_dir_abs, trigger_height=block_height, block_hash=block_hash)

                                set_most_recent_summary(summary)
                                set_most_recent_summary_diff(summary)

                                if False:
                                    # dump on trigger heights and for some time after startup
                                    if height % block_per_epoch in trigger_heights or client_timestamp < startup_end_timestamp:
                                        await printio(f'trigger: height: {height:_}')
                                        await do_dusk_provisioning(dusk_node_scheme_host_port, provisioning_dir_abs, trigger_height=height)

                                #await block_stats.event(event, client_timestamp)
                                #await blocks_accepted(event, client_timestamp)
                            case _ as unhandled:
                                await printio(f'\nunhandled: {unhandled}, event_type: {repr(event_type)}, event: {event}')

                    except asyncio.CancelledError:
                        raise
                    except BaseException as e:
                        await printio(f'\nexception: {type(e).__name__}: {e} : line: {e.__traceback__.tb_lineno}, event: {event}')
                        raise

        except WebSocketException as e:
            await printio(f'\n{type(e).__name__}: {e} : will attempt reconnect')
            await asyncio.sleep(5)
            continue

        except asyncio.CancelledError as e:
            await printio(f'\nasyncio.CancelledError : provisionator will exit')
            # task.cancel() or Ctrl-C, so quit the "forever" loop
            break

        finally:
            if websocket is not None:
                await websocket.close()



if __name__ == "__main__":

    async def main(args):

        await go()

        1/0


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
