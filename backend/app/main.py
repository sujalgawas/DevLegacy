from fastapi import FastAPI
from pydantic import BaseModel
from firebase_admin import credentials,initialize_app,auth
import json
from sqlalchemy import create_engine,Column,String,Integer
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

path = "../serviceAccountKey.json"

engine = create_engine("postgresql://postgres:1234@localhost:5432/dev")
Session = sessionmaker(engine)
session = Session()

Base = declarative_base()
#================ database models start ================#
"""
CREATE TABLE users(
	uid VARCHAR(100) PRIMARY KEY,
	Email VARCHAR(50),
	UserName VARCHAR(50)
);
"""

class User(Base):
    __tablename__ = 'users'
    uid = Column(String, primary_key=True)
    email = Column(String)
    username = Column(String)

#================ database models end ================#
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