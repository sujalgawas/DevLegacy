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
from models.tech_stack import tech_stack
from models.open_source import open_source
from models.consistency import consistency_status
from models.document_stat import document_stats
import re 
import requests
import os
from dotenv import load_dotenv
import datetime

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
from datetime import datetime, timedelta

@app.get("/username/consistency/{gitname}")
async def get_consistency(gitname: str):
    uid = "6"
    
    query = """
    query($owner: String!) {
        user(login: $owner) {
            contributionsCollection {
                contributionCalendar {
                    totalContributions
                    weeks {
                        contributionDays {
                            date
                            contributionCount
                        }
                    }
                }
            }
        }
    }
    """
    
    variables = {"owner": gitname}
    
    try:
        result = github_api(query, variables)
    except Exception as e:
         return {"message": "Error connecting to GitHub API", "error": str(e)}

    user_data = result.get('data', {}).get('user')
    
    if not user_data:
        return {"message": "User not found on GitHub"}
        
    calendar = user_data.get('contributionsCollection', {}).get('contributionCalendar', {})
    
    total_contributions = calendar.get('totalContributions', 0)
    weeks = calendar.get('weeks', [])
    
    all_days = []
    for week in weeks:
        for day in week['contributionDays']:
            all_days.append(day)
            
    longest_streak = 0
    current_streak = 0
    current_counting_streak = 0
    active_days_count = 0
    
    
    for day in all_days:
        count = day['contributionCount']
        if count > 0:
            active_days_count += 1
            current_counting_streak += 1
            if current_counting_streak > longest_streak:
                longest_streak = current_counting_streak
        else:
            current_counting_streak = 0

    
    today_str = datetime.utcnow().strftime('%Y-%m-%d')
    
    past_days = [d for d in all_days if d['date'] <= today_str]
    
    if past_days:
        for day in reversed(past_days):
            if day['contributionCount'] > 0:
                current_streak += 1
            else:
                if day['date'] == today_str:
                    continue 
                break

    user_consistency = session.query(consistency_status).filter_by(uid=uid).first()

    if user_consistency:
        user_consistency.total_contributions = total_contributions
        user_consistency.longest_streak = longest_streak
        user_consistency.current_streak = current_streak
        user_consistency.active_days = active_days_count
        user_consistency.last_updated = datetime.utcnow()
    else:
        user_consistency = consistency_status(
            uid=uid,
            total_contributions=total_contributions,
            longest_streak=longest_streak,
            current_streak=current_streak,
            active_days=active_days_count,
            last_updated=datetime.utcnow()
        )
        session.add(user_consistency)

    session.commit()

    return {
        "message": "Consistency data processed",
        "total_contributions": total_contributions,
        "longest_streak": longest_streak,
        "current_streak": current_streak,
        "active_days": active_days_count
    }
    
@app.get("/username/open_source/{gitname}")
async def get_open_source(gitname:str):
    uid = "1"
    
    query = """
    query($owner: String!){
        user(login: $owner){
            pullRequests(first:100){
                nodes{
                    baseRepository{
                        name
                    }
                }
            }
            
            issues(first:100){
                nodes{
                    repository{
                        name
                    }
                }
            }
            
            repositoriesContributedTo(first:100){
                nodes{
                    name
                }
            }

            contributionsCollection {
                pullRequestReviewContributions(first: 100) {
                    nodes {
                        pullRequest {
                            repository {
                                name
                            }
                        }
                    }
                }
            }
        }
    }
    """
    
    variables = {"owner": gitname}
    result = github_api(query,variables)
    
    pull_requests_raw = result.get('data', {}).get('user', {}).get('pullRequests', {}).get('nodes', [])
    issues_raw = result.get('data', {}).get('user', {}).get('issues', {}).get('nodes', [])
    contrib_raw = result.get('data', {}).get('user', {}).get('repositoriesContributedTo', {}).get('nodes', [])
    reviews_raw = result.get('data', {}).get('user', {}).get('contributionsCollection', {}).get('pullRequestReviewContributions', {}).get('nodes', [])

    pull_requests = {}
    issues = {}
    repositories_contributed_to = []
    code_reviews = {}

    for pr in pull_requests_raw:
        if pr.get('baseRepository'):
            name = pr['baseRepository']['name']
            pull_requests[name] = pull_requests.get(name, 0) + 1

    for issue in issues_raw:
        if issue.get('repository'):
            name = issue['repository']['name']
            issues[name] = issues.get(name, 0) + 1
            
    for repo in contrib_raw:
        if repo and repo['name']:
            repositories_contributed_to.append(repo['name'])

    for review in reviews_raw:
        if review.get('pullRequest') and review['pullRequest'].get('repository'):
            name = review['pullRequest']['repository']['name']
            code_reviews[name] = code_reviews.get(name, 0) + 1
    
    open_source_db = session.query(open_source).filter_by(uid=uid).first()
    
    if open_source_db:
        open_source_db.pull_requests = pull_requests
        open_source_db.issues = issues
        open_source_db.repositories_contributed_to = repositories_contributed_to
        open_source_db.code_reviews = code_reviews
    else:
        open_source_db = open_source(
            uid=uid,
            pull_requests=pull_requests,
            issues=issues,
            repositories_contributed_to=repositories_contributed_to,
            code_reviews=code_reviews
        )
        session.add(open_source_db)
    
    session.commit()

    return {
        "pull_requests": pull_requests,
        "issues": issues,
        "repositories_contributed_to": repositories_contributed_to,
        "code_reviews": code_reviews
    }

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
    
    tech_stack_db = session.query(tech_stack).filter_by(uid=uid).first()
    
    if tech_stack_db:
        tech_stack_db.all_languages = all_languages
        tech_stack_db.language_with_code_byte = language_with_code_byte
    else:
        tech_stack_db = tech_stack(
            uid=uid,
            all_languages=list(all_languages),
            language_with_code_byte=language_with_code_byte
        )
        
    session.add(tech_stack_db)
    session.commit()
    
    return all_languages,language_with_code_byte

@app.get("/user_name/documentation/{gitname}")
async def get_documenation_stats(gitname : str):
    uid = "1"
    
    try:
        author_id = get_user_id(gitname)
    except:
        return {"message": "Author not found"}
    
    query = """
        query($owner: String!){
            user(login: $owner){
                repositories(first:100,ownerAffiliations: OWNER, isFork: false){
                    nodes{
                        name
                        object(expression: "HEAD:README.md"){
                            ... on Blob{
                                text
                            }   
                        }
                    }
                }
            }
        }
    """

    variables = {"owner": gitname}
    result = github_api(query, variables)
    
    repos = result.get('data', {}).get('user', {}).get('repositories', {}).get('nodes', [])
    
    repo_readme_stats = {}
    total_readme_lines = 0
    repo_count = 0
    
    for repo in repos:
        name = repo['name']
        readme_object = repo.get('object')
        
        line_count = 0
        
        if readme_object and 'text' in readme_object:
            
            content = readme_object['text']

            line_count = len(content.splitlines())
            
        if line_count > 0:
            repo_readme_stats[name] = line_count
            total_readme_lines += line_count
            repo_count += 1
            
    avg_lines = int(total_readme_lines / repo_count) if repo_count > 0 else 0

    #code to code ration per repo and total
    
    return avg_lines

"""
    #data cleaning
    
    #document_stat
    
    #database 
    document_stats_db = session.query(document_stats).filter(uid=uid).first()
    
    if document_stats_db:
        #assign values
    else:
        document_stats_db = document_stats()
    
    session.add(document_stats_db)
    session.commit()
    
    return document_stat
"""

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