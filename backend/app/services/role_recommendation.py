import requests
import re
import os
from collections import defaultdict
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from app.services.github import _get_user_repos, _get_repo_code_data
from app.services.helper_function import FRAMEWORK_KEYWORDS, FRAMEWORK_TIERS, MIN_MATCHES, ROLE_DATASET

load_dotenv()

GITHUB_TOKEN = os.getenv("github_access_token", "")


# =============================================================================
# VOCAB / ROLE MATRIX
# =============================================================================
# Frameworks are categorical labels, not free text -- so instead of running
# them through CountVectorizer's tokenizer (which splits "Next.js" into
# "next" + "js" and silently shares that "js" token with Vue.js, Nuxt.js,
# Three.js, Express.js...), we build a fixed-vocabulary multi-hot matrix by
# hand. Each framework is its own independent dimension, no collisions.

FRAMEWORK_VOCAB = sorted(FRAMEWORK_TIERS.keys())
FRAMEWORK_INDEX = {fw: i for i, fw in enumerate(FRAMEWORK_VOCAB)}

role_name = list(ROLE_DATASET.keys())

# Only tier 1 (primary frameworks) and tier 3 (infra/db) are ever actually
# detected -- tier 2 is filtered out in _detect_frameworks. Several
# ROLE_DATASET lists (Backend, Frontend, AI/ML, Mobile, Game) still include
# tier-2 names for descriptive completeness (Celery, jQuery, Pandas, etc).
# Left in, those become permanent dead weight in the role vector -- they
# inflate its norm but can never be matched, which quietly penalizes those
# roles in cosine similarity relative to roles like Database Engineer/DevOps
# that happen to be built entirely out of detectable tier-1/3 names. Filter
# them out here so every role vector only contains things that could ever
# actually score.
DETECTABLE_TIERS = {1, 3}

# Tier-3 (database/infra) tools show up as supporting infrastructure in
# nearly every serious project -- Postgres/Redis/Docker don't make someone
# a "Database Engineer" the way PyTorch makes someone an ML engineer. Down-
# weight tier-3 evidence in the user's vector so it can nudge a score but
# not dominate it the way a primary framework choice should.
TIER_WEIGHT = {1: 1.0, 3: 0.35}


def _build_role_matrix():
    matrix = np.zeros((len(ROLE_DATASET), len(FRAMEWORK_VOCAB)))
    for row, frameworks in enumerate(ROLE_DATASET.values()):
        for fw in frameworks:
            if FRAMEWORK_TIERS.get(fw) in DETECTABLE_TIERS:
                matrix[row, FRAMEWORK_INDEX[fw]] = 1
    return matrix


role_matrix = _build_role_matrix()


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

def _vectorize_user(framework_counts: dict):
    """Build a user vector weighted by how many repos each framework
    appeared in, instead of a flat 0/1 'was it seen at all'. This is what
    lets someone with 9 backend repos and 1 stray frontend repo actually
    score as backend-leaning rather than tying the two together."""
    vec = np.zeros((1, len(FRAMEWORK_VOCAB)))
    for fw, count in framework_counts.items():
        if fw in FRAMEWORK_INDEX:
            weight = TIER_WEIGHT.get(FRAMEWORK_TIERS.get(fw), 1.0)
            vec[0, FRAMEWORK_INDEX[fw]] = count * weight
    return vec


def _label_full_stack(results, margin=0.7):
    """If Frontend and Backend are the top two roles and reasonably close,
    surface 'Full Stack Developer' instead of forcing a single winner.
    ROLE_DATASET has no Full Stack entry of its own on purpose -- this is
    a legible, tunable rule rather than hoping the vector space produces
    a 'full stack' cluster on its own."""
    if len(results) < 2:
        return results

    top1, top2 = results[0], results[1]
    if {top1["role"], top2["role"]} == {"Frontend Developer", "Backend Developer"}:
        if top2["score"] >= top1["score"] * margin:
            combined_score = round((top1["score"] + top2["score"]) / 2, 2)
            return [{"role": "Full Stack Developer", "score": combined_score}] + results

    return results


def _get_top_roles(framework_counts: dict, top_n=3):
    user_vector = _vectorize_user(framework_counts)

    similarity_scores = cosine_similarity(user_vector, role_matrix)[0]

    top_indices = np.argsort(similarity_scores)[::-1][:top_n]

    results = []
    for idx in top_indices:
        score = similarity_scores[idx]
        if score > 0:
            results.append({"role": role_name[idx], "score": round(score * 100, 2)})

    return _label_full_stack(results)


# =============================================================================
# MAIN FUNCTION (called from analysis.py)
# =============================================================================

def get_role_recommendation(gitname: str):
    """
    Scan all the user's repos (max 50), detect frameworks,
    and return recommended roles based on detected frameworks.
    """
    repos = _get_user_repos(gitname, max_repos=50)

    framework_counts = defaultdict(int)

    for repo in repos:
        owner = repo["owner"]
        name = repo["name"]

        # skip forked repos
        if repo.get("fork", False):
            continue

        code_data = _get_repo_code_data(owner, name)

        if not code_data:
            continue

        frameworks = _detect_frameworks(code_data)

        for fw in frameworks:
            framework_counts[fw] += 1

    detected_frameworks = sorted(framework_counts.keys())

    if not detected_frameworks:
        return {"detected_frameworks": [], "recommended_roles": []}

    recommended_roles = _get_top_roles(framework_counts)

    return {
        "detected_frameworks": detected_frameworks,
        "recommended_roles": recommended_roles
    }