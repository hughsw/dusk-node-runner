#!/home/duskadmin/pyvenv/bin/python3

# Alert on public key being the block generator

# see: https://docs.dusk.network/developer/integrations/rues/
# and: curl -sSL -X POST https://nodes.dusk.network/on/graphql/query
#        http://localhost:8080/on/graphql/query

import asyncio
import requests
import json
from functools import partial

from websockets.asyncio.client import connect

addresses_str = '21mif6HvgdLoJtLzibs42LZDtnwkf3518yfhBsTfVim2WZa3j8H9E64JHK4KWdc7W5KMDvoMk7zdY9ddeE1VuNQsks1suJzWDNf5mL5yBqjzdkdfWPaJjyg4rvJ1GqREuDBq,uF2f77E9ezKnWxs5TudPAwnFFLqwMJwXABraC3oWaVbjPCwsAJfsJoGBR571W2nyMCKuWaTDqWBjXbLm8HWak2mAuCrXTvoFw3vjioVAcv5nUC7qQ9HKA5i1cNCd78WEHjt,nJsNHjb9k6XXBZ7iXPESkspnSrV5vQJf83j7kuQhTtFc82Z6EzHKWtyTxXMHSCZGJCNifWsZkTz9vxxQiTdYPZGiMFK93JX3LWcE69KuwMrdiEiCDKwEBow4LkG9RoAubCs'

addresses = frozenset(addresses_str.split(','))

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

printio = partial(asyncio.to_thread, print)
get = partial(asyncio.to_thread, requests.get)

#def printio(*args, **kwargs):
#    return asyncio.to_thread(print, *args, **kwargs)

async def hello():
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
            'blocks/accepted',
            #'blocks/statechange',
            'transactions/Executed',
            )

        await printio(f'watch:')
        for event_to_watch in events_to_watch:
            url = f'{http_uri}/{event_to_watch}'
            #url = f'{http_uri}/transactions/Executed'
            #url = f'{https_host}/transactions/Executed'
            #url = 'https://nodes.dusk.network/on/node/provisioners'

            await printio(f'  {url}')

            x = await get(url, headers=headers)
            #x = await asyncio.to_thread(requests.get, url, headers=headers)
            #x = requests.get(url, headers=headers)
            #await printio(f'x: {x}, x.content: {x.content}')

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
            event = await websocket.recv()
            #await printio(f'type(event): {type(event)}')
            #await printio(f'event: {repr(event)}')
            #if event.find(b'21mif6HvgdLoJtLzibs42LZDtnwkf3518yfhBsTfVim2WZa3j8H9E64JHK4KWdc7W5KMDvoMk7zdY9ddeE1VuNQsks1suJzWDNf5mL5yBqjzdkdfWPaJjyg4rvJ1GqREuDBq') >= 0:
            #    await printio(f'My block!!')

            event_type = event[0:1]
            match event_type:
                case b'q':
                    await printio('transactions')
                case b'n':
                    await printio('statechange')
                case b'k':
                    await accepted(event)
                    #print('accepted')
                case _ as unhandled:
                    await printio(f'unhandled: {unhandled}, event_type: {repr(event_type)}, event: {event}')
"""                    
event: b'q\x00\x00\x00{"Content-Location":"/on/transactions:b58fe26af6c42a29d4ebf0a91ce5746eebad1b2bff46af1cce243fc901b25f26/executed"}{"block_height":73206,"err":null,"gas_spent":26031433,"inner":{"call":{"contract":"0200000000000000000000000000000000000000000000000000000000000000","fn_args":"AQAAAAAAAABGyYhcpgiuqAMfoQN364BYNGeImgjqSah+kMJu/N7l1EzTlCnXhj+MpoUH39IMxQ6CsQWlb4tMv5x1ZXgWuT3dDu/d1cn4jx4eqPevBneWrMsci9cnEiqSmX68RJiJ/Q+fPofrCx19RTFxEpHr24ZzkkiG2p+bm7BQL573tBYeIsuMDLDa1tzWBM5HddJtdQo6VnEXtdEgM+2/Oq4k0bBzHVBLD/+UGGcMqcYo7NBsNmUIH8u00ERybWKPNHyMRwQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEAAAAAAAAABgAAAAAAAAABAAAAAAAAAAn0XmDpqbWdGjF22nRKVi2MR0XSu8V7ectlqILoxJkx0GWAaJ8JxgXUs55WgLJwCxwCAW2csYwG9qJjOCsCZCCCMGHJYqytxxkFoy6EHC+NzEIYftNGdesYo+afIo38DwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA1wQzWKwAAABGyYhcpgiuqAMfoQN364BYNGeImgjqSah+kMJu/N7l1EzTlCnXhj+MpoUH39IMxQ6CsQWlb4tMv5x1ZXgWuT3dDu/d1cn4jx4eqPevBneWrMsci9cnEiqSmX68RJiJ/Q+fPofrCx19RTFxEpHr24ZzkkiG2p+bm7BQL573tBYeIsuMDLDa1tzWBM5HddJtdQo6VnEXtdEgM+2/Oq4k0bBzHVBLD/+UGGcMqcYo7NBsNmUIH8u00ERybWKPNHyMRwQAAAAAAAAAAOCvhyiI7a7G0aYwuFu9v1h1H63x1TtBhw2ZPL/TJxMpxZgbbvt3b0ylWwfawCzuE4z2x6aZD0QqU3nMKnYVgPZYgAV+I6tkFq0k5j8r9seahG+AVN8OMBt2E784v+WuDAAAAAAAAAAA4K+HKIjtrsbRpjC4W72/WHUfrfHVO0GHDZk8v9MnEynFmBtu+3dvTKVbB9rALO4TjPbHppkPRCpTecwqdhWA9liABX4jq2QWrSTmPyv2x5qEb4BU3w4wG3YTvzi/5a4MAAAAAAAAAAA=","fn_name":"withdraw"},"deposit":0,"fee":{"gas_limit":"100000000","gas_price":"1","refund_address":"t3hhgUWKSMJFrTHA9kHgCX7PkovZy5XS8LEFMm5wrSaADjD5kv6VWYsuEmYMhfwvdoxbL5cgfka6pPyNwKrWo33erV1zt1yb1ysJu6roX9JCFHSQ9mVButSAvvpCSSPfcE9"},"is_deploy":false,"memo":null,"nonce":6,"receiver":null,"sender":"t3hhgUWKSMJFrTHA9kHgCX7PkovZy5XS8LEFMm5wrSaADjD5kv6VWYsuEmYMhfwvdoxbL5cgfka6pPyNwKrWo33erV1zt1yb1ysJu6roX9JCFHSQ9mVButSAvvpCSSPfcE9","type":"moonlight","value":0}}'
event: b'n\x00\x00\x00{"Content-Location":"/on/blocks:007b84d08360c59359a0afc8c8dc29a4fbac9168282fb56276bf23ee2e1480e1/statechange"}{"atHeight":73206,"state":"confirmed"}'
event: b'n\x00\x00\x00{"Content-Location":"/on/blocks:007b84d08360c59359a0afc8c8dc29a4fbac9168282fb56276bf23ee2e1480e1/statechange"}{"atHeight":73206,"state":"finalized"}'
event: b'k\x00\x00\x00{"Content-Location":"/on/blocks:a27e812a9df93b5695cd672a56cbce15ee3e5852b451873bf10f4933ab50956d/accepted"}{"header":{"event_bloom":"00000000000200000000000100000000000000000000000000000400010000000000000000000008000000000000000000000000000000000000000000000000000000000000040000000000000000000000000000000000000000000000000000001002000000000000000000000000000000000000000200000000000008000000000000000000000000000000000000000000000000003000000008000080000000000000000000000000000000000000008000000000000000000000000001000800000002000000000000000000000000000000000000000000000000000000000000000000000000000202000000040000000000004000000000080200","failed_iterations":[],"faultroot":"0000000000000000000000000000000000000000000000000000000000000000","gas_limit":3000000000,"generator_bls_pubkey":"sJtg9Lv7N5wXhkpdKmV14AfvET9fKvBL7nnhtSFEs15rgSMzpbs2y6157QoeUneFhfG3KjNvmMRqV3QKiZhxN5jMGQ3pcBQKp9bzvHAprAHejSHUh3rxxdpvSidfSJtPt3v","hash":"a27e812a9df93b5695cd672a56cbce15ee3e5852b451873bf10f4933ab50956d","height":73206,"iteration":0,"prev_block_cert":{"ratification":{"aggregate_signature":"b3640689f6afc29fdd127c0d4bc0badec23344fd5fd8456ccace31d7d9da78220420d9219147f3491f327699b66fba14","bitset":11685208971199},"result":{"Valid":"007b84d08360c59359a0afc8c8dc29a4fbac9168282fb56276bf23ee2e1480e1"},"validation":{"aggregate_signature":"b7243863329e8131441c9097ba1d4506ecab57cc78aeddc547c80858f4d6485f8903ab8653159a0f95337b30a84be2d9","bitset":1028000119712157}},"prev_block_hash":"007b84d08360c59359a0afc8c8dc29a4fbac9168282fb56276bf23ee2e1480e1","seed":"a6d48b695df8ee66a9757c5605161dd2d022538f48977899c1a49f803106e2b21079f46f00f8e0f25271cc1006bbc803","signature":"aef8d96d9aee21f9b557e95af518faa5107ec1a049fa54c785f6e2c90a282846a0677b0e4bde0219432e15103e597742","state_hash":"7a2ffede37b8938cc958eb05f1a02f154bb1538d171f471ac9941dec71adb971","timestamp":1736983472,"txroot":"bd301f07b3f46e1410c4bff33c1eebbe1e4203cd59e560e1676218c50d7bc22a","version":1},"transactions":["b58fe26af6c42a29d4ebf0a91ce5746eebad1b2bff46af1cce243fc901b25f26"]}'
"""

raw_decode = json.JSONDecoder().raw_decode
async def accepted(event):
    #await printio(f'accepted: event: {event}')
    payload = event[4:].decode()
    offset = 0
    items = list()
    while offset < len(payload):
        item, extent = raw_decode(payload[offset:])
        items.append(item)
        offset += extent

    assert len(items) == 2, str((len(items), items))
    #await printio(f'items: {json.dumps(items)}')
    header = items[1]['header']
    height = header['height']
    timestamp = header['timestamp']
    generator_bls_pubkey = header['generator_bls_pubkey']
    #await printio(f'generator_bls_pubkey: {generator_bls_pubkey}')
    if generator_bls_pubkey in addresses:
        await printio(f'\a\nMy block !! :  height: {height}, timestamp: {timestamp}, generator_bls_pubkey: {generator_bls_pubkey}')
    else:
        await printio('.', end='', flush=True)
    
if __name__ == "__main__":
    asyncio.run(hello())
    
