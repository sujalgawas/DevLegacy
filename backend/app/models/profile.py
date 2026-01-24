from sqlalchemy import Column,Integer,String
from db.base import Base 

class github_profile(Base):
    __tablename__ = "github_profile"
    uid = Column(String,primary_key = True)
    github_id = Column(String)
    github_profile = Column(String)
    name = Column(String)
    public_repo = Column(Integer)
    followers = Column(Integer)
    following = Column(Integer)