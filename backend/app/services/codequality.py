import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel 
from huggingface_hub import login, snapshot_download
from pathlib import Path

from dotenv import load_dotenv
import os

from app.services.prompt import SYSTEM_PROMPT, base_prompt
import json

load_dotenv()

hugging_face_token = os.getenv('hugging_face_token')
login(token=hugging_face_token)


#ADAPTER_MODEL_REPO = "sujalgawas/codegemma-2b-code-reviewer_V1"
#BASE_MODEL_REPO = "google/codegemma-2b"

ADAPTER_MODEL_REPO = "sujalgawas/qwen2.5-coder-1.5b-code-reviewer"
BASE_MODEL_REPO = "Qwen/Qwen2.5-Coder-1.5B-Instruct"


SEVERITY_MAP = {'minor':10, 'major':20,'critical':30}

MODEL_DIR = Path("./.cache/models")
BASE_DIR = MODEL_DIR / "base"
ADAPTER_DIR = MODEL_DIR / "adapter"


def ensure_model(repo_id, local_dir):
    if not local_dir.exists() or not any(local_dir.iterdir()):
        print(f"Downloading {repo_id}...")

        snapshot_download(
            repo_id=repo_id,
            local_dir=str(local_dir)
        )

        print("Download complete.")
    else:
        print(f"Using cached model: {local_dir}")


def load_model(base_model_repo = BASE_MODEL_REPO, adapter_repo=ADAPTER_MODEL_REPO):

    ensure_model(base_model_repo, BASE_DIR)
    ensure_model(adapter_repo, ADAPTER_DIR)

    tokenizer = AutoTokenizer.from_pretrained(BASE_DIR)

    base = AutoModelForCausalLM.from_pretrained(
        BASE_DIR,
        torch_dtype=torch.bfloat16,
        low_cpu_mem_usage=True,
    )

    peft_model = PeftModel.from_pretrained(
        base,
        ADAPTER_DIR,
        is_trainable=False,
    )
    model = peft_model.merge_and_unload()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    model.eval()

    return model, tokenizer

model, tokenizer = load_model()

def inference(messages: str, max_new_tokens=300):
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    enc = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(**enc, max_new_tokens=max_new_tokens, temperature=0.0, do_sample=False)
    return tokenizer.decode(out[0][enc["input_ids"].shape[1]:], skip_special_tokens=True)

def score_normalize(response:dict):
    flaw_count = response['flaw_count']
    flaws = response['flaws']
    severity = [item['severity'] for item in flaws]
    
    score = 100
    
    for item in severity:
        score -= SEVERITY_MAP[str((item.lower()))]
    
    return score
    
def code_quality(code):
    """Analyse code quality from a dict or list of file snippets.

    Args:
        code: Either a dict mapping repo/language keys to file lists,
              or a plain list of file dicts/strings. Each file item
              should be a dict with a 'content'/'text' key, or a str.

    Returns:
        (score, level) tuple where score is 0-100 and level is one of
        'Intern', 'Fresher', 'Mid', 'Senior'.
    """
    import random

    # Unwrap wrapper dict produced by some fetchers
    if isinstance(code, dict) and "code_data" in code:
        code = code["code_data"]

    code_snippets = []

    if isinstance(code, dict):
        for key, value in code.items():
            if not isinstance(value, list):
                value = [value]
            for file_item in value:
                if isinstance(file_item, dict):
                    content = file_item.get("content") or file_item.get("text") or ""
                elif isinstance(file_item, str):
                    content = file_item
                else:
                    content = ""
                if content.strip():
                    code_snippets.append(content)

    elif isinstance(code, list):
        for file_item in code:
            if isinstance(file_item, dict):
                content = file_item.get("content") or file_item.get("text") or ""
            elif isinstance(file_item, str):
                content = file_item
            else:
                content = ""
            if content.strip():
                code_snippets.append(content)

    elif isinstance(code, str):
        # Fallback: single raw string passed directly
        if code.strip():
            code_snippets.append(code)

    if not code_snippets:
        return 0, 'Intern'

    samples = random.sample(code_snippets, min(len(code_snippets), 10))

    scores = []
    for snippet in samples:
        # Truncate very long snippets to keep inference fast
        truncated = " ".join(snippet.split()[:500])
        result = model_run(truncated)
        if result is not None:
            scores.append(result)

    if not scores:
        return 0, 'Intern'

    score = sum(scores) / len(scores)

    if score < 30:
        return score, 'Intern'
    elif score < 50:
        return score, 'Fresher'
    elif score < 70:
        return score, 'Mid'
    else:
        return score, 'Senior'

def model_run(code_sample):
    user_message = base_prompt(code_sample)
    
    message = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": user_message},
    ]
    
    #loop in case of Type error
    for _ in range(3):
        response = inference(message)
        try:
            response = json.loads(response)
            
            if 'flaw_count' in response and 'flaws' in response:
                break
                       
        except TypeError as E:
            print(f"{E} exception retrying")
        except Exception as E:
            print(f"exception {E}")
    score = score_normalize(response) if response is not None else None

    return score

if __name__ == '__main__':
    code = '''
        from app.services.helper_function import github_api,get_user_id,jupternotebook_cleaner

from app.services.cloc import get_comment_to_code

from datetime import datetime, timezone

from app.services.helper_function import _github_headers,INDICATOR_FILES

import requests
import os

def get_total_commit(gitname: str):    
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
            
    result =  {"total_commits": total_commits, "commits_per_repo": commit_per_repo}
    
    return result 
    

def get_consistency(gitname: str):
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

    today_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    
    past_days = [d for d in all_days if d['date'] <= today_str]
    
    if past_days:
        for day in reversed(past_days):
            if day['contributionCount'] > 0:
                current_streak += 1
            else:
                if day['date'] == today_str:
                    continue 
                break

    result = {
            "total_contributions": total_contributions,
            "longest_streak": longest_streak,
            "current_streak": current_streak,
            "active_days_count": active_days_count
            }   
    return result

def get_open_source(gitname: str):
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
    
    result =  {
        "pull_requests": pull_requests,
        "issues": issues,
        "repositories_contributed_to": repositories_contributed_to,
        "code_reviews": code_reviews
    }
    return result  
        '''
    
    print(code_quality(code))