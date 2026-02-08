from app.schemas.User import GithubProfile
from fastapi import APIRouter, Depends, HTTPException
from app.services.github import get_total_commit,get_consistency,get_open_source,get_tech_stack,get_code,get_documenation_stats,get_github_profile
from app.crud.User import update_code, update_commit_status, update_document_status, update_github_profile, update_open_source,update_consistency_status, update_tech_stack
import asyncio

router = APIRouter()

class AnalysisRequest:
    def __init__(self, get_total_commit = get_total_commit, get_consistency = get_consistency, get_open_source = get_open_source, get_tech_stack = get_tech_stack,
                 get_code = get_code, get_documentation_stats = get_documenation_stats, get_github_profile = get_github_profile, uid=None, gitname=None):
        self.get_total_commit = get_total_commit
        self.get_consistency = get_consistency
        self.get_open_source = get_open_source
        self.get_tech_stack = get_tech_stack
        self.get_code = get_code
        self.get_documentation_stats = get_documentation_stats
        self.get_github_profile = get_github_profile
        self.uid = uid
        self.gitname = gitname

    async def process(self):
        
        total_commit = asyncio.to_thread(self.get_total_commit, self.gitname)
        consistency = asyncio.to_thread(self.get_consistency, self.gitname)
        open_source = asyncio.to_thread(self.get_open_source, self.gitname)
        tech_stack = asyncio.to_thread(self.get_tech_stack, self.gitname)
        code = asyncio.to_thread(self.get_code, self.gitname)
        documentation = asyncio.to_thread(self.get_documentation_stats, self.gitname)
        github_profile = asyncio.to_thread(self.get_github_profile, self.gitname)
        
        self.result = await asyncio.gather(
            total_commit,
            consistency,
            open_source,
            tech_stack,
            code,
            documentation,
            github_profile)

        return {
            "total_commit": self.result[0],
            "consistency": self.result[1],
            "open_source": self.result[2],
            "tech_stack": self.result[3],
            "code": self.result[4],
            "documentation": self.result[5],
            "github_profile": self.result[6],
        }
    
    async def db_storing(self,result):
        #commit_status
        try:
            update_commit_status(uid = self.uid,
                                 total_commits = result["total_commit"]["total_commits"],
                                 commit_per_repo = result["total_commit"]["commit_per_repo"])
            
        except Exception as e:
              return f"Error updating commit_status with {e}"
        
        #github_profile
        try:
            profile = GithubProfile(
                github_id = result["github_profile"]["github_id"],
                github_profile = result["github_profile"]["github_profile"],
                name = result["github_profile"]["name"],
                public_repo = result["github_profile"]["public_repo"],
                followers = result["github_profile"]["followers"],
                following = result["github_profile"]["following"]
            )
            update_github_profile(uid = self.uid,
                                  profile = profile)
        except Exception as e:
            return f"Error updating github_profile with {e}"
        
        #open_source
        try:
            update_open_source(uid = self.uid,
                               pull_requests = result["open_source"]["pull_requests"],
                               issues = result["open_source"]["issues"],
                               repositories_contributed_to = result["open_source"]["repositories_contributed_to"],
                               code_reviews = result["open_source"]["code_reviews"])
        except Exception as e:
            return f"Error updating open_source with {e}"

        #consistency_status
        try:
            update_consistency_status(uid = self.uid,
                               total_contributions = result["consistency"]["total_contributions"],
                               longest_streak = result["consistency"]["longest_streak"],
                               current_streak = result["consistency"]["current_streak"],
                               active_days_count= result["consistency"]["active_days_count"])
        except Exception as e:
            return f"Error updating consistency with {e}"
        
        #document_status
        try:
            update_document_status(uid = self.uid,
                                 avg_lines_readme= result["documentation"]["avg_lines_readme"],
                                 comment_percentage= result["documentation"]["comment_percentage"],
                                 comment_pre_repos= result["documentation"]["comment_pre_repos"],
                                 final_dir= result["documentation"]["final_dir"])
        except Exception as e:
            return f"Error updating documentation with {e}"
        
        #code
        try:
            update_code(uid = self.uid,
                        code_data=result["code"]["code_data"])
        except Exception as e:
            return f"Error updating code with {e}"
        
        #tech_stack
        try:
            update_tech_stack(uid = self.uid,
                              all_languages = result["tech_stack"]["all_languages"],
                              language_with_code_byte = result["tech_stack"]["language_with_code_byte"])
        except Exception as e:
            return f"Error updating tech_stack with {e}"

@router.get('/username/analysis/{gitname}')
async def get_anaylsis(gitname: str):
    uid = "1"

    analysis_request = AnalysisRequest(
        uid=uid,
        gitname=gitname
    )

    result = await analysis_request.process()
    
    db_storing = await analysis_request.db_storing(result=result)
    
    if db_storing:
        return db_storing
    
    return result

    """    
    #functions
    total_commit = get_total_commit(uid = uid, gitname=gitname)
    
    consistency = get_consistency(uid=uid, gitname=gitname)
    
    open_source = get_open_source(uid=uid, gitname=gitname)
    
    tech_stack = get_tech_stack(uid=uid, gitname=gitname)
    
    code = get_code(uid=uid, gitname=gitname)
    
    documentation = get_documenation_stats(uid=uid,gitname=gitname)
    
    github_profile = get_github_profile(uid=uid, gitname=gitname)
    
    return {
        "total_commit": total_commit,
        "consistency": consistency,
        "open_source": open_source,
        "tech_stack": tech_stack,
        "documentation": documentation,
        "code": code,
        "github_profile": github_profile
    }       
    """