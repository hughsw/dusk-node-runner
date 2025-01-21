import sys, os
from io import BytesIO
from typing import Union
from json import loads

from fastapi import FastAPI, Path, Query, Form, File, UploadFile, Request
from fastapi.responses import StreamingResponse

#import papersize
#
#from utils import attrdict
#from fold import fold, copy

app = FastAPI()

@app.get('/')
async def read_root():
    return {'Hello': 'tinybook'}


@app.get('/items/{item_id}')
async def read_item(item_id: int, q: Union[str, None] = None):
    #print(f'/items/: item_id: {item_id}')
    return {'item_id': item_id, 'q': q}
