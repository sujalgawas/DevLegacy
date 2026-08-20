import asyncio
import json
import logging
import os
import re
import time
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from redis import asyncio as aioredis
from sqlalchemy.orm import Session

from app.crud.User import (
    check_user,
    get_db,
    get_session,
    get_user_data,
    update_code,
    update_code_quality,
    update_commit_status,
    update_consistency_status,
    update_document_status,
    update_github_profile,
    update_open_source,
    update_tech_stack,
)
from app.services.codequality import code_quality
from app.services.file_structure import get_file_structure_score
from app.services.github import (
    get_code,
    get_consistency,
    get_documenation_stats,
    get_github_profile,
    get_open_source,
    get_tech_stack,
    get_total_commit,
)
from app.services.helper_function import sanitize_data
from app.services.role_recommendation import get_role_recommendation

logger = logging.getLogger(__name__)
router = APIRouter()

TASK_STORE: dict = {}
_TASK_TTL_SECONDS = 3600  #1 hour


def _prune_task_store():
    """Remove tasks older than _TASK_TTL_SECONDS to avoid memory leaks."""
    now = time.monotonic()
    expired = [
        tid for tid, task in TASK_STORE.items()
        if now - task.get("created_at", now) > _TASK_TTL_SECONDS
    ]
    for tid in expired:
        TASK_STORE.pop(tid, None)

#default url using docker-composer
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)


def rate_comment_percentage(percentage: float) -> int:
    if percentage < 0 or percentage > 100:
        return 0
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


_VALID_GITHUB_USERNAME = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,37}[a-zA-Z0-9])?$")


def _validate_gitname(gitname: str):
    """Raise 400 if *gitname* is not a valid GitHub username."""
    if not gitname or not _VALID_GITHUB_USERNAME.match(gitname):
        raise HTTPException(
            status_code=400,
            detail="Invalid GitHub username. Usernames must be 1-39 characters "
                   "and contain only letters, numbers, and hyphens.",
        )


async def _run_analysis(gitname: str) -> dict:
    """Fetch all GitHub data concurrently and run code quality in thread pool."""
    (
        total_commit,
        consistency,
        open_source,
        tech_stack,
        code,
        documentation,
        github_profile_data,
        role_recommendation,
    ) = await asyncio.gather(
        asyncio.to_thread(get_total_commit, gitname),
        asyncio.to_thread(get_consistency, gitname),
        asyncio.to_thread(get_open_source, gitname),
        asyncio.to_thread(get_tech_stack, gitname),
        asyncio.to_thread(get_code, gitname),
        asyncio.to_thread(get_documenation_stats, gitname),
        asyncio.to_thread(get_github_profile, gitname),
        asyncio.to_thread(get_role_recommendation, gitname),
    )

    code_score_num, code_level_label = await asyncio.to_thread(code_quality, code)

    return {
        "total_commit":        total_commit,
        "consistency":         consistency,
        "open_source":         open_source,
        "tech_stack":          tech_stack,
        "code":                code,
        "documentation":       documentation,
        "github_profile":      github_profile_data,
        "role_recommendation": role_recommendation,
        "code_score_num":      code_score_num,
        "code_level_label":    code_level_label,
    }


def _build_final_payload(result: dict) -> dict:
    """Transform the raw analysis result into the final payload shape."""
    commits_per_repo = result["total_commit"].get("commits_per_repo", {}) or {}
    top_3_repo = [
        repo for repo, _ in
        sorted(commits_per_repo.items(), key=lambda x: x[1], reverse=True)[:3]
    ]

    lang_bytes = result["tech_stack"].get("language_with_code_byte", {}) or {}
    top_languages = [
        lang for lang, _ in
        sorted(lang_bytes.items(), key=lambda x: x[1], reverse=True)[:3]
    ]

    file_structure = get_file_structure_score(result["documentation"]["final_dir"])
    raw_comment_pct = float(result["documentation"]["comment_percentage"])
    comment_pct = round(raw_comment_pct, 2)
    comment_score = rate_comment_percentage(comment_pct)

    code_score_num = float(result["code_score_num"])
    final_score = int((int(code_score_num / 10) + file_structure + comment_score) / 3)

    return {
        "name":                        result["github_profile"]["name"],
        "public_repos":                result["github_profile"]["public_repo"],
        "profile_picture":             result["github_profile"]["profile_pic"],
        "followers":                   result["github_profile"]["followers"],
        "following":                   result["github_profile"]["following"],
        "total_commits":               result["total_commit"]["total_commits"],
        "top_3_repo":                  top_3_repo,
        "longest_streak":              result["consistency"]["longest_streak"],
        "current_streak":              result["consistency"]["current_streak"],
        "active_days":                 result["consistency"]["active_days_count"],
        "pull_requests":               result["open_source"]["pull_requests"],
        "issues":                      result["open_source"]["issues"],
        "repositories_contributed_to": result["open_source"]["repositories_contributed_to"],
        "code_reviews":                result["open_source"]["code_reviews"],
        "all_languages":               result["tech_stack"]["all_languages"],
        "most_used_language":          top_languages,
        "code_score":                  result["code_level_label"],
        "code_level":                  round(code_score_num),
        "average_lines_readme":        result["documentation"]["avg_lines_readme"],
        "comment_percentage":          comment_pct,
        "file_structure":              file_structure,
        "detected_frameworks":         result["role_recommendation"]["detected_frameworks"],
        "recommended_role":            result["role_recommendation"]["recommended_roles"],
        "final_score":                 final_score,
    }


async def background_analysis_worker(task_id: str, gitname: str, uid: str):
    db = get_session()
    try:
        result = await _run_analysis(gitname)
        result = sanitize_data(result)
        final_payload = _build_final_payload(result)

        # Persist to DB
        update_github_profile(
            uid=uid,
            profile=result["github_profile"],
            recommended_role=result["role_recommendation"]["recommended_roles"],
            detected_frameworks=result["role_recommendation"]["detected_frameworks"],
            final_score=final_payload["final_score"],
            file_structure=final_payload["file_structure"],
            db=db,
        )
        update_code_quality(
            uid=uid,
            code_score=round(result["code_score_num"]),
            code_level=result["code_level_label"],
            db=db,
        )
        update_commit_status(
            uid=uid,
            total_commits=result["total_commit"]["total_commits"],
            commits_per_repo=result["total_commit"]["commits_per_repo"],
            db=db,
        )
        update_tech_stack(
            uid=uid,
            all_languages=list(result["tech_stack"]["all_languages"]),
            language_with_code_byte=result["tech_stack"]["language_with_code_byte"],
            db=db,
        )
        update_open_source(
            uid=uid,
            pull_requests=result["open_source"]["pull_requests"],
            issues=result["open_source"]["issues"],
            repositories_contributed_to=result["open_source"]["repositories_contributed_to"],
            code_reviews=result["open_source"]["code_reviews"],
            db=db,
        )
        update_consistency_status(
            uid=uid,
            total_contributions=result["consistency"]["total_contributions"],
            current_streak=result["consistency"]["current_streak"],
            longest_streak=result["consistency"]["longest_streak"],
            active_days_count=result["consistency"]["active_days_count"],
            db=db,
        )
        update_document_status(
            uid=uid,
            avg_lines_readme=result["documentation"]["avg_lines_readme"],
            comment_percentage=round(result["documentation"]["comment_percentage"]),
            comment_pre_repos=result["documentation"]["comment_pre_repos"],
            final_dir=result["documentation"]["final_dir"],
            db=db,
        )
        update_code(
            uid=uid,
            code_data=result["code"]["code_data"],
            db=db,
        )

        # Invalidate Redis cache
        cache_key = f"analysis_check:{gitname}"
        try:
            await redis_client.delete(cache_key)
        except Exception as exc:
            logger.warning("Redis delete error for %s: %s", gitname, exc)

        TASK_STORE[task_id] = {
            "status":     "completed",
            "data":       final_payload,
            "created_at": time.monotonic(),
        }

    except Exception as exc:
        logger.error("Analysis failed for %s: %s", gitname, exc, exc_info=True)
        try:
            db.rollback()
        except Exception:
            pass
        TASK_STORE[task_id] = {
            "status":     "failed",
            "error":      str(exc),
            "created_at": time.monotonic(),
        }
    finally:
        db.close()



@router.get("/check/{gitname}")
async def check_existing_analysis(gitname: str, db: Session = Depends(get_db)):
    _validate_gitname(gitname)
    cache_key = f"analysis_check:{gitname}"

    try:
        cached = await redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception as exc:
        logger.warning("Redis get error (falling back to DB): %s", exc)

    uid = check_user(username=gitname, db=db)
    if uid:
        data = get_user_data(uid, db=db)
        if data:
            response_data = {"status": "completed", "data": data}
            try:
                await redis_client.set(cache_key, json.dumps(response_data), ex=86400)
            except Exception as exc:
                logger.warning("Redis set error: %s", exc)
            return response_data

    return {"status": "not_found"}


@router.get("/status/{task_id}")
async def get_analysis_status(task_id: str):
    task = TASK_STORE.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return {k: v for k, v in task.items() if k != "created_at"}


@router.post("/{gitname}")
async def start_analysis(gitname: str, background_tasks: BackgroundTasks):
    _validate_gitname(gitname)
    _prune_task_store()

    task_id = str(uuid.uuid4())
    TASK_STORE[task_id] = {"status": "processing", "created_at": time.monotonic()}
    background_tasks.add_task(background_analysis_worker, task_id, gitname, gitname)
    return {"message": "Analysis started.", "task_id": task_id, "status": "processing"}