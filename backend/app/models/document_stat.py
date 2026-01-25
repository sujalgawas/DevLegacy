from sqlalchemy import Column, String, Integer,DateTime
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from db.base import Base

#================ database models start ================#
class document_stats(Base):
    __tablename__ = 'document_stats'
    uid = Column(String, primary_key=True)
    comment_per = Column(Integer)
    comment_to_repo = Column(JSONB)
    documentation = Column(Integer)
    
#================ database models end ================#