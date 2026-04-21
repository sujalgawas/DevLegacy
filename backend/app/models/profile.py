from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from app.db.base import Base 

class github_profile(Base):
    __tablename__ = "github_profile"
    uid = Column(String, primary_key=True)
    github_id = Column(String)
    github_profile = Column(String)
    profile_pic = Column(String)
    name = Column(String)
    public_repo = Column(Integer)
    followers = Column(Integer)
    following = Column(Integer)
    recommended_role = Column(JSONB)
    detected_frameworks = Column(JSONB)
    final_score = Column(Integer)
    file_structure = Column(Integer)