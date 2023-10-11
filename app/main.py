from uuid import uuid4
from datetime import datetime
from os import environ

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from redis import Redis
from motor.motor_asyncio import AsyncIOMotorClient
from bson import encode as bson_encode
from bson.raw_bson import RawBSONDocument
from fastapi.responses import StreamingResponse
from io import BytesIO
from starlette import status as http_status
from pymongo.errors import DocumentTooLarge

from .models import *

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

redis = Redis(host='orders_database', port=6379, db=0)
mongo = AsyncIOMotorClient('mongodb://test:test@general_database:27017').restaurants

@app.post('/order')
async def create_order(order: Order):
    order_id = str(uuid4())
    order = {'created_at': datetime.now().isoformat()} | order.model_dump()
    redis.json().set(order_id, '$', order)
    redis.expire(order_id, 2*60*60) # 2 horas
    return {'order_id': order_id} | order

@app.get('/order/{order_id}')
def get_order(order_id: str):
    if (order := redis.json().get(order_id)) is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND)
    return {'order_id': order_id} | order
    
@app.get('/restaurant/{restaurant_id}')
async def get_restaurant(restaurant_id: str):
    if (restaurant := await mongo['restaurants'].find_one({'restaurant_id': restaurant_id.lower()})) is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND)
    restaurant.pop('_id')

    # ¿Será mejor guardar directamente la URL?
    restaurant['banner'] = f"http://{environ['URL']}:8000/image/{restaurant['banner']}"
    for dish in restaurant['menu']:
        dish['image'] = f"http://{environ['URL']}:8000/image/{dish['image']}"

    return restaurant

@app.post('/upload/image')
async def upload_image(restaurant_id: str, image: UploadFile):
    if image.content_type not in ('image/jpeg', 'image/png', 'image/webp'):
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST)

    file_size = 0
    data = bytearray()
    for chunk in image.file:
        file_size += len(chunk)
        # https://www.mongodb.com/docs/manual/reference/limits/#mongodb-limit-Sharding-Existing-Collection-Data-Size
        if file_size >= 16777216:
            raise HTTPException(status_code=http_status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        data += chunk

    metadata = {
        'restaurant_id': restaurant_id,
        'image_id': str(uuid4()),
        'content_type': image.content_type,
        'created_at': datetime.now().isoformat(),
    }

    document = RawBSONDocument(bson_encode(metadata | {'data': bytes(data)}))
    try:
        await mongo['images'].insert_one(document)
    except DocumentTooLarge:
        raise HTTPException(status_code=http_status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

    return metadata

# Quizás sea mejor ruta: /image/{restaurant_id}/{image_id}
@app.get('/image/{image_id}')
async def get_image(image_id: str):
    if (image := await mongo['images'].find_one({'image_id': image_id})) is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND)
    return StreamingResponse(BytesIO(image['data']), media_type=image['content_type'])
