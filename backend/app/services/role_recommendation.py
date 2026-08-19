import logging
import os
import re
from collections import defaultdict

import numpy as np
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity

from app.services.helper_function import (
    FRAMEWORK_KEYWORDS,
    FRAMEWORK_TIERS,
    MIN_MATCHES,
    ROLE_DATASET,
    github_api,
)

load_dotenv()
logger = logging.getLogger(__name__)

# ── Vocab / Role Matrix ───────────────────────────────────────────────────────

FRAMEWORK_VOCAB  = sorted(FRAMEWORK_TIERS.keys())
FRAMEWORK_INDEX  = {fw: i for i, fw in enumerate(FRAMEWORK_VOCAB)}
role_name        = list(ROLE_DATASET.keys())
DETECTABLE_TIERS = {1, 3}
TIER_WEIGHT      = {1: 1.0, 3: 0.35}


def _build_role_matrix() -> np.ndarray:
    matrix = np.zeros((len(ROLE_DATASET), len(FRAMEWORK_VOCAB)))
    for row, frameworks in enumerate(ROLE_DATASET.values()):
        for fw in frameworks:
            if FRAMEWORK_TIERS.get(fw) in DETECTABLE_TIERS:
                matrix[row, FRAMEWORK_INDEX[fw]] = 1
    return matrix


role_matrix = _build_role_matrix()


# ── Pre-compiled regex patterns (compiled once at module load) ────────────────

def _compile_patterns() -> dict:
    compiled: dict = {}
    for framework, tier in FRAMEWORK_TIERS.items():
        if tier not in DETECTABLE_TIERS:
            continue
        raw_patterns = FRAMEWORK_KEYWORDS.get(
            framework,
            [r"\b" + re.escape(framework.lower()) + r"\b"],
        )
        try:
            compiled[framework] = [
                re.compile(p, re.IGNORECASE) for p in raw_patterns
            ]
        except re.error as exc:
            logger.warning("Skipping invalid regex for %s: %s", framework, exc)
    return compiled


_COMPILED_PATTERNS: dict = _compile_patterns()


# ── Framework Detection ───────────────────────────────────────────────────────

def _detect_frameworks(code_data: str) -> list:
    if not code_data:
        return []

    code_lower = code_data.lower()
    detected = []

    for framework, patterns in _COMPILED_PATTERNS.items():
        tier = FRAMEWORK_TIERS.get(framework, 1)
        total_matches = sum(len(p.findall(code_lower)) for p in patterns)
        threshold = MIN_MATCHES.get(tier, 1)

        if total_matches >= threshold:
            detected.append(framework)

    return detected


# ── Role Recommendation ───────────────────────────────────────────────────────

def _vectorize_user(framework_counts: dict) -> np.ndarray:
    vec = np.zeros((1, len(FRAMEWORK_VOCAB)))
    for fw, count in framework_counts.items():
        if fw in FRAMEWORK_INDEX:
            weight = TIER_WEIGHT.get(FRAMEWORK_TIERS.get(fw), 1.0)
            vec[0, FRAMEWORK_INDEX[fw]] = count * weight
    return vec


def _label_full_stack(results: list, margin: float = 0.7) -> list:
    if len(results) < 2:
        return results

    top1, top2 = results[0], results[1]
    if {top1["role"], top2["role"]} == {"Frontend Developer", "Backend Developer"}:
        if top2["score"] >= top1["score"] * margin:
            combined_score = round((top1["score"] + top2["score"]) / 2, 2)
            return [{"role": "Full Stack Developer", "score": combined_score}] + results

    return results


def _get_top_roles(framework_counts: dict, top_n: int = 3) -> list:
    user_vector = _vectorize_user(framework_counts)
    similarity_scores = cosine_similarity(user_vector, role_matrix)[0]
    top_indices = np.argsort(similarity_scores)[::-1][:top_n]

    results = []
    for idx in top_indices:
        score = similarity_scores[idx]
        if score > 0:
            results.append({"role": role_name[idx], "score": round(score * 100, 2)})

    return _label_full_stack(results)


# ── Main Entry Point ──────────────────────────────────────────────────────────

def get_role_recommendation(gitname: str) -> dict:
    """
    Fetch manifests and topics from user repos (up to 50) via GraphQL,
    detect frameworks using pre-compiled regex, and compute cosine-similarity role scores.
    """
    query = """
    query($owner: String!) {
        user(login: $owner) {
            repositories(first: 50, ownerAffiliations: OWNER, isFork: false) {
                nodes {
                    name
                    repositoryTopics(first: 20) {
                        nodes { topic { name } }
                    }
                    languages(first: 10) {
                        nodes { name }
                    }
                    packageJson: object(expression: "HEAD:package.json") { ... on Blob { text } }
                    requirements: object(expression: "HEAD:requirements.txt") { ... on Blob { text } }
                    pyproject: object(expression: "HEAD:pyproject.toml") { ... on Blob { text } }
                    pomXml: object(expression: "HEAD:pom.xml") { ... on Blob { text } }
                    buildGradle: object(expression: "HEAD:build.gradle") { ... on Blob { text } }
                    goMod: object(expression: "HEAD:go.mod") { ... on Blob { text } }
                    cargoToml: object(expression: "HEAD:Cargo.toml") { ... on Blob { text } }
                    dockerfile: object(expression: "HEAD:Dockerfile") { ... on Blob { text } }
                    dockerCompose: object(expression: "HEAD:docker-compose.yml") { ... on Blob { text } }
                }
            }
        }
    }
    """
    try:
        data = github_api(query, {"owner": gitname})
        repos = data.get("data", {}).get("user", {}).get("repositories", {}).get("nodes", [])
    except Exception as exc:
        logger.warning("get_role_recommendation GraphQL query failed for %s: %s", gitname, exc)
        return {"detected_frameworks": [], "recommended_roles": []}

    framework_counts: dict = defaultdict(int)

    for repo in repos:
        combined_text_parts = [repo.get("name", "")]

        # Topics
        topics = repo.get("repositoryTopics", {}).get("nodes", [])
        for t in topics:
            combined_text_parts.append(t.get("topic", {}).get("name", ""))

        # Languages
        langs = repo.get("languages", {}).get("nodes", [])
        for l in langs:
            combined_text_parts.append(l.get("name", ""))

        # Manifest files
        for key in ("packageJson", "requirements", "pyproject", "pomXml",
                    "buildGradle", "goMod", "cargoToml", "dockerfile", "dockerCompose"):
            blob = repo.get(key)
            if blob and blob.get("text"):
                combined_text_parts.append(blob["text"])

        repo_code_data = "\n".join(combined_text_parts)
        for fw in _detect_frameworks(repo_code_data):
            framework_counts[fw] += 1

    detected_frameworks = sorted(framework_counts.keys())

    if not detected_frameworks:
        return {"detected_frameworks": [], "recommended_roles": []}

    return {
        "detected_frameworks": detected_frameworks,
        "recommended_roles":   _get_top_roles(framework_counts),
    }