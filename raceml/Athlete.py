import sqlalchemy
import sqlalchemy.orm
from .Base import Base
from .Team import Team


class Athlete(Base):
    __tablename__ = "athletes"
    id = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    dob = sqlalchemy.Column(sqlalchemy.Date)

    team_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("teams.id"))
    team = sqlalchemy.orm.relationship("Team", back_populates="athletes")

    def __repr__(self):
        return f"<Athlete(name={self.name}, dob={self.dob}, team={self.team})>"
