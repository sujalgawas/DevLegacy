import uuid
import asyncio
import itertools
from fastapi import APIRouter, HTTPException, BackgroundTasks

from app.schemas.User import GithubProfile
from app.services.github import get_total_commit, get_consistency, get_open_source, get_tech_stack, get_code, get_documenation_stats, get_github_profile
from app.services.role_recommendation import get_role_recommendation
from app.services.file_structure import get_file_structure_score
from app.crud.User import update_code, update_code_quality, update_commit_status, update_document_status, update_github_profile, update_open_source, update_consistency_status, update_tech_stack
from app.services.codequality import code_quality

router = APIRouter()

TASK_STORE = {}

def rate_comment_percentage(percentage):
    if percentage < 0 or percentage > 100:
        return "Invalid percentage"
    if percentage < 5:
        return 0
    elif percentage < 10:
        return 7
    elif percentage <= 20:
        return 10
    elif percentage <= 30:
        return 5
    else:
        return 2


class AnalysisRequest:
    def __init__(self, uid=None, gitname=None):
        self.get_total_commit = get_total_commit
        self.get_consistency = get_consistency
        self.get_open_source = get_open_source
        self.get_tech_stack = get_tech_stack
        self.get_code = get_code
        self.get_documentation_stats = get_documenation_stats
        self.get_github_profile = get_github_profile
        self.get_role_recommendation = get_role_recommendation
        self.code_quality = code_quality
        self.uid = uid
        self.gitname = gitname

    async def process(self):
        results = await asyncio.gather(
            asyncio.to_thread(self.get_total_commit, self.gitname),
            asyncio.to_thread(self.get_consistency, self.gitname),
            asyncio.to_thread(self.get_open_source, self.gitname),
            asyncio.to_thread(self.get_tech_stack, self.gitname),
            asyncio.to_thread(self.get_code, self.gitname),
            asyncio.to_thread(self.get_documentation_stats, self.gitname),
            asyncio.to_thread(self.get_github_profile, self.gitname),
            asyncio.to_thread(self.get_role_recommendation, self.gitname),
        )

        code_level, code_score = self.code_quality(results[4])

        return {
            "total_commit": results[0],
            "consistency": results[1],
            "open_source": results[2],
            "tech_stack": results[3],
            "code": results[4],
            "documentation": results[5],
            "github_profile": results[6],
            "role_recommendation": results[7],
            "code_level": code_level,
            "code_score": code_score,
        }


async def background_analysis_worker(task_id: str, gitname: str, uid: str):
    try:
        analysis_request = AnalysisRequest(uid=uid, gitname=gitname)
        result = await analysis_request.process()

        top_3_repo = dict(itertools.islice(
            dict(sorted(result["total_commit"]["commits_per_repo"].items(), key=lambda x: x[1], reverse=True)).items(), 3
        ))
        top_languages = dict(itertools.islice(
            dict(sorted(result["tech_stack"]["language_with_code_byte"].items(), key=lambda x: x[1], reverse=True)).items(), 3
        ))

        file_structure = get_file_structure_score(result["documentation"]["final_dir"])
        comment_score = rate_comment_percentage(float(f"{float(result['documentation']['comment_percentage']):.2f}"))

        final_payload = {
            "name": result["github_profile"]["name"],
            "public_repos": result["github_profile"]["public_repo"],
            "profile_picture": result["github_profile"]["profile_pic"],
            "followers": result["github_profile"]["followers"],
            "following": result["github_profile"]["following"],
            "total_commits": result["total_commit"]["total_commits"],
            "top_3_repo": list(top_3_repo),
            "longest_streak": result["consistency"]["longest_streak"],
            "current_streak": result["consistency"]["current_streak"],
            "active_days": result["consistency"]["active_days_count"],
            "pull_requests": result["open_source"]["pull_requests"],
            "issues": result["open_source"]["issues"],
            "repositories_contributed_to": result["open_source"]["repositories_contributed_to"],
            "code_reviews": result["open_source"]["code_reviews"],
            "all_languages": result["tech_stack"]["all_languages"],
            "most_used_language": list(top_languages),
            "code_score": result["code_score"],
            "code_level": int(result["code_level"]),
            "average_lines_readme": result["documentation"]["avg_lines_readme"],
            "comment_percentage": float(f"{float(result['documentation']['comment_percentage']):.2f}"),
            "file_structure": file_structure,
            "detected_frameworks": result["role_recommendation"]["detected_frameworks"],
            "recommended_role": result["role_recommendation"]["recommended_roles"],
            "final_score": int((int(result["code_level"] / 10) + file_structure + comment_score) / 3),
        }

        TASK_STORE[task_id] = {"status": "completed", "data": final_payload}

    except Exception as e:
        TASK_STORE[task_id] = {"status": "failed", "error": str(e)}


# ── POST /api/v1/analysis/{gitname} ──────────────────────
@router.post("/{gitname}")
async def start_analysis(gitname: str, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    TASK_STORE[task_id] = {"status": "processing"}  # set BEFORE background task
    background_tasks.add_task(background_analysis_worker, task_id, gitname, "1")
    return {"message": "Analysis started.", "task_id": task_id, "status": "processing"}


# ── GET /api/v1/analysis/status/{task_id} ────────────────
@router.get("/status/{task_id}")
async def get_analysis_status(task_id: str):
    task = TASK_STORE.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return task

# ---- GET /api/v1/analysis/testing -----------
@router.get("/testing")
async def test_endpoint():
    return {"message": "Analysis endpoint is working!"}


# ---- GET /api/v1/analysis/test2 -----------
@router.get("/test2")
async def test_endpoint():
    return {"message": "Analysis endpoint is working!"}

# ---- GET /api/v1/analysis/test -----------
@router.get("/test")
async def test_endpoint():
    return {"message": "Analysis endpoint is working!"}
