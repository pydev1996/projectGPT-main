from fastapi import FastAPI
from app.api_v1.user import user_router
from app.api_v1.assistant import assistant_router
from app.api_v1.client import client_router
from app.database import close_mongo_connection, connect_to_mongo
from openai import OpenAI
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Event handlers to connect and disconnect from the MongoDB
@app.on_event("startup")
async def startup_db_client():
    connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    close_mongo_connection()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

app.include_router(user_router, prefix="/api/v1")
app.include_router(assistant_router, prefix="/api/v1/assistant")
app.include_router(client_router, prefix="/api/v1/client")