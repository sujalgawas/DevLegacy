import requests
import re
import os
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np

from app.services.github import _get_user_repos,_get_repo_code_data
from app.services.helper_function import FRAMEWORK_KEYWORDS, FRAMEWORK_TIERS, MIN_MATCHES,ROLE_DATASET

load_dotenv()

GITHUB_TOKEN = os.getenv("github_access_token", "")


role_name = list(ROLE_DATASET.keys())

role_document = [" ".join(frameworks) for frameworks in ROLE_DATASET.values()]

vectorizer = CountVectorizer(lowercase=True)
role_matrix = vectorizer.fit_transform(role_document)

# =============================================================================
# FRAMEWORK DETECTION
# =============================================================================

def _detect_frameworks(code_data):
    if not code_data:
        return []

    code_lower = code_data.lower()
    detected = []

    for framework, tier in FRAMEWORK_TIERS.items():
        patterns = FRAMEWORK_KEYWORDS.get(framework, [r"\b" + re.escape(framework.lower()) + r"\b"])

        total_matches = 0
        for pattern in patterns:
            matches = re.findall(pattern, code_lower)
            total_matches += len(matches)

        threshold = MIN_MATCHES.get(tier, 1)

        if total_matches >= threshold and tier in (1, 3):
            detected.append(framework)

    return detected


# =============================================================================
# ROLE RECOMMENDATION
# =============================================================================

def _get_top_roles(user_frameworks, top_n = 3):
    user_document = [" ".join(user_frameworks)]
    
    user_vector = vectorizer.transform(user_document)
    
    similarity_scores = cosine_similarity(user_vector,role_matrix)[0]
    
    top_indices = np.argsort(similarity_scores)[::-1][:top_n]
    
    results = []
    
    for idx in top_indices:
        score = similarity_scores[idx]
        if score > 0:
            results.append({"role": role_name[idx], "score": round(score * 100, 2)})
    
    return results


# =============================================================================
# MAIN FUNCTION (called from analysis.py)
# =============================================================================

def get_role_recommendation(gitname: str):
    """
    Scan all the user's repos (max 50), detect frameworks,
    and return recommended roles based on detected frameworks.
    """
    repos = _get_user_repos(gitname, max_repos=50)
    
    all_frameworks = set()
    
    for repo in repos:
        owner = repo["owner"]
        name = repo["name"]
        
        #skip forked repos
        if repo.get("fork", False):
            continue
        
        code_data = _get_repo_code_data(owner, name)
        
        if not code_data:
            continue
        
        frameworks = _detect_frameworks(code_data)
        
        if frameworks:
            all_frameworks.update(frameworks)
    
    detected_frameworks = sorted(all_frameworks)
    
    if not detected_frameworks:
        return {"detected_frameworks": [], "recommended_roles": []}
    
    recommended_roles = _get_top_roles(detected_frameworks)
    
    return {
        "detected_frameworks": detected_frameworks,
        "recommended_roles": recommended_roles
    }
