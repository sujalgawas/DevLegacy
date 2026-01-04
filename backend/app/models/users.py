from sqlalchemy import Column, String
from db.base import Base

#================ database models start ================#
"""
CREATE TABLE users(
	uid VARCHAR(100) PRIMARY KEY,
	Email VARCHAR(50),
	UserName VARCHAR(50)
);
"""

class User(Base):
    __tablename__ = 'users'
    uid = Column(String, primary_key=True)
    email = Column(String)
    username = Column(String)

#================ database models end ================#