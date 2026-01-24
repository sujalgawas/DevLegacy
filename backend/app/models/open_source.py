from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from db.base import Base

#================ database models start ================#
class open_source(Base):
    __tablename__ = "open_source"
    uid = Column(String,primary_key=True)
    pull_requests = Column(JSONB)
    issues = Column(JSONB)
    repositories_contributed_to = Column(ARRAY(String))
    code_reviews = Column(JSONB)
#================ database models end ================#