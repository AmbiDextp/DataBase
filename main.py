from fastapi import FastAPI
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, CheckConstraint
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from starlette.applications import Starlette

from starlette_admin.contrib.sqla import Admin, ModelView

SQLALCHEMY_DATABASE_URL = "sqlite:///./University.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

Base = declarative_base()


class Curator(Base):
    __tablename__ = "Curators"
 
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)

class Group(Base):
    __tablename__ = "Groups"
 
    id = Column(Integer, primary_key=True, autoincrement=True)
    curator_id = Column(Integer, ForeignKey('Curators.id'), nullable=False, unique=True)
    name_number = Column(String, nullable=False)


class Student(Base):
    __tablename__ = "Students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey('Groups.id'), nullable=False)
    name = Column(String, nullable=False)
    birthday = Column(String, nullable=False)

class Course(Base):
    __tablename__ = "Courses"
 
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False, unique=True)  

class Mark(Base):
    __tablename__ = "Marks"
    __table_args__ = (
        CheckConstraint('mark >= 2 AND mark <= 5', name='mark_range_check'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey('Courses.id'), nullable=False)
    student_id = Column(Integer, ForeignKey('Students.id', ondelete='CASCADE'), nullable=False)
    mark = Column(Integer)

class Degree(Base):
    __tablename__ = "Degrees"
 
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    title = Column(String, nullable=False, unique=True)

class Position(Base):
    __tablename__ = "Positions"
 
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)

class Teacher(Base):
    __tablename__ = "Teachers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    degree_id = Column(Integer, ForeignKey('Degrees.id'), nullable=False)
    position_id = Column(Integer, ForeignKey('Positions.id'), nullable=False)
    name = Column(String, nullable=False)

class Lesson(Base):
    __tablename__ = "Lessons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey('Groups.id'), nullable=False)
    teacher_id = Column(Integer, ForeignKey('Teachers.id', ondelete='CASCADE'), nullable=False)
    course_id = Column(Integer, ForeignKey('Courses.id'), nullable=False)




Base.metadata.create_all(bind = engine)

app = FastAPI()

admin = Admin(engine, title="Example: SQLAlchemy")
admin.add_view(ModelView(Student))
admin.add_view(ModelView(Lesson))
admin.add_view(ModelView(Group))
admin.add_view(ModelView(Teacher))
admin.add_view(ModelView(Mark))
admin.add_view(ModelView(Course))
admin.add_view(ModelView(Curator))
admin.add_view(ModelView(Degree))
admin.add_view(ModelView(Position))
admin.mount_to(app)