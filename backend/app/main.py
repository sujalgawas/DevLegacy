from fastapi import FastAPI
from pydantic import BaseModel
from firebase_admin import credentials,initialize_app,auth
import json
from sqlalchemy import create_engine,Column,String,Integer
from sqlalchemy.orm import sessionmaker
from models.users import User
from models.test import Testing
from models.commit_status import commit_status
from models.profile import github_profile

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

class GithubProfile(BaseModel):
    uid : int
    github_id : str
    github_profile : str
    name : str
    public_repo : int
    followers : int
    following : int
    
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

def github_api(query : str,variable = None):
    url = "https://api.github.com/graphql"
    
    header = {
        'Authorization': f'Bearer {github_access_token}',
        "Accept":"application/vnd.github+json",
        #"X-GitHub-Api-Version":"2022-11-28",
    }
    
    json_data = {"query":query}
    if variable:
        json_data["variables"] = variable
        
    response = requests.post(url=url,json=json_data,headers=header)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"query failed {response.status_code}:{response.text}") 

def get_user_id(login):
    """Helper to get the Node ID for a username (required for filtering history)"""
    query = """
    query($login: String!) {
        user(login: $login) { id }
    }
    """
    data = github_api(query, {'login': login})
    return data['data']['user']['id']

@app.get("/username/commit/{gitname}")
async def get_total_commit(gitname: str):
    uid = "5"
    
    try:
        author_id = get_user_id(gitname)
    except:
        return {"message": "Author not found"}
    
    query = """
    query($owner: String!, $authorId:ID!){
        user(login: $owner){
            repositories(first: 100, ownerAffiliations: OWNER){
                nodes{
                    name
                    defaultBranchRef{
                        target{
                            ... on Commit {
                                history(author: {id: $authorId}){
                                    totalCount
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    """
    
    variables = {"owner": gitname, "authorId": author_id}
    result = github_api(query, variables)
    
    total_commits = 0
    commit_per_repo = {}
    
    repos = result.get('data', {}).get('user', {}).get('repositories', {}).get('nodes', [])
    
    for repo in repos:
        repo_name = repo['name']
        count = 0
        
        if (repo.get('defaultBranchRef') and 
            repo['defaultBranchRef'].get('target') and 
            repo['defaultBranchRef']['target'].get('history')):
            
            count = repo['defaultBranchRef']['target']['history']['totalCount']
            
        if count > 0:
            commit_per_repo[repo_name] = count
            total_commits += count

    user_commit_metadata = session.query(commit_status).filter_by(uid=uid).first()

    if user_commit_metadata:
        user_commit_metadata.total_commits = total_commits
        user_commit_metadata.commits_per_repo = commit_per_repo
    else:
        user_commit_metadata = commit_status(
            uid=uid,
            total_commits=total_commits,
            commits_per_repo=commit_per_repo
        )
        session.add(user_commit_metadata)

    session.commit()

    return {
        "message": "total commits processed successfully",
        "total_commits": total_commits,
        "commit_per_repository": commit_per_repo
    }, 200

@app.get("/username/technology_stack/{gitname}")
async def get_tech_stack(gitname:str):
    uid = "1"
    
    try: 
        author_id = get_user_id(gitname)
    except:
        return {"message": "Author not found"}
    
    query = """
        query($owner: String!){
            user(login: $owner){
                repositories(first:100, ownerAffiliations: OWNER){
                    nodes{
                        name
                        languages(first:100){
                            totalCount
                            nodes{
                                name
                            }
                            edges{
                                size
                            }
                        }
                    }
                }
            }
        }
    """
    
    variables = {"owner":gitname}
    result = github_api(query, variables)
    
    #return result
    all_languages = set()
    language_with_code_byte = {}
    
    repos = result.get('data', {}).get('user', {}).get('repositories', {}).get('nodes', [])

    language_with_code_byte = {}

    for repo in repos:
        lang_nodes = repo.get('languages', {}).get('nodes', [])
        lang_edges = repo.get('languages', {}).get('edges', [])
        
        for node, edge in zip(lang_nodes, lang_edges):
            name = node['name']
            size = edge['size']
            
            all_languages.update([node['name'] for node in lang_nodes]) 
            
            language_with_code_byte[name] = language_with_code_byte.get(name, 0) + size
    
    return all_languages,language_with_code_byte

@app.get("/username/profile/{gitname}")
async def get_github_profile(gitname: str):
    uid = "3"
    
    query = """
        query($owner: String!){
            user(login: $owner){
                id
                name 
                url
                
                repositories(privacy: PUBLIC){
                    totalCount
                }
                
                followers{
                    totalCount
                }
                following{
                    totalCount
                }
            }
        }
     """
    
    repository = github_api(query,{"owner":gitname})
        
    profile = GithubProfile(uid = uid,
                            github_id = repository['data']['user']['id'],
                            github_profile = repository['data']['user']['url'],
                            name = repository['data']['user']['name'],
                            public_repo = repository['data']['user']['repositories']['totalCount'],
                            followers = repository['data']['user']['followers']['totalCount'],
                            following = repository['data']['user']['following']['totalCount'])

    profile_db = session.query(github_profile).filter_by(uid=uid).first()
    
    if profile_db:
        profile_db.github_id = repository['data']['user']['id']
        profile_db.github_profile = repository['data']['user']['url']
        profile_db.name = repository['data']['user']['name']
        profile_db.public_repo = repository['data']['user']['repositories']['totalCount']
        profile_db.followers = repository['data']['user']['followers']['totalCount']
        profile_db.following = repository['data']['user']['following']['totalCount']
    else:
        profile_db = github_profile(uid = uid,
                                github_id = repository['data']['user']['id'],
                                github_profile = repository['data']['user']['url'],
                                name = repository['data']['user']['name'],
                                public_repo = repository['data']['user']['repositories']['totalCount'],
                                followers = repository['data']['user']['followers']['totalCount'],
                                following = repository['data']['user']['following']['totalCount'])
        
        session.add(profile_db)
        
    session.commit()
    
    if profile:
        return {"message":"profile data is saved",
                "profile": profile},200
    else:
        return {"message":"api not found"},401

"""
#testing github api
@app.get("/username/{gitname}")
async def get_user_data(gitname : str):
    
    url = f"https://api.github.com/search/users?q={gitname}"
    
    reponse = github_api(url)
    
    if reponse.status_code == 200:
        return {"message" : "api works",
                "data":reponse.json()},200
    else:
        return {"message" : "error api request"},401
"""

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