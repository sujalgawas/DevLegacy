from firebase_admin import credentials,initialize_app
import json
import os
from fastapi import FastAPI

        
app = FastAPI()

path = "../serviceAccountKey.json"
cred = credentials.Certificate(path)
initialize_app(cred)

app = FastAPI()
        
