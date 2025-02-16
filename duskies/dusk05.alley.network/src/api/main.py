print(f'main.py(): {__file__} : start loading', flush=True)

import sys, os
import asyncio
import time
import json
from io import BytesIO
from typing import Union
from json import loads, dumps

from fastapi import FastAPI, Path, Query, Form, File, UploadFile, Request, Response
from fastapi.responses import StreamingResponse
import strawberry
from strawberry.fastapi import GraphQLRouter

from utils import printio
from dusk_tokenomics import dusk_tokenomics

from provisionator import startup, provisionator, get_summary, get_summary_diff

#from myblock import hello

#import papersize
#
#from utils import attrdict
#from fold import fold, copy


app = FastAPI()

items = {}

server_tasks = set()
def start_server_task(coro, *, name=None):
    server_tasks.add(asyncio.get_running_loop().create_task(coro, name=name))
def cancel_server_tasks():
    while server_tasks:
        server_tasks.pop().cancel()

async def forever():
    while True:
        await printio(f'forever: {time.time():_}', flush=True)
        await asyncio.sleep(7)


@app.on_event('startup')
async def startup_event():
    items['foo'] = {'name': 'Fighters'}
    items['bar'] = {'name': 'Tenders'}
    await printio(f'startup_event: items: {items}', flush=True)

    await startup()

    #start_server_task(forever(), name='forevaah')
    start_server_task(provisionator(), name='provisionator')

    if False:
        loop = asyncio.get_running_loop()
        task = loop.create_task(forever(), name='forevah')
        server_tasks.add(task)
        await printio(f'startup_event: loop: {loop}', flush=True)
        await printio(f'startup_event: task: {task}, task.get_name(): {repr(task.get_name())}', flush=True)


@app.on_event('shutdown')
async def shutdown_event():
    await printio(f'shutdown_event: items: {items}', flush=True)

    cancel_server_tasks()

    if False:
        for task in server_tasks:
            await printio(f'shutdown_event: cancel task: {task.get_name()}', flush=True)
            task.cancel()


@app.get('/')
async def read_root():
    return dict(Hello='tinybook')
    #return {'Hello': 'tinybook'}

@app.get('/items/{item_id}')
async def read_item(item_id: int, q: Union[str, None] = None):
    #print(f'/items/: item_id: {item_id}')
    return {'item_id': item_id, 'q': q}


@app.get('/dusk-tokenomics')
async def dusk_tokenomics_get():
    return dict(dusk_tokenomics_alpha=await dusk_tokenomics())

@app.get('/dusk-provisioning-summary')
async def dusk_provisioning_summary_get():
    summary = await get_summary()
    if summary is None: return {}

    # dev
    summary_json_str = json.dumps(summary, indent=2)
    return Response(content=summary_json_str.encode(), media_type='text/json')


@app.get('/dusk-provisioning-summary-diff')
async def dusk_provisioning_summary_diff_get():
    diff = await get_summary_diff()
    if diff is None: return {}

    diff_json_str = json.dumps(diff, indent=2)
    return Response(content=diff_json_str.encode(), media_type='text/json')

    return

@app.get('/fooner')
async def fooner_get():
    fooner = dumps(dict(
        foo = 'bar',
        barn = 23,
        ))

    return Response(content=fooner.encode(), media_type='text/json')



@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return 'Hello World'

schema = strawberry.Schema(Query)
graphql_app = GraphQLRouter(schema)

app.include_router(graphql_app, prefix='/graphql')


print(f'main.py: {__file__} : done loading', flush=True)
