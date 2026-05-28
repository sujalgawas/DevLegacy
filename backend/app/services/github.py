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

def get_tech_stack(gitname: str):    
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
        
    result = {"all_languages": all_languages, "language_with_code_byte": language_with_code_byte}
    return result
    
def get_code(gitname: str):
    valid_extensions = (
        ".py", ".js", ".java", ".c", ".cpp", ".cc", ".cxx", ".go",
        ".ts", ".tsx", ".php", ".cs", ".rs", ".sql", ".dockerfile",
        ".kt","kts",".html", ".css", ".lua"
    )

    def build_nested_query(depth):
        # Start with the base case (a plain blob leaf)
        query_part = """
          object {
            ... on Blob { text }
          }
        """
        for _ in range(depth):
            query_part = f"""
            object {{
              ... on Blob {{ text }}
              ... on Tree {{
                entries {{
                  name
                  type
                  {query_part}
                }}
              }}
            }}
            """
        return query_part

    def extract_files_from_entries(entries_list, current_path=""):
        found_code = []
        
        for entry in entries_list:
            file_name = entry.get("name", "")
            file_type = entry.get("type", "")
            file_path = f"{current_path}/{file_name}" if current_path else file_name

            if file_type == "blob":
                is_valid = file_name.endswith(valid_extensions) or file_name == "Dockerfile"
                
                if is_valid:
                    text = entry.get("object", {}).get("text")
                    if text is not None:  # skip binaries (text is null), but allow empty files
                        found_code.append({"path": file_path, "content": text})

                elif file_name.endswith(".ipynb"):
                    text = entry.get("object", {}).get("text")
                    if text is not None:
                        found_code.append({"path": file_path, "content": jupternotebook_cleaner(text)})

            elif file_type == "tree":
                sub_entries = entry.get("object", {}).get("entries", [])
                if sub_entries:
                    found_code.extend(extract_files_from_entries(sub_entries, file_path))
        
        return found_code

    variables = {"owner": gitname}

    nested_structure = build_nested_query(8)

    pinned_query = f"""
    query($owner: String!) {{
        user(login: $owner) {{
            pinnedItems(first: 6, types: REPOSITORY) {{
                edges {{
                    node {{
                        ... on Repository {{
                            name
                            object(expression: "HEAD:") {{
                                ... on Tree {{
                                    entries {{
                                        name
                                        type
                                        {nested_structure}
                                    }}
                                }}
                            }}
                        }}
                    }}
                }}
            }}
        }}
    }}
    """

    result = github_api(pinned_query, variables)
    repos = result.get("data", {}).get("user", {}).get("pinnedItems", {}).get("edges", [])
    
    if not repos:
        print("trying fallback_query")
        fallback_query = f"""
        query($owner: String!) {{
            user(login: $owner) {{
                repositories(
                    first: 3,
                    ownerAffiliations: OWNER,
                    orderBy: {{ field: UPDATED_AT, direction: DESC }}
                ) {{
                    edges {{
                        node {{
                            name
                            object(expression: "HEAD:") {{
                                ... on Tree {{
                                    entries {{
                                        name
                                        type
                                        {nested_structure}
                                    }}
                                }}
                            }}
                        }}
                    }}
                }}
            }}
        }}
        """
        result = github_api(fallback_query, variables)
        repos = result.get("data", {}).get("user", {}).get("repositories", {}).get("edges", [])

        if not repos:
            print("[get_code] Warning: No repos found. Raw API result:", result)

    code_data = {}

    for repo in repos:
        repo_node = repo.get("node", {})

        print("checking repo_node",repo_node)

        if repo_node:
            repo_name = repo_node.get("name")
            root_entries = repo_node.get("object", {}).get("entries", [])
        else:
            repo_name = repo.get("name")
            root_entries = repo.get("object", {}).get("entries", [])

        if not repo_name:
            continue

        repo_files = extract_files_from_entries(root_entries)

        if repo_files:
            code_data[repo_name] = repo_files

    print("code data in get_code function",code_data)

    return {"code_data": code_data}

from urllib.parse import urlparse

def get_code_framework(repo_url: str):
    valid_extensions = (
        ".py", ".js", ".java", ".c", ".cpp", ".cc", ".cxx", ".go", 
        ".ts", ".tsx", ".php", ".cs", ".rs", ".sql", "Dockerfile", 
        ".dockerfile", ".kt", ".html", ".css", ".lua"
    )

    def parse_repo_url(url):
        parsed = urlparse(url)
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) < 2:
            raise ValueError("Invalid GitHub URL format. Expected: https://github.com/owner/repo")
        return path_parts[0], path_parts[1]

    owner, repo_name = parse_repo_url(repo_url)

    def build_nested_query(depth):
        query_part = """
          object {
            ... on Blob { text }
          }
        """
        
        for _ in range(depth):
            query_part = f"""
            object {{
              ... on Blob {{ text }}
              ... on Tree {{
                entries {{
                  name
                  type
                  {query_part}
                }}
              }}
            }}
            """
        return query_part

    #increased build nest 5 -> 8 for java and andriod projects
    nested_structure = build_nested_query(8)

    query = f"""
    query($owner: String!, $name: String!) {{
        repository(owner: $owner, name: $name) {{
            object(expression: "HEAD:") {{
                ... on Tree {{
                    entries {{
                        name
                        type
                        {nested_structure}
                    }}
                }}
            }}
        }}
    }}
    """

    variables = {"owner": owner, "name": repo_name}
    result = github_api(query, variables)
    
    repo_data = result.get("data", {}).get("repository", {})
    
    if not repo_data or not repo_data.get("object"):
        return []

    root_entries = repo_data.get("object", {}).get("entries", [])
    
    def extract_files_from_entries(entries_list):
        """
            entries_list : list
            function created to extract code from github graphql
            pre-requisite :- name -> type -> blob (valid extensions)
        """
        found_code = []

        for entry in entries_list:
            file_name = entry.get("name", "")
            file_type = entry.get("type", "")
            
            if file_type == "blob":
                if file_name.endswith(valid_extensions):
                    text = entry.get("object", {}).get("text", "")
                    if text:
                        found_code.append(text)
                
                elif file_name.endswith(".ipynb"):
                    text = entry.get("object", {}).get("text", "")
                    if text:
                        processed_text = jupternotebook_cleaner(text)
                        found_code.append(processed_text)
                    
            elif file_type == "tree":
                sub_entries = entry.get("object", {}).get("entries", [])
                if sub_entries:
                    found_code.extend(extract_files_from_entries(sub_entries))

        return found_code

    return extract_files_from_entries(root_entries)
    
def get_documenation_stats(gitname : str):    
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
                
                pinnedItems(first:5, types: REPOSITORY){
                edges{
                    node{
                        ... on Repository{
                            url   
                            name
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
            
    avg_lines_readme = int(total_readme_lines / repo_count) if repo_count > 0 else 0

    pin_repo = result.get('data', {}).get('user', {}).get("pinnedItems",{}).get("edges",[])
    
    total_code = 0
    commented_code = 0
    final_dir = {}

    if pin_repo:
        for repo in pin_repo:
            url = repo.get("node", {}).get("url", "")
            name = repo.get("node", {}).get("name", "")
            cloc_result = get_comment_to_code(url)
            if cloc_result is None:
                continue
            cloc_data, file = cloc_result
            if cloc_data is None:
                continue
            final_dir[name] = file
            total_code += cloc_data.get('code', 0)
            commented_code += cloc_data.get('comment', 0)
    else:
        import random
        sampled_repos = random.sample(repos, min(3, len(repos)))
        for repo in sampled_repos:
            name = repo.get("name", "")
            url = f"https://github.com/{gitname}/{name}"
            cloc_result = get_comment_to_code(url)
            if cloc_result is None:
                continue
            cloc_data, file = cloc_result
            if cloc_data is None:
                continue
            final_dir[name] = file
            total_code += cloc_data.get('code', 0)
            commented_code += cloc_data.get('comment', 0)

    total = total_code + commented_code
    
    comment_percentage = (100 / total * commented_code) if total > 0 else 0
    
    comment_pre_repos = {"total_code":total_code,"commented_code":commented_code}
    
    result =  {"avg_lines_readme": avg_lines_readme,
            "comment_percentage": comment_percentage,
            "comment_pre_repos": comment_pre_repos,
            "final_dir": final_dir}
    return result
    
def get_github_profile(gitname: str):
    
    query = """
        query($owner: String!){
            user(login: $owner){
                id
                name 
                url
                avatarUrl
                
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
                
    return {
        "username": gitname,
        "github_id": repository['data']['user']['id'],
        "github_profile": repository['data']['user']['url'],
        "profile_pic": repository['data']['user']['avatarUrl'],
        "name": repository['data']['user']['name'],
        "public_repo": repository['data']['user']['repositories']['totalCount'],
        "followers": repository['data']['user']['followers']['totalCount'],
        "following": repository['data']['user']['following']['totalCount']
    }
    
    


def _get_user_repos(username, max_repos=50):
    headers = _github_headers()
    repos = []
    page = 1
    per_page = min(max_repos, 50)

    while len(repos) < max_repos:
        url = f"https://api.github.com/users/{username}/repos"
        params = {
            "sort": "pushed",
            "direction": "desc",
            "per_page": per_page,
            "page": page,
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            break

        page_repos = response.json()
        if not page_repos:
            break

        for repo in page_repos:
            if len(repos) >= max_repos:
                break
            repos.append({
                "name": repo["name"],
                "owner": repo["owner"]["login"],
                "fork": repo.get("fork", False),
            })

        page += 1

    return repos

def _get_repo_code_data(owner, repo_name):
    headers = _github_headers()
    code_data = ""

    tree_url = f"https://api.github.com/repos/{owner}/{repo_name}/git/trees/HEAD?recursive=1"
    tree_response = requests.get(tree_url, headers=headers)

    if tree_response.status_code != 200:
        return ""

    tree_data = tree_response.json()
    tree_items = tree_data.get("tree", [])

    file_paths = [item["path"] for item in tree_items if item["type"] == "blob"]
    code_data = " ".join(file_paths)

    for item in tree_items:
        if item["type"] == "blob" and os.path.basename(item["path"]) in INDICATOR_FILES:
            file_url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/{item['path']}"
            file_response = requests.get(file_url, headers=headers, params={"ref": "HEAD"})

            if file_response.status_code == 200:
                file_data = file_response.json()
                download_url = file_data.get("download_url")
                if download_url:
                    raw_response = requests.get(download_url)
                    if raw_response.status_code == 200:
                        code_data += " " + raw_response.text

    return code_data

