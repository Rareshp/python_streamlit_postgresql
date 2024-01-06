from sqlalchemy import Table, Column, Integer, String, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func
import datetime

# we must define the table format
# otherwise use text(raw sql)
class Base(DeclarativeBase):
    pass

class my_table(Base):
    __tablename__ = "my_table"
    id: Mapped[int] = mapped_column(primary_key=True)
    tag_name:  Mapped[str] = mapped_column(String(40), nullable=False)
    num_value: Mapped[int] = mapped_column(Integer)
    str_value: Mapped[str] = mapped_column(String(40))
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
