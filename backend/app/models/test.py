from sqlalchemy import Column,String, Integer
from db.base import Base

class Testing(Base):
    __tablename__ = 'testing'
    name = Column(String)
    age = Column(String) 
    temp = Column(Integer,primary_key=True)