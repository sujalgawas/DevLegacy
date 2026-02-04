from fastapi import APIRouter, Depends, HTTPException
from app.services.github import get_total_commit,get_consistency,get_open_source,get_tech_stack,get_code,get_documenation_stats,get_github_profile
from multiprocessing import Process, Queue

router = APIRouter()

class AnalysisRequest:
    def __init__(self,get_total_commit,get_consistency,get_open_source,get_tech_stack,get_code,
                 get_documentation_stats,get_github_profile,q,uid,gitname):
        self.get_total_commit = get_total_commit
        self.get_consistency = get_consistency
        self.get_open_source = get_open_source
        self.get_tech_stack = get_tech_stack
        self.get_code = get_code 
        self.get_documentation_stats = get_documentation_stats
        self.get_github_profile = get_github_profile
        self.q = q
        self.uid = uid 
        self.gitname = gitname
    
    def process(self):
        
        processes = [Process(target=self.get_total_commit, args=(self.uid,self.gitname,self.q)),
                Process(target=self.get_consistency, args=(self.uid,self.gitname,self.q)),
                Process(target=self.get_open_source, args=(self.uid,self.gitname,self.q)),
                Process(target=self.get_tech_stack, args=(self.uid,self.gitname,self.q)),
                Process(target=self.get_code, args=(self.uid,self.gitname,self.q)),
                Process(target=self.get_documentation_stats, args=(self.uid,self.gitname,self.q)),
                Process(target=self.get_github_profile, args=(self.uid,self.gitname,self.q))]

        result = {}
        
        for p in processes:
            p.start()
        
        for p in processes:
            p.join()
            
        for _ in processes:
            key, value = self.q.get()
            result[key] = value
        
        return result
        
            
@router.get('/username/analysis/{gitname}')
async def get_anaylsis(gitname:str):
    uid = "1"
    
    q = Queue()
    
    analysis_request = AnalysisRequest(get_total_commit = get_total_commit, get_consistency = get_consistency, get_open_source = get_open_source,
                                      get_tech_stack = get_tech_stack, get_code = get_code, get_documentation_stats = get_documenation_stats, get_github_profile = get_github_profile,
                                      q = q, uid = uid, gitname = gitname)
    
    result = analysis_request.process()
    """
    test = Process(target=get_total_commit, args=(uid, gitname,q))
    test.start()
    test.join()
    
    result = q.get()
    """
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