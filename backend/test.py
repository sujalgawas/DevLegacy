import requests
import json
import subprocess
import tempfile
import os
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


def directory(url):
    ideal_structure = []

    with tempfile.TemporaryDirectory() as tempdirname:
        subprocess.run(args=["git","clone",url,tempdirname],capture_output=True)

        result = subprocess.run(args=["cloc","--by-file","--json",tempdirname],
                                capture_output=True,
                                text=True,
                                check=True)
        
        data = json.loads(result.stdout)
        json_head = data.keys()

        for dict in json_head:
            if tempdirname in dict:
                length = len(tempdirname)
                final_output = dict[length:]
                ideal_structure.append(final_output)

        return ideal_structure

url = "https://api.github.com/search/repositories"
header = {"Accept":"application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}

framework = ["react","fastapi"] 
final_string = ""
for x in framework:
    temp_str = "topic:" + x + " "
    final_string = final_string + temp_str

query = {"q": final_string,
        "sort": "stars",
        "order": "desc",
        "per_page": 1}

response = requests.get(url = url,params=query,headers=header)

if response.status_code == 200:
    try:
        data = response.json()
    except Exception as e:
        print(f"error in {e}")
else:
    print(f"{response.status_code}")

top_repo = data["items"][0]
template_url = top_repo["html_url"]
repo_url = "https://github.com/sujalgawas/DevLegacy.git"

user_dir = directory(repo_url)
template_dir = directory(template_url)

transformer = SentenceTransformer('all-MiniLM-L6-v2')

def dir_score(user_url, template_dir,transformer):
    user_endcode = transformer.encode(user_url)
    template_encode = transformer.encode(template_dir)
    
    score = cosine_similarity(user_endcode,template_encode)
    
    print(f"{score[0]:.4f}")


dir_score(user_url=user_dir,template_dir=template_dir,transformer=transformer)