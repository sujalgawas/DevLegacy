from fastAPI import APIRouter,Depends, HTTPException, status
from schemas.User import Login, SignUp, Test
from main import get_session #from crud.user import get_session

from models.users import User
from models.test import Testing

router = APIRouter()
session = get_session()

@router.get('/username/analysis/{gitname}')
async def get_anaylsis(gitname:str):
    pass


@router.post("/login")
def login(login:Login):
    uid = verify_token(login.token)
    
    #postgres SQL session activate 
    
    if uid:
        return {"message" : "user logged in successfull"},200
    else:
        return {"message" : "Error occured while loggin in"},401

@router.post("/test")
def test(test:Test):
    current_test = Testing(name = test.name,age = test.age,temp = test.temp)
    session.add(current_test)
    session.commit()
    
    return{"message":"working"},200

@router.post("/signup")
def signup(signup:SignUp):
    user = auth.create_user(email= signup.Email,password=signup.Password,
                            display_name = signup.UserName)
    current_uid = user.uid
    
    user = User(uid = current_uid,email = signup.Email, username = signup.UserName)
    session.add(user)
    session.commit()
    
    if user.uid:
        return {"message":"user created"},200
    else:
        return {"message":"Error creating user"},401
    

@router.get("/")
def home():
    return {"message":"home page"}



"""
#testing github api
@router.get("/username/{gitname}")
async def get_user_data(gitname : str):
    
    url = f"https://api.github.com/search/users?q={gitname}"
    
    reponse = github_api(url)
    
    if reponse.status_code == 200:
        return {"message" : "api works",
                "data":reponse.json()},200
    else:
        return {"message" : "error api request"},401
"""