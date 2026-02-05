import logging
import os 
import requests
from dotenv import load_dotenv
from firebase_admin import auth
import json
from jupyter_notebook_parser import SourceCodeContainer

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

logger = logging.getLogger(__name__)

def jupternotebook_cleaner(text):
    if not text:
        return ""

    try:
        notebook_json = json.loads(text)
        
        final_clean_code = []
        
        if 'cells' in notebook_json:
            for cell in notebook_json['cells']:
                if cell.get('cell_type') == 'code':
                    raw_source = "".join(cell.get('source', []))
                    container = SourceCodeContainer(raw_source)
                    
                    clean_code = container.source_without_magic
                    if clean_code.strip():
                        final_clean_code.append(clean_code)
                        
        return '\n'.join(final_clean_code)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Jupyter Notebook JSON: {str(e)}")
        logger.error(f"Snippet of invalid text: {text[-100:]}") 
        return ""

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
