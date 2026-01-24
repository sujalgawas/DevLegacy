from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from db.base import Base

#================ database models start ================#
class tech_stack(Base):
    __tablename__ = "tech_stack"
    uid = Column(String,primary_key=True)
    all_languages = Column(ARRAY(String))
    language_with_code_byte = Column(JSONB) 
#================ database models end ================#