print(f'main.py(): {__file__} : start loading', flush=True)

import sys, os
from io import BytesIO
from typing import Union
from json import loads

from fastapi import FastAPI, Path, Query, Form, File, UploadFile, Request
from fastapi.responses import StreamingResponse
import strawberry
from strawberry.fastapi import GraphQLRouter

from dusk_tokenomics import dusk_tokenomics, foo

#import papersize
#
#from utils import attrdict
#from fold import fold, copy


app = FastAPI()

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
    return dict(dusk_tokenomics_alpha=await foo())
    #return dict(dusk_tokenomics_alpha=dusk_tokenomics)



@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello World"

schema = strawberry.Schema(Query)
graphql_app = GraphQLRouter(schema)

app.include_router(graphql_app, prefix="/graphql")


print(f'main.py: {__file__} : done loading', flush=True)
