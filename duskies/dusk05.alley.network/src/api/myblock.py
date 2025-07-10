#!/home/duskadmin/pyvenv/bin/python3

# Alert on public key being the block generator

# see: https://docs.dusk.network/developer/integrations/rues/
# and: curl -sSL -X POST https://nodes.dusk.network/on/graphql/query
#        http://localhost:8080/on/graphql/query

import asyncio
import requests
import json
import time
from functools import partial
import websockets.exceptions
#print(f'dir(websockets.exceptions): {sorted(dir(websockets.exceptions))}')
from websockets.exceptions import ConnectionClosedOK, WebSocketException
from websockets.asyncio.client import connect

addresses_str = '21mif6HvgdLoJtLzibs42LZDtnwkf3518yfhBsTfVim2WZa3j8H9E64JHK4KWdc7W5KMDvoMk7zdY9ddeE1VuNQsks1suJzWDNf5mL5yBqjzdkdfWPaJjyg4rvJ1GqREuDBq,uF2f77E9ezKnWxs5TudPAwnFFLqwMJwXABraC3oWaVbjPCwsAJfsJoGBR571W2nyMCKuWaTDqWBjXbLm8HWak2mAuCrXTvoFw3vjioVAcv5nUC7qQ9HKA5i1cNCd78WEHjt,nJsNHjb9k6XXBZ7iXPESkspnSrV5vQJf83j7kuQhTtFc82Z6EzHKWtyTxXMHSCZGJCNifWsZkTz9vxxQiTdYPZGiMFK93JX3LWcE69KuwMrdiEiCDKwEBow4LkG9RoAubCs'

addresses = frozenset(addresses_str.split(','))

#rues_host = 'dusk03.alley.network'
rues_host = 'nodes.dusk.network'

is_tls = True
#rues_host = 'localhost:8080'
#is_tls = False


tls_maybe = 's' if is_tls else ''
WS_SCHEME = 'ws' + tls_maybe
HTTP_SCHEME = 'http' + tls_maybe

root_path = 'on'

rues_host_path = f'{rues_host}/{root_path}'

ws_uri = f'{WS_SCHEME}://{rues_host_path}'
http_uri = f'{HTTP_SCHEME}://{rues_host_path}'

#ws_uri = 'wss://nodes.dusk.network/on'
#http_uri = 'https://nodes.dusk.network/on'

_printio = partial(asyncio.to_thread, print)
async def printio(*args, **kwargs):
    await _printio(*args, **kwargs, flush=True)

getio = partial(asyncio.to_thread, requests.get)

#def printio(*args, **kwargs):
#    return asyncio.to_thread(print, *args, **kwargs)

class BlockStats(object):

    def __init__(self):
        self.client_timestamp_prev = None
        self.client_timestamp_finalized_prev = None

    async def event(self, event, client_timestamp):
        details = unpack_event(event)
        details.client_timestamp = client_timestamp
        details.client_timestamp_interval = client_timestamp - self.client_timestamp_prev if self.client_timestamp_prev is not None else None
        if details.event_type == 'blocks/statechange/finalized':
            details.client_finalized_interval = client_timestamp - self.client_timestamp_finalized_prev if self.client_timestamp_finalized_prev is not None else None
            self.client_timestamp_finalized_prev = client_timestamp
        self.client_timestamp_prev = client_timestamp

        await printio(f'BlockStats.event: details: {json.dumps(details)}')

async def hello():
    await printio(f'hello():')

    block_stats = BlockStats()

    while True:
        try:
            websocket = None
            if False:
                # Ding!
                with open('/dev/tty', 'wb') as tty:
                    tty.write(b'\a\n')
                    #await printio('\a', end='', file=tty)

            async with connect(ws_uri) as websocket:
                #await websocket.send("Hello world!")
                address, port = websocket.remote_address
                #https_host = f'https://{address}:{port}/on'

                await printio(f'rues_host_path: {rues_host_path}, address: {address}, port: {port}')
                #await printio(f'address: {address}, port: {port}, https_host: {https_host}')

                #await printio(f'websocket.remote_address 2: {websocket.remote_address}')

                rusk_session_id = await websocket.recv()
                #await printio(f'websocket.remote_address 3: {websocket.remote_address}')
                await printio(f'rusk_session_id: {rusk_session_id}')

                headers = {'Rusk-Session-Id': rusk_session_id}

                events_to_watch = (
                    #'blocks/',
                    'blocks/accepted',
                    'blocks/statechange',
                    'transactions/Executed',
                    'contracts/',
                    #'contracts:/',
                    'contracts/deploy',
                    'contracts:0200000000000000000000000000000000000000000000000000000000000000/',
                    )

                await printio(f'watch:')
                for event_to_watch in events_to_watch:
                    url = f'{http_uri}/{event_to_watch}'
                    #url = f'{http_uri}/transactions/Executed'
                    #url = f'{https_host}/transactions/Executed'
                    #url = 'https://nodes.dusk.network/on/node/provisioners'

                    await printio(f'  {url}')

                    response = await getio(url, headers=headers)
                    await printio(f'    response: {response}, response.content: {response.content}')

                await printio(f'public keys:')
                for key in sorted(addresses):
                    await printio(f'  {key}')

                #ping = await websocket.ping()
                #await printio(f'ping: {ping}')
                #ping_latency_msec = 1000 * (await ping)
                ping_latency_msec = 1000 * (await (await websocket.ping()))
                await printio(f'ping_latency_msec: {ping_latency_msec:_.6}')

                await printio()
                while True:
                    event = None
                    try:
                        event = await websocket.recv()
                        client_timestamp = time.time()
                        #await printio(f'type(event): {type(event)}')
                        #await printio(f'event: {repr(event)}')
                        #if event.find(b'21mif6HvgdLoJtLzibs42LZDtnwkf3518yfhBsTfVim2WZa3j8H9E64JHK4KWdc7W5KMDvoMk7zdY9ddeE1VuNQsks1suJzWDNf5mL5yBqjzdkdfWPaJjyg4rvJ1GqREuDBq') >= 0:
                        #    await printio(f'My block!!')

                        #await printio('.', end='', flush=True)

                        event_type = event[0:1]
                        match event_type:
                            case b'q':
                                await transactions(event, client_timestamp)
                                #await printio('transactions')
                            case b'n':
                                await block_stats.event(event, client_timestamp)
                                #await blocks_statechange(event, client_timestamp)
                            case b'k':
                                await block_stats.event(event, client_timestamp)
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
            await printio(f'\nasyncio.CancelledError : hello will exit')
            # task.cancel() or Ctrl-C, so quit the "forever" loop
            break

        finally:
            if websocket is not None:
                await websocket.close()



"""
event: b'q\x00\x00\x00{"Content-Location":"/on/transactions:b58fe26af6c42a29d4ebf0a91ce5746eebad1b2bff46af1cce243fc901b25f26/executed"}{"block_height":73206,"err":null,"gas_spent":26031433,"inner":{"call":{"contract":"0200000000000000000000000000000000000000000000000000000000000000","fn_args":"AQAAAAAAAABGyYhcpgiuqAMfoQN364BYNGeImgjqSah+kMJu/N7l1EzTlCnXhj+MpoUH39IMxQ6CsQWlb4tMv5x1ZXgWuT3dDu/d1cn4jx4eqPevBneWrMsci9cnEiqSmX68RJiJ/Q+fPofrCx19RTFxEpHr24ZzkkiG2p+bm7BQL573tBYeIsuMDLDa1tzWBM5HddJtdQo6VnEXtdEgM+2/Oq4k0bBzHVBLD/+UGGcMqcYo7NBsNmUIH8u00ERybWKPNHyMRwQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEAAAAAAAAABgAAAAAAAAABAAAAAAAAAAn0XmDpqbWdGjF22nRKVi2MR0XSu8V7ectlqILoxJkx0GWAaJ8JxgXUs55WgLJwCxwCAW2csYwG9qJjOCsCZCCCMGHJYqytxxkFoy6EHC+NzEIYftNGdesYo+afIo38DwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA1wQzWKwAAABGyYhcpgiuqAMfoQN364BYNGeImgjqSah+kMJu/N7l1EzTlCnXhj+MpoUH39IMxQ6CsQWlb4tMv5x1ZXgWuT3dDu/d1cn4jx4eqPevBneWrMsci9cnEiqSmX68RJiJ/Q+fPofrCx19RTFxEpHr24ZzkkiG2p+bm7BQL573tBYeIsuMDLDa1tzWBM5HddJtdQo6VnEXtdEgM+2/Oq4k0bBzHVBLD/+UGGcMqcYo7NBsNmUIH8u00ERybWKPNHyMRwQAAAAAAAAAAOCvhyiI7a7G0aYwuFu9v1h1H63x1TtBhw2ZPL/TJxMpxZgbbvt3b0ylWwfawCzuE4z2x6aZD0QqU3nMKnYVgPZYgAV+I6tkFq0k5j8r9seahG+AVN8OMBt2E784v+WuDAAAAAAAAAAA4K+HKIjtrsbRpjC4W72/WHUfrfHVO0GHDZk8v9MnEynFmBtu+3dvTKVbB9rALO4TjPbHppkPRCpTecwqdhWA9liABX4jq2QWrSTmPyv2x5qEb4BU3w4wG3YTvzi/5a4MAAAAAAAAAAA=","fn_name":"withdraw"},"deposit":0,"fee":{"gas_limit":"100000000","gas_price":"1","refund_address":"t3hhgUWKSMJFrTHA9kHgCX7PkovZy5XS8LEFMm5wrSaADjD5kv6VWYsuEmYMhfwvdoxbL5cgfka6pPyNwKrWo33erV1zt1yb1ysJu6roX9JCFHSQ9mVButSAvvpCSSPfcE9"},"is_deploy":false,"memo":null,"nonce":6,"receiver":null,"sender":"t3hhgUWKSMJFrTHA9kHgCX7PkovZy5XS8LEFMm5wrSaADjD5kv6VWYsuEmYMhfwvdoxbL5cgfka6pPyNwKrWo33erV1zt1yb1ysJu6roX9JCFHSQ9mVButSAvvpCSSPfcE9","type":"moonlight","value":0}}'
event: b'n\x00\x00\x00{"Content-Location":"/on/blocks:007b84d08360c59359a0afc8c8dc29a4fbac9168282fb56276bf23ee2e1480e1/statechange"}{"atHeight":73206,"state":"confirmed"}'
event: b'n\x00\x00\x00{"Content-Location":"/on/blocks:007b84d08360c59359a0afc8c8dc29a4fbac9168282fb56276bf23ee2e1480e1/statechange"}{"atHeight":73206,"state":"finalized"}'
event: b'k\x00\x00\x00{"Content-Location":"/on/blocks:a27e812a9df93b5695cd672a56cbce15ee3e5852b451873bf10f4933ab50956d/accepted"}{"header":{"event_bloom":"00000000000200000000000100000000000000000000000000000400010000000000000000000008000000000000000000000000000000000000000000000000000000000000040000000000000000000000000000000000000000000000000000001002000000000000000000000000000000000000000200000000000008000000000000000000000000000000000000000000000000003000000008000080000000000000000000000000000000000000008000000000000000000000000001000800000002000000000000000000000000000000000000000000000000000000000000000000000000000202000000040000000000004000000000080200","failed_iterations":[],"faultroot":"0000000000000000000000000000000000000000000000000000000000000000","gas_limit":3000000000,"generator_bls_pubkey":"sJtg9Lv7N5wXhkpdKmV14AfvET9fKvBL7nnhtSFEs15rgSMzpbs2y6157QoeUneFhfG3KjNvmMRqV3QKiZhxN5jMGQ3pcBQKp9bzvHAprAHejSHUh3rxxdpvSidfSJtPt3v","hash":"a27e812a9df93b5695cd672a56cbce15ee3e5852b451873bf10f4933ab50956d","height":73206,"iteration":0,"prev_block_cert":{"ratification":{"aggregate_signature":"b3640689f6afc29fdd127c0d4bc0badec23344fd5fd8456ccace31d7d9da78220420d9219147f3491f327699b66fba14","bitset":11685208971199},"result":{"Valid":"007b84d08360c59359a0afc8c8dc29a4fbac9168282fb56276bf23ee2e1480e1"},"validation":{"aggregate_signature":"b7243863329e8131441c9097ba1d4506ecab57cc78aeddc547c80858f4d6485f8903ab8653159a0f95337b30a84be2d9","bitset":1028000119712157}},"prev_block_hash":"007b84d08360c59359a0afc8c8dc29a4fbac9168282fb56276bf23ee2e1480e1","seed":"a6d48b695df8ee66a9757c5605161dd2d022538f48977899c1a49f803106e2b21079f46f00f8e0f25271cc1006bbc803","signature":"aef8d96d9aee21f9b557e95af518faa5107ec1a049fa54c785f6e2c90a282846a0677b0e4bde0219432e15103e597742","state_hash":"7a2ffede37b8938cc958eb05f1a02f154bb1538d171f471ac9941dec71adb971","timestamp":1736983472,"txroot":"bd301f07b3f46e1410c4bff33c1eebbe1e4203cd59e560e1676218c50d7bc22a","version":1},"transactions":["b58fe26af6c42a29d4ebf0a91ce5746eebad1b2bff46af1cce243fc901b25f26"]}'
"""


class attrdict(dict):
    def __getattr__(self, key):
        return self[key]
    def __setattr__(self, key, value):
        self[key] = value
    def __delattr__(self, key):
        del self[key]

def unpack_event(event, *, raw_decode = json.JSONDecoder().raw_decode):
    tag = event[:1].decode()
    assert event[1:4] == b'\0\0\0', str((tag, event[1:4], event,))

    # Note: should use a raw decode?
    payload = event[4:].decode()
    offset = 0
    items = list()
    rest = None
    while offset < len(payload):
        try:
            item, extent = raw_decode(payload[offset:])
            items.append(item)
            offset += extent
        except:
            items.append(attrdict(rest=payload[offset:]))
            offset = len(payload)

    #assert len(items) == 2, str((len(items), items, event))

    location = items[0]['Content-Location']
    parts = location.split('/')[2:]
    type = parts[0].split(':')[0]
    topic = parts[1]
    event_type = f'{type}/{topic}'

    content = attrdict(items[1])
    # grrr, separation of concerns
    if event_type == 'blocks/statechange':
        event_type += f'/{content.state}'

    return attrdict(tag=tag, event_type=event_type, location=location, content=content, items=items[2:], rest=rest)


# babylonian digits
def base60p(num, *, babyl='.123456789abcdefghijkmnopqrstuvwxyzABCDEFGHIJKLMNPQRSTUVWXYZ'):
    return babyl[num] if num < len(babyl) else '+'

async def blocks_statechange(event, client_timestamp):
    details = unpack_event(event)
    #tag, items = unpack_event(event)

    assert details.tag == 'n', str(('n', details.tag, event,))

    await printio(f'blocks_statechange: details: {json.dumps(details)}')
    return

    #await printio(f'items: {json.dumps(items)}')
    header = details.content['header']
    height = header['height']
    timestamp = header['timestamp']
    generator_bls_pubkey = header['generator_bls_pubkey']
    transactions_len = len(details.content['transactions'])
    babyl = base60p(transactions_len)
    await printio(f'{babyl}', end='', flush=True)
    #await printio(f'generator_bls_pubkey: {generator_bls_pubkey}')
    if generator_bls_pubkey in addresses:
        await printio(f'\a\nMy block !! :  height: {height}, timestamp: {timestamp:_}, generator_bls_pubkey: {generator_bls_pubkey[:7]}')

async def blocks_accepted(event, client_timestamp):
    details = unpack_event(event)
    #tag, items = unpack_event(event)

    assert details.tag == 'k', str(('k', details.tag, event,))

    await printio(f'blocks_accepted: details: {json.dumps(details)}')
    return

    #await printio(f'items: {json.dumps(items)}')
    header = details.content['header']
    height = header['height']
    timestamp = header['timestamp']
    generator_bls_pubkey = header['generator_bls_pubkey']
    transactions_len = len(details.content['transactions'])
    babyl = base60p(transactions_len)
    await printio(f'{babyl}', end='', flush=True)
    #await printio(f'generator_bls_pubkey: {generator_bls_pubkey}')
    if generator_bls_pubkey in addresses:
        await printio(f'\a\nMy block !! :  height: {height}, timestamp: {timestamp:_}, generator_bls_pubkey: {generator_bls_pubkey[:7]}')

async def transactions(event, client_timestamp):
    details = unpack_event(event)
    assert details.tag == 'q', str(('q', details.tag, event,))

    content = details.content
    block_height = content['block_height']
    gas_spent =content['gas_spent']
    inner = content['inner']
    typ = inner['type']
    fn_name = inner['call']['fn_name'] if inner['call'] is not None else None
    if typ != 'phoenix':
        value = inner['value']
        sender = inner['sender']
        receiver = inner['receiver']
        await printio(f'\ntransaction: block_height: {block_height:_}, gas_spent: {gas_spent:_}, typ: {typ}, fn_name: {fn_name}, value: {value:_}, sender: {sender[:7]}, receiver: {receiver[:7] if receiver else None}')
    else:
        await printio(f'\ntransaction: block_height: {block_height:_}, gas_spent: {gas_spent:_}, typ: {typ}, fn_name: {fn_name}')

if __name__ == "__main__":
    asyncio.run(hello())


"""
{
  "Content-Location": "/on/transactions:db3ec6b0f19076418ae76c95fb3bae3f566cf8397fc102ca50dbff93874b4757/executed"
}
{
  "block_height": 87283,
  "err": null,
  "gas_spent": 103596,
  "inner": {
    "call": null,
    "deposit": 0,
    "fee": {
      "gas_limit": "2500000",
      "gas_price": "1",
      "refund_address": "nJsNHjb9k6XXBZ7iXPESkspnSrV5vQJf83j7kuQhTtFc82Z6EzHKWtyTxXMHSCZGJCNifWsZkTz9vxxQiTdYPZGiMFK93JX3LWcE69KuwMrdiEiCDKwEBow4LkG9RoAubCs"
    },
    "is_deploy": false,
    "memo": null,
    "nonce": 13,
    "receiver": "uF2f77E9ezKnWxs5TudPAwnFFLqwMJwXABraC3oWaVbjPCwsAJfsJoGBR571W2nyMCKuWaTDqWBjXbLm8HWak2mAuCrXTvoFw3vjioVAcv5nUC7qQ9HKA5i1cNCd78WEHjt",
    "sender": "nJsNHjb9k6XXBZ7iXPESkspnSrV5vQJf83j7kuQhTtFc82Z6EzHKWtyTxXMHSCZGJCNifWsZkTz9vxxQiTdYPZGiMFK93JX3LWcE69KuwMrdiEiCDKwEBow4LkG9RoAubCs",
    "type": "moonlight",
    "value": 1000000000
  }
}

"""
