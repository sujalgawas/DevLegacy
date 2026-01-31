import os 
import requests
from dotenv import load_dotenv
from firebase_admin import auth


load_dotenv()
github_client_id = os.getenv("github_client_id")
github_secret = os.getenv("github_secret")
github_access_token = os.getenv("github_access_token")

#function to verify firebase token
def verify_token(token):
    decoded_token = auth.verify_id_token(token)
    uid = decoded_token['uid']
    return uid

#function to call github api
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

#function to get user id from username
def get_user_id(login):
    """Helper to get the Node ID for a username (required for filtering history)"""
    query = """
    query($login: String!) {
        user(login: $login) { id }
    }
    """
    data = github_api(query, {'login': login})
    return data['data']['user']['id']
