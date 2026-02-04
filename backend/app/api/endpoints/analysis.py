from fastapi import APIRouter, Depends, HTTPException
from app.services.github import get_total_commit,get_consistency,get_open_source,get_tech_stack,get_code,get_documenation_stats,get_github_profile

router = APIRouter()

class AnalysisRequest:
    def __init__(self, get_total_commit, get_consistency, get_open_source, get_tech_stack,
                 get_code, get_documentation_stats, get_github_profile, uid, gitname):
        self.get_total_commit = get_total_commit
        self.get_consistency = get_consistency
        self.get_open_source = get_open_source
        self.get_tech_stack = get_tech_stack
        self.get_code = get_code
        self.get_documentation_stats = get_documentation_stats
        self.get_github_profile = get_github_profile
        self.uid = uid
        self.gitname = gitname

    def process(self):
        total_commit = self.get_total_commit(self.uid, self.gitname)
        consistency = self.get_consistency(self.uid, self.gitname)
        open_source = self.get_open_source(self.uid, self.gitname)
        tech_stack = self.get_tech_stack(self.uid, self.gitname)
        code = self.get_code(self.uid, self.gitname)
        documentation = self.get_documentation_stats(self.uid, self.gitname)
        github_profile = self.get_github_profile(self.uid, self.gitname)

        return {
            "total_commit": total_commit,
            "consistency": consistency,
            "open_source": open_source,
            "tech_stack": tech_stack,
            "code": code,
            "documentation": documentation,
            "github_profile": github_profile,
        }



@router.get('/username/analysis/{gitname}')
async def get_anaylsis(gitname: str):
    uid = "1"

    analysis_request = AnalysisRequest(
        get_total_commit=get_total_commit,
        get_consistency=get_consistency,
        get_open_source=get_open_source,
        get_tech_stack=get_tech_stack,
        get_code=get_code,
        get_documentation_stats=get_documenation_stats,
        get_github_profile=get_github_profile,
        uid=uid,
        gitname=gitname
    )

    result = analysis_request.process()
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