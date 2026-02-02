from fastapi import APIRouter, Depends, HTTPException
from app.services.github import get_total_commit,get_consistency,get_open_source,get_tech_stack,get_code,get_documenation_stats,get_github_profile

router = APIRouter()

@router.get('/username/analysis/{gitname}')
async def get_anaylsis(gitname:str):
    uid = "1"
    
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