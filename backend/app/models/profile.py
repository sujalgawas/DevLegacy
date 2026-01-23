from sqlaclchmey import Columns,Integer,String 
from db.base import Base 

class github_profile(Base):
    __tablename__ = "github_profile"
    uid = Columns(String,primary_key = True)
    gitub_user_id = Columns()
    github_profile = Columns()
    public_repo = Columns()
    followers = Columns()
    following = Columns()