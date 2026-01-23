from fastapi import FastAPI
from pydantic import BaseModel
from firebase_admin import credentials,initialize_app,auth
import json
from sqlalchemy import create_engine,Column,String,Integer
from sqlalchemy.orm import sessionmaker
from models.users import User
from models.test import Testing
from models.commit_status import commit_status

import re 
import requests
import os
from dotenv import load_dotenv

load_dotenv()
github_client_id = os.getenv("github_client_id")
github_secret = os.getenv("github_secret")
github_access_token = os.getenv("github_access_token")

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

"""
class User_Data(BaseModel):
    followers : int
    repos : int 
    total_commits : int
"""
#================ FastAPI BaseModel End ================#

#helper function
def verify_token(token):
    decoded_token = auth.verify_id_token(token)
    uid = decoded_token['uid']
    return uid

@app.get("/username/commit/{gitname}")
async def get_total_commit(gitname: str):
    
    url = f"https://api.github.com/users/{gitname}/repos?type=owner"

    header = {
        'Authorization': f'Bearer {github_access_token}',
        "Accept":"application/vnd.github+json",
        "X-GitHub-Api-Version":"2022-11-28",
    }
    
    response = requests.get(url=url,headers=header)
    
    repository = response.json()
    
    final_count = 0
    commit_pre_repo = {}
    total_repository = len(repository) - 1
    
    for repo_count in range(total_repository):
        repo_name = repository[repo_count]["name"]
        url = f"https://api.github.com/repos/{gitname}/{repo_name}/commits?per_page=1&author=sujalgawas"
        response = requests.get(url=url,headers=header)

        if "Link" in response.headers:
            link = response.headers["Link"]
            final_list = re.findall(r"[\d\.]+",link)
            final_count = int(final_list[-1]) + final_count
            commit_pre_repo[repo_name] = int(final_list[-1])
    
    user_commit_metadata = commit_status(uid = 1,total_commits = final_count,commits_per_repo = commit_pre_repo)
    session.add(user_commit_metadata)
    session.commit()

    if response.status_code == 200:
        return {"message" : "total commits founds",
                "total_commits" : final_count,
                "commit pre repository" : commit_pre_repo},200
    else:
        return {"message" : "error api request"},401


@app.get("/username/profile/{gitname}")
async def get_total_commit(gitname: str):
    
    url = f"https://api.github.com/users/{gitname}"

    header = {
        'Authorization': f'Bearer {github_access_token}',
        "Accept":"application/vnd.github+json",
        "X-GitHub-Api-Version":"2022-11-28",
    }
    
    response = requests.get(url=url,headers=header)
    
    repository = response.json()
    
    return repository

#testing github api
@app.get("/username/{gitname}")
async def get_user_data(gitname : str):
    
    url = f"https://api.github.com/search/users?q={gitname}"
    
    header = {
        'Authorization': f'Bearer {github_access_token}',
        "Accept":"application/vnd.github+json",
        "X-GitHub-Api-Version":"2022-11-28",
    }
    
    reponse = requests.get(url=url,headers=header)
    
    if reponse.status_code == 200:
        return {"message" : "api works",
                "data":reponse.json()},200
    else:
        return {"message" : "error api request"},401


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