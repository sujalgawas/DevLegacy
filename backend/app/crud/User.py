import datetime

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine,Column,Integer,String

from app.models.commit_status import commit_status
from app.models.profile import github_profile
from app.models.tech_stack import tech_stack
from app.models.open_source import open_source
from app.models.consistency import consistency_status
from app.models.document_stat import document_stats
from app.models.code import Code

engine = create_engine("postgresql://postgres:1234@localhost:5432/dev")

def get_session():
    Session = sessionmaker(engine)
    session = Session()
    return session

session = get_session()


def update_commit_status(uid:str, total_commits:int, commit_per_repo:dict):
    user_commit_metadata = session.query(commit_status).filter_by(uid=uid).first()

    if user_commit_metadata:
        user_commit_metadata.total_commits = total_commits
        user_commit_metadata.commits_per_repo = commit_per_repo
    else:
        user_commit_metadata = commit_status(
            uid=uid,
            total_commits=total_commits,
            commits_per_repo=commit_per_repo
        )
        session.add(user_commit_metadata)

    session.commit()


def update_github_profile(uid,profile):
    
    profile_db = session.query(github_profile).filter_by(uid=uid).first()
    
    if profile_db:
        profile_db.github_id = profile.github_id
        profile_db.github_profile = profile.github_profile
        profile_db.name = profile.name
        profile_db.public_repo = profile.public_repo
        profile_db.followers = profile.followers
        profile_db.following = profile.following
    else:
        profile_db = github_profile(uid = uid,
                                github_id = profile.github_id,
                                github_profile = profile.github_profile,
                                name = profile.name,
                                public_repo = profile.public_repo,
                                followers = profile.followers,
                                following = profile.following)
        
        session.add(profile_db)
        
    session.commit()    

def update_tech_stack(uid:str,all_languages:list,language_with_code_byte:dict):        
    tech_stack_db = session.query(tech_stack).filter_by(uid=uid).first()
    
    if tech_stack_db:
        tech_stack_db.all_languages = all_languages
        tech_stack_db.language_with_code_byte = language_with_code_byte
    else:
        tech_stack_db = tech_stack(
            uid=uid,
            all_languages=list(all_languages),
            language_with_code_byte=language_with_code_byte
        )
        session.add(tech_stack_db)
    
    session.commit()

def update_open_source(uid:str,pull_requests:dict,issues:dict,
                       repositories_contributed_to:list,code_reviews:dict):
    open_source_db = session.query(open_source).filter_by(uid=uid).first()
    
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
            code_reviews=code_reviews
        )
        session.add(open_source_db)
    
    session.commit()

def update_consistency_status(uid:str,total_contributions:int,
                              current_streak:int,longest_streak:int,
                              active_days_count:int):
    
    user_consistency = session.query(consistency_status).filter_by(uid=uid).first()

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
            last_updated=datetime.utcnow()
        )
        session.add(user_consistency)

    session.commit()

def update_document_status(uid:str, avg_lines_readme:int,
                           comment_percentage:int,comment_pre_repos:dict,final_dir:dict):
    document_stats_db = session.query(document_stats).filter_by(uid=uid).first()
    
    if document_stats_db:
        document_stats_db.uid = uid
        document_stats_db.avg_lines_readme = avg_lines_readme
        document_stats_db.comment_percentage = comment_percentage
        document_stats_db.comment_to_repos = comment_pre_repos
        document_stats_db.final_dir = final_dir
    else:
        document_stats_db = document_stats(uid = uid,avg_lines_readme=avg_lines_readme,
                                           comment_percentage=comment_percentage,comment_to_repos=comment_pre_repos,
                                           final_dir = final_dir)

        session.add(document_stats_db)
        
    session.commit()

def update_code(uid:str,code_data:dict):
    code_db = session.query(Code).filter_by(uid = uid).first()
    
    if code_db:
        code_db.uid = uid
        code_db.code = code_data
    else:
        code_db = Code(uid = uid,
                       code = code_data)
        session.add(code_db)
    session.commit()