import os
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.models.commit_status import commit_status
from app.models.profile import github_profile
from app.models.tech_stack import tech_stack
from app.models.open_source import open_source
from app.models.consistency import consistency_status
from app.models.document_stat import document_stats
from app.models.code import Code
from app.models.code_quality import Code_quality

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:1234@localhost:5432/dev")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session() -> Session:
    """Create a new SQLAlchemy session."""
    return SessionLocal()


def get_db():
    """FastAPI dependency for database sessions."""
    db = get_session()
    try:
        yield db
    finally:
        db.close()


def update_code_quality(uid: str, code_score: int, code_level: str, db: Session = None):
    local_session = False
    if db is None:
        db = get_session()
        local_session = True

    try:
        code = db.query(Code_quality).filter_by(uid=uid).first()
        if code:
            code.code_score = code_score
            code.code_level = code_level
        else:
            code = Code_quality(uid=uid, code_score=code_score, code_level=code_level)
            db.add(code)
        db.commit()
    finally:
        if local_session:
            db.close()


def update_commit_status(uid: str, total_commits: int, commits_per_repo: dict, db: Session = None):
    local_session = False
    if db is None:
        db = get_session()
        local_session = True

    try:
        user_commit_metadata = db.query(commit_status).filter_by(uid=uid).first()
        if user_commit_metadata:
            user_commit_metadata.total_commits = total_commits
            user_commit_metadata.commits_per_repo = commits_per_repo
        else:
            user_commit_metadata = commit_status(
                uid=uid,
                total_commits=total_commits,
                commits_per_repo=commits_per_repo,
            )
            db.add(user_commit_metadata)
        db.commit()
    finally:
        if local_session:
            db.close()


def update_github_profile(
    uid: str,
    profile: dict,
    recommended_role: list,
    detected_frameworks: list,
    final_score: int,
    file_structure: int,
    db: Session = None,
):
    local_session = False
    if db is None:
        db = get_session()
        local_session = True

    try:
        profile_db = db.query(github_profile).filter_by(uid=uid).first()
        if profile_db:
            profile_db.github_id = profile.get("github_id")
            profile_db.github_profile = profile.get("github_profile")
            profile_db.name = profile.get("name")
            profile_db.public_repo = profile.get("public_repo")
            profile_db.followers = profile.get("followers")
            profile_db.following = profile.get("following")
            profile_db.profile_pic = profile.get("profile_pic")
            profile_db.recommended_role = recommended_role
            profile_db.detected_frameworks = detected_frameworks
            profile_db.final_score = final_score
            profile_db.file_structure = file_structure
        else:
            profile_db = github_profile(
                uid=uid,
                github_id=profile.get("github_id"),
                github_profile=profile.get("github_profile"),
                profile_pic=profile.get("profile_pic"),
                name=profile.get("name"),
                public_repo=profile.get("public_repo"),
                followers=profile.get("followers"),
                following=profile.get("following"),
                recommended_role=recommended_role,
                detected_frameworks=detected_frameworks,
                final_score=final_score,
                file_structure=file_structure,
            )
            db.add(profile_db)
        db.commit()
    finally:
        if local_session:
            db.close()


def update_tech_stack(uid: str, all_languages: list, language_with_code_byte: dict, db: Session = None):
    local_session = False
    if db is None:
        db = get_session()
        local_session = True

    try:
        tech_stack_db = db.query(tech_stack).filter_by(uid=uid).first()
        if tech_stack_db:
            tech_stack_db.all_languages = list(all_languages)
            tech_stack_db.language_with_code_byte = language_with_code_byte
        else:
            tech_stack_db = tech_stack(
                uid=uid,
                all_languages=list(all_languages),
                language_with_code_byte=language_with_code_byte,
            )
            db.add(tech_stack_db)
        db.commit()
    finally:
        if local_session:
            db.close()


def update_open_source(
    uid: str,
    pull_requests: dict,
    issues: dict,
    repositories_contributed_to: list,
    code_reviews: dict,
    db: Session = None,
):
    local_session = False
    if db is None:
        db = get_session()
        local_session = True

    try:
        open_source_db = db.query(open_source).filter_by(uid=uid).first()
        if open_source_db:
            open_source_db.pull_requests = pull_requests
            open_source_db.issues = issues
            open_source_db.repositories_contributed_to = repositories_contributed_to
            open_source_db.code_reviews = code_reviews
        else:
            open_source_db = open_source(
                uid=uid,
                pull_requests=pull_requests,
                issues=issues,
                repositories_contributed_to=repositories_contributed_to,
                code_reviews=code_reviews,
            )
            db.add(open_source_db)
        db.commit()
    finally:
        if local_session:
            db.close()


def update_consistency_status(
    uid: str,
    total_contributions: int,
    current_streak: int,
    longest_streak: int,
    active_days_count: int,
    db: Session = None,
):
    local_session = False
    if db is None:
        db = get_session()
        local_session = True

    try:
        user_consistency = db.query(consistency_status).filter_by(uid=uid).first()
        if user_consistency:
            user_consistency.total_contributions = total_contributions
            user_consistency.longest_streak = longest_streak
            user_consistency.current_streak = current_streak
            user_consistency.active_days = active_days_count
            user_consistency.last_updated = datetime.utcnow()
        else:
            user_consistency = consistency_status(
                uid=uid,
                total_contributions=total_contributions,
                longest_streak=longest_streak,
                current_streak=current_streak,
                active_days=active_days_count,
                last_updated=datetime.utcnow(),
            )
            db.add(user_consistency)
        db.commit()
    finally:
        if local_session:
            db.close()


def update_document_status(
    uid: str,
    avg_lines_readme: int,
    comment_percentage: int,
    comment_pre_repos: dict,
    final_dir: dict,
    db: Session = None,
):
    local_session = False
    if db is None:
        db = get_session()
        local_session = True

    try:
        document_stats_db = db.query(document_stats).filter_by(uid=uid).first()
        if document_stats_db:
            document_stats_db.uid = uid
            document_stats_db.avg_lines_readme = avg_lines_readme
            document_stats_db.comment_percentage = comment_percentage
            document_stats_db.comment_to_repos = comment_pre_repos
            document_stats_db.final_dir = final_dir
        else:
            document_stats_db = document_stats(
                uid=uid,
                avg_lines_readme=avg_lines_readme,
                comment_percentage=comment_percentage,
                comment_to_repos=comment_pre_repos,
                final_dir=final_dir,
            )
            db.add(document_stats_db)
        db.commit()
    finally:
        if local_session:
            db.close()


def update_code(uid: str, code_data: dict, db: Session = None):
    local_session = False
    if db is None:
        db = get_session()
        local_session = True

    try:
        code_db = db.query(Code).filter_by(uid=uid).first()
        if code_db:
            code_db.uid = uid
            code_db.code = code_data
        else:
            code_db = Code(uid=uid, code=code_data)
            db.add(code_db)
        db.commit()
    finally:
        if local_session:
            db.close()


def check_user(username: str, db: Session = None) -> str | None:
    local_session = False
    if db is None:
        db = get_session()
        local_session = True

    try:
        profile_db = db.query(github_profile).filter_by(uid=username).first()
        return profile_db.uid if profile_db else None
    finally:
        if local_session:
            db.close()


def get_user_data(uid: str, db: Session = None) -> dict | None:
    from app.services.helper_function import sanitize_data

    local_session = False
    if db is None:
        db = get_session()
        local_session = True

    try:
        profile_db = db.query(github_profile).filter_by(uid=uid).first()
        if not profile_db:
            return None

        code_qual = db.query(Code_quality).filter_by(uid=uid).first()
        user_commit = db.query(commit_status).filter_by(uid=uid).first()
        tech_stack_db = db.query(tech_stack).filter_by(uid=uid).first()
        open_source_db = db.query(open_source).filter_by(uid=uid).first()
        user_consistency = db.query(consistency_status).filter_by(uid=uid).first()
        document_stats_db = db.query(document_stats).filter_by(uid=uid).first()

        commits_per_repo = getattr(user_commit, "commits_per_repo", {}) or {}
        top_3_repo = []
        if commits_per_repo:
            sorted_repos = sorted(commits_per_repo.items(), key=lambda x: x[1], reverse=True)
            top_3_repo = [repo[0] for repo in sorted_repos[:3]]

        lang_with_bytes = getattr(tech_stack_db, "language_with_code_byte", {}) or {}
        top_languages = []
        if lang_with_bytes:
            sorted_langs = sorted(lang_with_bytes.items(), key=lambda x: x[1], reverse=True)
            top_languages = [lang[0] for lang in sorted_langs[:3]]

        data = {
            "name": getattr(profile_db, "name", ""),
            "public_repos": getattr(profile_db, "public_repo", 0),
            "profile_picture": getattr(profile_db, "profile_pic", ""),
            "followers": getattr(profile_db, "followers", 0),
            "following": getattr(profile_db, "following", 0),
            "total_commits": getattr(user_commit, "total_commits", 0),
            "top_3_repo": top_3_repo,
            "longest_streak": getattr(user_consistency, "longest_streak", 0),
            "current_streak": getattr(user_consistency, "current_streak", 0),
            "active_days": getattr(user_consistency, "active_days", 0),
            "pull_requests": getattr(open_source_db, "pull_requests", {}),
            "issues": getattr(open_source_db, "issues", {}),
            "repositories_contributed_to": getattr(open_source_db, "repositories_contributed_to", []),
            "code_reviews": getattr(open_source_db, "code_reviews", {}),
            "all_languages": getattr(tech_stack_db, "all_languages", []),
            "most_used_language": top_languages,
            "code_score": getattr(code_qual, "code_level", "N/A"),
            "code_level": getattr(code_qual, "code_score", 0),
            "average_lines_readme": getattr(document_stats_db, "avg_lines_readme", 0),
            "comment_percentage": getattr(document_stats_db, "comment_percentage", 0.0),
            "file_structure": getattr(profile_db, "file_structure", 0),
            "detected_frameworks": getattr(profile_db, "detected_frameworks", []),
            "recommended_role": getattr(profile_db, "recommended_role", []),
            "final_score": getattr(profile_db, "final_score", 0),
        }
        return sanitize_data(data)
    finally:
        if local_session:
            db.close()