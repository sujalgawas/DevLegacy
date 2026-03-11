from sqlalchemy import Column, String, Integer,DateTime
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from app.db.base import Base

#================ database models start ================#
class Code_quality(Base):
    __tablename__ = 'code_quality'
    uid = Column(String, primary_key=True)
    code_score = Integer
    code_level = String
    
#================ database models end ================#