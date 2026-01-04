from fastapi import FastAPI
from pydantic import BaseModel
from firebase_admin import credentials,initialize_app,auth
import json
from sqlalchemy import create_engine,Column,String,Integer
from sqlalchemy.orm import sessionmaker
from models.users import User
from models.test import Testing

engine = create_engine("postgresql://postgres:1234@localhost:5432/dev")
Session = sessionmaker(engine)
session = Session()

path = "../serviceAccountKey.json"
cred = credentials.Certificate(path)
initialize_app(cred)

app = FastAPI()

#================ FastAPI BaseModel Start ================#
class Login(BaseModel):
    token : str
    
class SignUp(BaseModel):
    UserName : str
    Email : str
    Password: str

class Test(BaseModel):
    name : str
    age : str
    temp : int
#================ FastAPI BaseModel End ================#

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

@app.post("/test")
def test(test:Test):
    current_test = Testing(name = test.name,age = test.age,temp = test.temp)
    session.add(current_test)
    session.commit()
    
    return{"message":"working"},200

@app.post("/signup")
def signup(signup:SignUp):
    user = auth.create_user(email= signup.Email,password=signup.Password,
                            display_name = signup.UserName)
    current_uid = user.uid
    
    user = User(uid = current_uid,email = signup.Email, username = signup.UserName)
    session.add(user)
    session.commit()
    
    if user.uid:
        return {"message":"user created"},200
    else:
        return {"message":"Error creating user"},401
    

@app.get("/")
def home():
    return {"message":"home page"}