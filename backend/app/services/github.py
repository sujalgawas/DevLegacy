import logging
from datetime import datetime, timezone
from urllib.parse import urlparse

from app.services.cloc import get_comment_to_code
from app.services.helper_function import (
    get_user_id,
    github_api,
    jupternotebook_cleaner,
)

logger = logging.getLogger(__name__)

# ── Valid source-file extensions (shared by get_code and get_code_framework) ──
_VALID_EXTENSIONS = (
    ".py", ".js", ".java", ".c", ".cpp", ".cc", ".cxx", ".go",
    ".ts", ".tsx", ".php", ".cs", ".rs", ".sql", ".dockerfile",
    ".kt", ".kts", ".html", ".css", ".lua",
)


# ── Shared helpers ────────────────────────────────────────────────────────────

def _build_nested_query(depth: int) -> str:
    """Build a recursive GraphQL fragment for tree traversal up to *depth* levels."""
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


def _extract_files_from_entries(entries_list: list, current_path: str = "") -> list:
    """
    Walk the nested GraphQL entry tree and return a list of dicts:
      {"path": str, "content": str}
    """
    found_code = []

    for entry in entries_list:
        file_name = entry.get("name", "")
        file_type = entry.get("type", "")
        file_path = f"{current_path}/{file_name}" if current_path else file_name

        if file_type == "blob":
            is_valid = file_name.endswith(_VALID_EXTENSIONS) or file_name == "Dockerfile"

            if is_valid:
                text = entry.get("object", {}).get("text")
                if text is not None:
                    found_code.append({"path": file_path, "content": text})

            elif file_name.endswith(".ipynb"):
                text = entry.get("object", {}).get("text")
                if text is not None:
                    found_code.append({
                        "path": file_path,
                        "content": jupternotebook_cleaner(text),
                    })

        elif file_type == "tree":
            sub_entries = entry.get("object", {}).get("entries", [])
            if sub_entries:
                found_code.extend(_extract_files_from_entries(sub_entries, file_path))

    return found_code


# ── Public service functions ──────────────────────────────────────────────────

def get_total_commit(gitname: str) -> dict:
    try:
        author_id = get_user_id(gitname)
    except Exception as exc:
        logger.warning("Could not get user ID for %s: %s", gitname, exc)
        return {"total_commits": 0, "commits_per_repo": {}}

    query = """
    query($owner: String!, $authorId: ID!) {
        user(login: $owner) {
            repositories(first: 100, ownerAffiliations: OWNER) {
                nodes {
                    name
                    defaultBranchRef {
                        target {
                            ... on Commit {
                                history(author: {id: $authorId}) {
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
    try:
        result = github_api(query, variables)
    except Exception as exc:
        logger.error("get_total_commit failed for %s: %s", gitname, exc)
        return {"total_commits": 0, "commits_per_repo": {}}

    total_commits = 0
    commit_per_repo = {}

    repos = result.get("data", {}).get("user", {}).get("repositories", {}).get("nodes", [])

    for repo in repos:
        repo_name = repo.get("name", "")
        count = 0

        branch_ref = repo.get("defaultBranchRef")
        if branch_ref:
            target = branch_ref.get("target")
            if target:
                history = target.get("history")
                if history:
                    count = history.get("totalCount", 0)

        if count > 0:
            commit_per_repo[repo_name] = count
            total_commits += count

    return {"total_commits": total_commits, "commits_per_repo": commit_per_repo}


def get_consistency(gitname: str) -> dict:
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
    except Exception as exc:
        logger.warning("get_consistency failed for %s: %s", gitname, exc)
        return {"message": "Error connecting to GitHub API", "error": str(exc)}

    user_data = result.get("data", {}).get("user")
    if not user_data:
        return {"message": "User not found on GitHub"}

    calendar = (
        user_data
        .get("contributionsCollection", {})
        .get("contributionCalendar", {})
    )

    total_contributions = calendar.get("totalContributions", 0)
    weeks = calendar.get("weeks", [])

    all_days = [day for week in weeks for day in week["contributionDays"]]

    longest_streak = 0
    current_counting_streak = 0
    active_days_count = 0

    for day in all_days:
        if day["contributionCount"] > 0:
            active_days_count += 1
            current_counting_streak += 1
            if current_counting_streak > longest_streak:
                longest_streak = current_counting_streak
        else:
            current_counting_streak = 0

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    past_days = [d for d in all_days if d["date"] <= today_str]

    current_streak = 0
    if past_days:
        for day in reversed(past_days):
            if day["contributionCount"] > 0:
                current_streak += 1
            else:
                if day["date"] == today_str:
                    continue
                break

    return {
        "total_contributions": total_contributions,
        "longest_streak": longest_streak,
        "current_streak": current_streak,
        "active_days_count": active_days_count,
    }


def get_open_source(gitname: str) -> dict:
    query = """
    query($owner: String!) {
        user(login: $owner) {
            pullRequests(first: 100) {
                nodes {
                    baseRepository { name }
                }
            }
            issues(first: 100) {
                nodes {
                    repository { name }
                }
            }
            repositoriesContributedTo(first: 100) {
                nodes { name }
            }
            contributionsCollection {
                pullRequestReviewContributions(first: 100) {
                    nodes {
                        pullRequest {
                            repository { name }
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
    except Exception as exc:
        logger.warning("get_open_source failed for %s: %s", gitname, exc)
        return {
            "pull_requests": {},
            "issues": {},
            "repositories_contributed_to": [],
            "code_reviews": {},
        }

    user = result.get("data", {}).get("user", {})
    pull_requests_raw = user.get("pullRequests", {}).get("nodes", [])
    issues_raw        = user.get("issues", {}).get("nodes", [])
    contrib_raw       = user.get("repositoriesContributedTo", {}).get("nodes", [])
    reviews_raw       = (
        user
        .get("contributionsCollection", {})
        .get("pullRequestReviewContributions", {})
        .get("nodes", [])
    )

    pull_requests: dict = {}
    issues: dict = {}
    repositories_contributed_to: list = []
    code_reviews: dict = {}

    for pr in pull_requests_raw:
        base_repo = pr.get("baseRepository")
        if base_repo:
            name = base_repo.get("name")
            if name:
                pull_requests[name] = pull_requests.get(name, 0) + 1

    for issue in issues_raw:
        repo = issue.get("repository")
        if repo:
            name = repo.get("name")
            if name:
                issues[name] = issues.get(name, 0) + 1

    for repo in contrib_raw:
        if repo and repo.get("name"):
            repositories_contributed_to.append(repo["name"])

    for review in reviews_raw:
        pr = review.get("pullRequest")
        if pr:
            repo = pr.get("repository")
            if repo:
                name = repo.get("name")
                if name:
                    code_reviews[name] = code_reviews.get(name, 0) + 1

    return {
        "pull_requests": pull_requests,
        "issues": issues,
        "repositories_contributed_to": repositories_contributed_to,
        "code_reviews": code_reviews,
    }


def get_tech_stack(gitname: str) -> dict:
    query = """
    query($owner: String!) {
        user(login: $owner) {
            repositories(first: 100, ownerAffiliations: OWNER) {
                nodes {
                    name
                    languages(first: 100) {
                        nodes { name }
                        edges { size }
                    }
                }
            }
        }
    }
    """

    variables = {"owner": gitname}
    try:
        result = github_api(query, variables)
    except Exception as exc:
        logger.warning("get_tech_stack failed for %s: %s", gitname, exc)
        return {"all_languages": set(), "language_with_code_byte": {}}

    language_with_code_byte: dict = {}

    repos = (
        result.get("data", {})
        .get("user", {})
        .get("repositories", {})
        .get("nodes", [])
    )

    for repo in repos:
        lang_nodes = repo.get("languages", {}).get("nodes", [])
        lang_edges = repo.get("languages", {}).get("edges", [])

        for node, edge in zip(lang_nodes, lang_edges):
            name = node.get("name")
            size = edge.get("size", 0)
            if name:
                language_with_code_byte[name] = language_with_code_byte.get(name, 0) + size

    all_languages = set(language_with_code_byte.keys())

    return {
        "all_languages": all_languages,
        "language_with_code_byte": language_with_code_byte,
    }


def get_code(gitname: str) -> dict:
    """
    Fetch source code from the user's pinned repositories (up to 6),
    falling back to the 3 most recently pushed repos if no pins exist.
    """
    variables = {"owner": gitname}
    repos = []

    for depth in (8, 5):
        nested_structure = _build_nested_query(depth)
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
        try:
            result = github_api(pinned_query, variables)
            repos = result.get("data", {}).get("user", {}).get("pinnedItems", {}).get("edges", [])
            break
        except Exception as exc:
            if depth == 5:
                logger.error("Pinned repos query failed at depth 5: %s", exc)
            else:
                logger.debug("Depth-8 query failed, trying depth-5: %s", exc)

    if not repos:
        logger.info("No pinned repos for %s, falling back to recent repos.", gitname)
        nested_structure = _build_nested_query(5)
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
        try:
            result = github_api(fallback_query, variables)
            repos = (
                result.get("data", {})
                .get("user", {})
                .get("repositories", {})
                .get("edges", [])
            )
        except Exception as exc:
            logger.error("Fallback repo query failed: %s", exc)

    code_data: dict = {}

    for repo in repos:
        repo_node = repo.get("node", {})
        if repo_node:
            repo_name = repo_node.get("name")
            root_entries = repo_node.get("object", {}).get("entries", [])
        else:
            repo_name = repo.get("name")
            root_entries = repo.get("object", {}).get("entries", [])

        if not repo_name:
            continue

        repo_files = _extract_files_from_entries(root_entries)
        if repo_files:
            code_data[repo_name] = repo_files

    return {"code_data": code_data}


def get_code_framework(repo_url: str) -> list:
    """Fetch all source files from a single repo by its URL."""
    def parse_repo_url(url: str):
        parsed = urlparse(url)
        parts = parsed.path.strip("/").split("/")
        if len(parts) < 2:
            raise ValueError(
                f"Invalid GitHub URL: {url!r}. Expected: https://github.com/owner/repo"
            )
        return parts[0], parts[1]

    owner, repo_name = parse_repo_url(repo_url)
    variables = {"owner": owner, "name": repo_name}

    entries = []
    for depth in (8, 5):
        nested_structure = _build_nested_query(depth)
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
        try:
            result = github_api(query, variables)
            repo_data = result.get("data", {}).get("repository", {})
            if repo_data and repo_data.get("object"):
                entries = repo_data["object"].get("entries", [])
            break
        except Exception as exc:
            if depth == 5:
                logger.error("get_code_framework depth-5 also failed: %s", exc)
            else:
                logger.debug("get_code_framework depth-8 failed, retrying depth-5: %s", exc)

    if not entries:
        return []

    file_dicts = _extract_files_from_entries(entries)
    return [f["content"] for f in file_dicts if f.get("content")]


def get_documenation_stats(gitname: str) -> dict:
    query = """
    query($owner: String!) {
        user(login: $owner) {
            repositories(first: 50, ownerAffiliations: OWNER, isFork: false) {
                nodes {
                    name
                    object(expression: "HEAD:README.md") {
                        ... on Blob { text }
                    }
                }
            }
            pinnedItems(first: 5, types: REPOSITORY) {
                edges {
                    node {
                        ... on Repository {
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
    try:
        result = github_api(query, variables)
    except Exception as exc:
        logger.warning("get_documenation_stats query failed for %s: %s", gitname, exc)
        return {
            "avg_lines_readme": 0,
            "comment_percentage": 0.0,
            "comment_pre_repos": {"total_code": 0, "commented_code": 0},
            "final_dir": {},
        }

    repos = (
        result.get("data", {})
        .get("user", {})
        .get("repositories", {})
        .get("nodes", [])
    )

    repo_readme_stats: dict = {}
    total_readme_lines = 0
    repo_count = 0

    for repo in repos:
        name = repo.get("name", "")
        readme_object = repo.get("object")
        line_count = 0

        if readme_object and "text" in readme_object:
            line_count = len(readme_object["text"].splitlines())

        if line_count > 0:
            repo_readme_stats[name] = line_count
            total_readme_lines += line_count
            repo_count += 1

    avg_lines_readme = (total_readme_lines // repo_count) if repo_count > 0 else 0

    pin_repo = (
        result.get("data", {})
        .get("user", {})
        .get("pinnedItems", {})
        .get("edges", [])
    )

    total_code = 0
    commented_code = 0
    final_dir: dict = {}

    import random as _random

    if pin_repo:
        sources = [
            (repo.get("node", {}).get("name", ""), repo.get("node", {}).get("url", ""))
            for repo in pin_repo[:2]
        ]
    else:
        sampled = _random.sample(repos, min(2, len(repos))) if repos else []
        sources = [
            (r.get("name", ""), f"https://github.com/{gitname}/{r.get('name', '')}")
            for r in sampled
        ]

    for name, url in sources:
        if not url:
            continue
        cloc_result = get_comment_to_code(url)
        if cloc_result is None:
            continue
        cloc_data, file_list = cloc_result
        if cloc_data is None:
            continue
        final_dir[name] = file_list
        total_code     += cloc_data.get("code", 0)
        commented_code += cloc_data.get("comment", 0)

    total = total_code + commented_code
    comment_percentage = (100 / total * commented_code) if total > 0 else 0.0

    return {
        "avg_lines_readme":   avg_lines_readme,
        "comment_percentage": comment_percentage,
        "comment_pre_repos":  {"total_code": total_code, "commented_code": commented_code},
        "final_dir":          final_dir,
    }


def get_github_profile(gitname: str) -> dict:
    query = """
    query($owner: String!) {
        user(login: $owner) {
            id
            name
            url
            avatarUrl
            repositories(privacy: PUBLIC) { totalCount }
            followers  { totalCount }
            following  { totalCount }
        }
    }
    """

    try:
        result = github_api(query, {"owner": gitname})
        user = result["data"]["user"]
    except Exception as exc:
        raise ValueError(f"GitHub user '{gitname}' not found or API error.") from exc

    if not user:
        raise ValueError(f"GitHub user '{gitname}' does not exist.")

    return {
        "username":       gitname,
        "github_id":      user["id"],
        "github_profile": user["url"],
        "profile_pic":    user["avatarUrl"],
        "name":           user.get("name") or gitname,
        "public_repo":    user["repositories"]["totalCount"],
        "followers":      user["followers"]["totalCount"],
        "following":      user["following"]["totalCount"],
    }
