from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, CheckConstraint
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from starlette.applications import Starlette
import uvicorn


from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import date

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

@app.get('/')
def Hello():
    html_content = "<h2>url/docs -- для действий с эндпоинтами</h2> <h2>url/admin -- админка(просто либа)</h2> <h2>url/table_name -- вывод всех данных таблицы</h2>"
    return HTMLResponse(content=html_content)

admin = Admin(engine, title="DataBase")
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

# ------------------------------------------------------------------------------------------------

def get_db():
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()

# Pydantic модели для запросов и ответов
class CuratorCreate(BaseModel):
    name: str

class CuratorResponse(CuratorCreate):
    id: int

class GroupCreate(BaseModel):
    curator_id: int
    name_number: str

class GroupResponse(GroupCreate):
    id: int

class StudentCreate(BaseModel):
    group_id: int
    name: str
    birthday: str  # или можно использовать date если преобразуете строку

class StudentResponse(StudentCreate):
    id: int

class CourseCreate(BaseModel):
    title: str

class CourseResponse(CourseCreate):
    id: int

class MarkCreate(BaseModel):
    course_id: int
    student_id: int
    mark: int

class MarkResponse(MarkCreate):
    id: int

class DegreeCreate(BaseModel):
    title: str

class DegreeResponse(DegreeCreate):
    id: int

class PositionCreate(BaseModel):
    title: str

class PositionResponse(PositionCreate):
    id: int

class TeacherCreate(BaseModel):
    degree_id: int
    position_id: int
    name: str

class TeacherResponse(TeacherCreate):
    id: int

class LessonCreate(BaseModel):
    group_id: int
    teacher_id: int
    course_id: int

class LessonResponse(LessonCreate):
    id: int

# Эндпоинты для Curator
@app.post("/curators/", response_model=CuratorResponse)
def create_curator(curator: CuratorCreate, db: Session = Depends(get_db)):
    db_curator = Curator(**curator.dict())
    db.add(db_curator)
    db.commit()
    db.refresh(db_curator)
    return db_curator

@app.get("/curators/", response_model=List[CuratorResponse])
def read_curators(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Curator).offset(skip).limit(limit).all()

@app.get("/curators/{curator_id}", response_model=CuratorResponse)
def read_curator(curator_id: int, db: Session = Depends(get_db)):
    curator = db.query(Curator).filter(Curator.id == curator_id).first()
    if curator is None:
        raise HTTPException(status_code=404, detail="Curator not found")
    return curator

@app.put("/curators/{curator_id}", response_model=CuratorResponse)
def update_curator(curator_id: int, curator: CuratorCreate, db: Session = Depends(get_db)):
    db_curator = db.query(Curator).filter(Curator.id == curator_id).first()
    if db_curator is None:
        raise HTTPException(status_code=404, detail="Curator not found")
    for key, value in curator.dict().items():
        setattr(db_curator, key, value)
    db.commit()
    db.refresh(db_curator)
    return db_curator

@app.delete("/curators/{curator_id}")
def delete_curator(curator_id: int, db: Session = Depends(get_db)):
    db_curator = db.query(Curator).filter(Curator.id == curator_id).first()
    if db_curator is None:
        raise HTTPException(status_code=404, detail="Curator not found")
    db.delete(db_curator)
    db.commit()
    return {"message": "Curator deleted successfully"}

# Эндпоинты для Group (аналогично для остальных моделей)
@app.post("/groups/", response_model=GroupResponse)
def create_group(group: GroupCreate, db: Session = Depends(get_db)):
    db_group = Group(**group.dict())
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

@app.get("/groups/", response_model=List[GroupResponse])
def read_groups(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Group).offset(skip).limit(limit).all()

@app.get("/groups/{group_id}", response_model=GroupResponse)
def read_group(group_id: int, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    return group

@app.put("/groups/{group_id}", response_model=GroupResponse)
def update_group(group_id: int, group: GroupCreate, db: Session = Depends(get_db)):
    db_group = db.query(Group).filter(Group.id == group_id).first()
    if db_group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    for key, value in group.dict().items():
        setattr(db_group, key, value)
    db.commit()
    db.refresh(db_group)
    return db_group

@app.delete("/groups/{group_id}")
def delete_group(group_id: int, db: Session = Depends(get_db)):
    db_group = db.query(Group).filter(Group.id == group_id).first()
    if db_group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    db.delete(db_group)
    db.commit()
    return {"message": "Group deleted successfully"}

# Аналогичные эндпоинты для остальных моделей (Student, Course, Mark, Degree, Position, Teacher, Lesson)
# Шаблон тот же: POST для создания, GET для чтения (одного или списка), PUT для обновления, DELETE для удаления

# Пример для Student
@app.post("/students/", response_model=StudentResponse)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    db_student = Student(**student.dict())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

@app.get("/students/", response_model=List[StudentResponse])
def read_students(db = Depends(get_db)):
    return db.query(Student)

@app.get("/students/{student_id}", response_model=StudentResponse)
def read_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@app.put("/students/{student_id}", response_model=StudentResponse)
def update_student(student_id: int, student: StudentCreate, db: Session = Depends(get_db)):
    db_student = db.query(Student).filter(Student.id == student_id).first()
    if db_student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    for key, value in student.dict().items():
        setattr(db_student, key, value)
    db.commit()
    db.refresh(db_student)
    return db_student

@app.delete("/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    db_student = db.query(Student).filter(Student.id == student_id).first()
    if db_student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(db_student)
    db.commit()
    return {"message": "Student deleted successfully"}

# Дополнительные эндпоинты для специфичных запросов
@app.get("/groups/{group_id}/students", response_model=List[StudentResponse])
def read_group_students(group_id: int, db: Session = Depends(get_db)):
    students = db.query(Student).filter(Student.group_id == group_id).all()
    return students

@app.get("/teachers/{teacher_id}/lessons", response_model=List[LessonResponse])
def read_teacher_lessons(teacher_id: int, db: Session = Depends(get_db)):
    lessons = db.query(Lesson).filter(Lesson.teacher_id == teacher_id).all()
    return lessons

@app.get("/students/{student_id}/marks", response_model=List[MarkResponse])
def read_student_marks(student_id: int, db: Session = Depends(get_db)):
    marks = db.query(Mark).filter(Mark.student_id == student_id).all()
    return marks

@app.get("/courses/{course_id}/marks", response_model=List[MarkResponse])
def read_course_marks(course_id: int, db: Session = Depends(get_db)):
    marks = db.query(Mark).filter(Mark.course_id == course_id).all()
    return marks


if __name__ == '__main__':
    uvicorn.run("main:app", reload=True)