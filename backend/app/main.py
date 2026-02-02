from firebase_admin import credentials,initialize_app
import json
import os
from fastapi import FastAPI

from app.api.router import api_router

        
app = FastAPI()

path = "./serviceAccountKey.json"
cred = credentials.Certificate(path)
initialize_app(cred)

app = FastAPI()

app.include_router(api_router,prefix="/api/v1")

@app.get("/")
def home():
    return {"message":"Welcome to DevLegacy Backend"}
        
