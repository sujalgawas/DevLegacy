from sqlalchemy import Column, String, Integer,DateTime
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from db.base import Base

#================ database models start ================#
class Code(Base):
    __tablename__ = 'code'
    uid = Column(String, primary_key=True)
    code = Column(JSONB)
    
#================ database models end ================#