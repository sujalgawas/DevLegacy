from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.postgresql import JSONB 
from db.base import Base

#================ database models start ================#
class commit_status(Base):
    __tablename__ = "commit_status"
    uid = Column(String,primary_key=True)
    total_commits = Column(Integer)
    commits_per_repo = Column(JSONB) 
#================ database models end ================#