from sqlalchemy import Column, String, Integer,DateTime
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from db.base import Base

#================ database models start ================#
class consistency_status(Base):
    __tablename__ = 'consistency_status'
    uid = Column(String, primary_key=True)
    total_contributions = Column(Integer)
    longest_streak = Column(Integer)
    current_streak = Column(Integer)
    active_days = Column(Integer)
    last_updated = Column(DateTime)
#================ database models end ================#