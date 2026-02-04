from app.crud.User import update_code, update_commit_status, update_document_status, update_github_profile, update_open_source,update_consistency_status, update_tech_stack

from app.services.helper_function import get_user_id
from app.services.helper_function import github_api,get_user_id

from app.services.cloc import get_comment_to_code

from datetime import datetime, timezone

from app.schemas.User import GithubProfile

def get_total_commit(uid: str, gitname: str,q):    
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
    try:
        update_commit_status(uid=uid,total_commits=total_commits,commit_per_repo=commit_per_repo)
    except Exception as e:
        return f"Error while updating database {e}"

    result =  {"total_commits": total_commits, "commit_per_repo": commit_per_repo}
    
    q.put(result)

    

def get_consistency(uid: str, gitname: str,q):
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
    
    try:
        update_consistency_status(uid = uid, total_contributions=total_contributions,
                                  longest_streak=longest_streak,current_streak=current_streak,
                                  active_days_count=active_days_count)
    except Exception as e:
        return f"Error updating databse {e}"

    result = {
            "total_contributions": total_contributions,
            "longest_streak": longest_streak,
            "current_streak": current_streak,
            "active_days_count": active_days_count
            }   
    q.put(result)

def get_open_source(uid: str, gitname: str,q):
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
    
    try:
        update_open_source(uid=uid,pull_requests=pull_requests,
                           issues=issues,repositories_contributed_to=repositories_contributed_to,
                           code_reviews=code_reviews)
    except Exception as e:
        return f"Error while updating database {e}"
    
    result =  {
        "pull_requests": pull_requests,
        "issues": issues,
        "repositories_contributed_to": repositories_contributed_to,
        "code_reviews": code_reviews
    }
    q.put(result)

def get_tech_stack(uid: str, gitname: str,q):    
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
        
    try:
        update_tech_stack(uid = uid,all_languages=all_languages,
                          language_with_code_byte=language_with_code_byte)
    except Exception as e:
        return f"Error with updating databse {e}"
        
    result = {"all_languages": all_languages, "language_with_code_byte": language_with_code_byte}
    q.put(result)

def get_code(uid:str, gitname: str,q):
    valid_extensions = (
        ".py", ".js", ".java", ".c", ".cpp", ".cc", ".cxx", ".go", 
        ".ts", ".tsx", ".php", ".cs", ".rs", ".sql", "Dockerfile", 
        ".dockerfile", ".kt", ".html", ".css", ".lua", ".ipynb"
    )

    query = """
    query($owner: String!) {
        user(login: $owner) {
            pinnedItems(first: 5, types: REPOSITORY) {
                edges {
                    node {
                        ... on Repository {
                            name
                            object(expression: "HEAD:") {
                                ... on Tree {
                                    entries {
                                        name
                                        type
                                        object {
                                            ... on Blob { text }
                                            ... on Tree {
                                                entries {
                                                    name
                                                    type
                                                    object {
                                                        ... on Blob { text }
                                                        ... on Tree {
                                                            entries {
                                                                name
                                                                type
                                                                object {
                                                                    ... on Blob { text }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    """

    variables = {"owner": gitname}
    
    result = github_api(query, variables)
    
    repos = result.get("data", {}).get("user", {}).get("pinnedItems", {}).get("edges", [])
    
    code_data = {}

    def extract_files_from_entries(entries_list):
        found_code = []
        for entry in entries_list:
            file_name = entry.get("name", "")
            file_type = entry.get("type", "")
                        
            if file_type == "blob":
                if file_name.endswith(valid_extensions):
                    text = entry.get("object", {}).get("text", "")
                    if text:
                        found_code.append(text)
            
            elif file_type == "tree":
                sub_entries = entry.get("object", {}).get("entries", [])
                if sub_entries:
                    found_code.extend(extract_files_from_entries(sub_entries))
                    
        return found_code

    for repo in repos:
        repo_node = repo.get("node", {})
        repo_name = repo_node.get("name")
    
        root_entries = repo_node.get("object", {}).get("entries", [])

        repo_files = extract_files_from_entries(root_entries)
        
        if repo_files:
            code_data[repo_name] = repo_files
    
    try:
        update_code(uid=uid,code_data=code_data)
    except Exception as e:
        return f"Error while updating database {e}"

    result = {"code_data": code_data}
    q.put(result)
    
def get_documenation_stats(uid:str,gitname : str,q):    
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
    for repo in pin_repo:
        url = repo.get("node",{}).get("url",[])
        name = repo.get("node",{}).get("name",[])
        result, file = get_comment_to_code(url)
        final_dir[name] = file
        total_code += result['code']
        commented_code += result['comment']
    
    comment_percentage = 100/(total_code + commented_code) * commented_code
    comment_pre_repos = {"total_code":total_code,"commented_code":commented_code}
    
    try:
        update_document_status(uid=uid,avg_lines_readme=avg_lines_readme,
                               comment_percentage=comment_percentage,
                               comment_pre_repos=comment_pre_repos,final_dir=final_dir)
    except Exception as e:
        return f"Error updating database {e}"
    
    result =  {"avg_lines_readme": avg_lines_readme,
            "comment_percentage": comment_percentage,
            "comment_pre_repos": comment_pre_repos,
            "final_dir": final_dir}
    q.put(result)
    
def get_github_profile(uid:str,gitname: str,q):
    
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

    try:
        update_github_profile(uid,profile)
    except Exception as e:
        return f"Error while updating database {e}"
        
    q.put(profile)