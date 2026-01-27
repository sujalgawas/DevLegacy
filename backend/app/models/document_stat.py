from sqlalchemy import Column, String, Integer,DateTime
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from db.base import Base

#================ database models start ================#
class document_stats(Base):
    __tablename__ = 'document_stats'
    uid = Column(String, primary_key=True)
    avg_lines_readme = Column(Integer)
    comment_percentage = Column(Integer)
    comment_to_repos = Column(JSONB)
    final_dir = Column(JSONB)
    
#================ database models end ================#