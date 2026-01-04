from fastapi import FastAPI
from pydantic import BaseModel
from firebase_admin import credentials,initialize_app,auth
import json

path = "../serviceAccountKey.json"

cred = credentials.Certificate(path)
initialize_app(cred)

app = FastAPI()

class Login(BaseModel):
    token : str
    
class SignUp(BaseModel):
    UserName : str
    Email : str
    Password: str
    
#helper function
def verify_token(token):
    decoded_token = auth.verify_id_token(token)
    uid = decoded_token['uid']
    return uid

@app.post("/login")
def login(login:Login):
    uid = verify_token(login.token)
    
    #postgres SQL session activate 
    
    if uid:
        return {"message" : "user logged in successfull"},200
    else:
        return {"message" : "Error occured while loggin in"},401

@app.post("/signup")
def signup(signup:SignUp):
    user = auth.create_user(email= signup.Email,password=signup.Password,
                            display_name = signup.UserName)
    
    #postgres SQL verfication + session activation
    
    if user.uid():
        return {"message":"user created"},200
    else:
        return {"message":"Error creating user"},401
    

@app.get("/")
def home():
    return {"message":"home page"}