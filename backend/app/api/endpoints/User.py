from fastapi import APIRouter,Depends, HTTPException, status
from app.schemas.User import Login, SignUp, Test
from app.crud.User import get_session, get_db
from sqlalchemy.orm import Session

from app.models.users import User
from app.models.test import Testing

from app.services.helper_function import verify_token
from firebase_admin import auth

router = APIRouter()
# session = get_session()


@router.post("/login")
def login(login:Login):
    uid = verify_token(login.token)
    
    #postgres SQL session activate 
    
    if uid:
        return {"message" : "user logged in successfull"}
    else:
        raise HTTPException(status_code=401, detail="Error occured while loggin in")

@router.post("/test")
def test(test:Test, db: Session = Depends(get_db)):
    current_test = Testing(name = test.name,age = test.age,temp = test.temp)
    db.add(current_test)
    db.commit()
    
    return{"message":"working"}

@router.post("/signup")
def signup(signup:SignUp, db: Session = Depends(get_db)):
    user = auth.create_user(email= signup.Email,password=signup.Password,
                            display_name = signup.UserName)
    current_uid = user.uid
    
    user = User(uid = current_uid,email = signup.Email, username = signup.UserName)
    db.add(user)
    db.commit()
    
    if user.uid:
        return {"message":"user created"}
    else:
        raise HTTPException(status_code=401, detail="Error creating user")
    

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