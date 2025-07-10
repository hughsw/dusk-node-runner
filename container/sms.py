#!/home/duskadmin/pyvenv/bin/python3

import asyncio
import time
import json
from functools import partial

from twilio.rest import Client

account_sid = get twilio account_sid
auth_token = get twilio auth_token


printio = partial(asyncio.to_thread, print)
Clientio = partial(asyncio.to_thread, Client)

async def sms():
    client = await Clientio(account_sid, auth_token)
    createio = partial(asyncio.to_thread, client.messages.create)

    #client = Client(account_sid, auth_token)

    async def send():
        message = await createio(
            from_='+18338585345',
            body=f'Async Hello from dusk05: {time.time()}',
            #to='+19785010114'
            to='+18777804236',
        )

        sid = message.sid
        return asyncio.gather(*(
            printio(f'sid: {sid}, dir(message): {dir(message)}'),
            printio(f'sid: {sid}, message.sid: {message.sid}'),
            printio(f'sid: {sid}, message.body: {message.body}'),
            printio(f'sid: {sid}, message.price: {message.price}'),
            printio(f'sid: {sid}, message.price_unit: {message.price_unit}'),
            printio(f'sid: {sid}, message.status: {message.status}'),
            printio(f'sid: {sid}, message: {message}'),
            printio(f'sid: {sid}, message.__dict__: {json.dumps(message.__dict__, default = lambda x: "<" + type(x).__name__ + ">")}'),
            ), return_exceptions=True)

        if False:
            await printio(f'sid: {sid}, dir(message): {dir(message)}')
            await printio(f'sid: {sid}, message.sid: {message.sid}')
            await printio(f'sid: {sid}, message.body: {message.body}')
            await printio(f'sid: {sid}, message.price: {message.price}')
            await printio(f'sid: {sid}, message.price_unit: {message.price_unit}')
            await printio(f'sid: {sid}, message.status: {message.status}')
            await printio(f'sid: {sid}, message: {message}')
            await printio(f'sid: {sid}, message.__dict__: {json.dumps(message.__dict__, default = lambda x: "<" + type(x).__name__ + ">")}')

    messages = (send() for _ in range(3))
    result = await asyncio.gather(*messages, return_exceptions=True)
    await printio(f'result: {result}')

if __name__ == "__main__":
    asyncio.run(sms())

    """
{
  "_version": "V2010",
  "body": "Sent from your Twilio trial account - Async Hello from dusk05: 1737665230.7126913",
  "num_segments": "1",
  "direction": "outbound-api",
  "from_": "+18338585345",
  "to": "+18777804236",
  "date_updated": "datetime",
  "price": null,
  "error_message": null,
  "uri": "/2010-04-01/Accounts/
  "account_sid": 
  "num_media": "0",
  "status": "queued",
  "messaging_service_sid": null,
  "sid": "SM413ce1426c1b85a2f3d34b2bf061bd72",
  "date_sent": null,
  "date_created": "datetime",
  "error_code": null,
  "price_unit": "USD",
  "api_version": "2010-04-01",
  "subresource_uris": {
    "media": "/2010-04-01/Accounts/
  },
  "_solution": {
    "account_sid": "
    "sid": "SM413ce1426c1b85a2f3d34b2bf061bd72"
  },
  "_context": null
}
"""
    
