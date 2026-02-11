from pydantic import BaseModel


#================ FastAPI BaseModel Start ================#
class Login(BaseModel):
    token : str
    
class SignUp(BaseModel):
    UserName : str
    Email : str
    Password: str

class Test(BaseModel):
    name : str
    age : str
    temp : int

class GithubProfile(BaseModel):
    github_id : str
    github_profile : str
    profile_pic : str
    name : str
    public_repo : int
    followers : int
    following : int
    
"""
class User_Data(BaseModel):
    followers : int
    repos : int 
    total_commits : int
"""
#================ FastAPI BaseModel End ================#
