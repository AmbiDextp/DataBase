from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Annotated, List
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, CheckConstraint, distinct, func
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, Session, relationship
from pydantic import BaseModel
from starlette_admin.contrib.sqla import Admin, ModelView
import uvicorn

engine = create_engine("sqlite:///./University.db", connect_args={"check_same_thread": False})

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
    curator = relationship("Curator")

class Student(Base):
    __tablename__ = "Students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey('Groups.id'), nullable=False)
    name = Column(String, nullable=False)
    birthday = Column(String, nullable=False)
    group = relationship("Group")


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
    course = relationship("Course")
    student = relationship("Student")

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
    degree = relationship("Degree")
    position = relationship("Position")


class Lesson(Base):
    __tablename__ = "Lessons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey('Groups.id'), nullable=False)
    teacher_id = Column(Integer, ForeignKey('Teachers.id', ondelete='CASCADE'), nullable=False)
    course_id = Column(Integer, ForeignKey('Courses.id'), nullable=False)
    time = Column(String, nullable=False)

    group = relationship("Group")
    teacher = relationship("Teacher")
    course = relationship("Course")


Base.metadata.create_all(bind = engine)


def get_db():
    with Session(engine) as session:
        yield session

dbDep = Annotated[Session, Depends(get_db)]

app = FastAPI()

@app.get('/')
def Hello():
    html_content = "<h2>url/docs -- для действий с эндпоинтами</h2> <h2>url/admin -- админка(просто либа)</h2> <h2>url/table_name -- вывод всех данных таблицы</h2>"
    return HTMLResponse(content=html_content)

#-------------------------------------- MMMHHHHMMMM DELICIOUS --------------------------------------

class CuratorCreate(BaseModel):
    name: str

class CuratorResponse(CuratorCreate):
    id: int

@app.post("/curators/", tags=["CRUD"], response_model=CuratorResponse)
def create_curator(curator: CuratorCreate, db: dbDep):
    curator_db = Curator.model_validate(curator)
    db.add(curator_db)
    db.commit()
    db.refresh(curator_db)
    return curator_db

@app.get("/curators/", tags=["CRUD"], response_model=List[CuratorResponse])
def read_curators(db: dbDep):
    return db.query(Curator).all()

@app.get("/curators/{curator_id}", tags=["CRUD"])
def read_curator(curator_id: int, db: dbDep):
    curator = db.get(Curator, curator_id)
    if not curator:
        raise HTTPException(status_code=404, detail="Curator not found")
    return curator   

@app.put("/curators/{curator_id}", tags=["CRUD"], response_model=CuratorResponse)
def update_curator(curator_id: int, curator: CuratorCreate, db: dbDep):
    curator_db = db.get(Curator, curator_id)
    if not curator_db:
        raise HTTPException(status_code=404, detail="Curator not found")
    curator_db.name = curator.name
    db.commit()
    db.refresh(curator_db)
    return curator_db


@app.delete("/curators/{curator_id}", tags=["CRUD"])
def delete_curator(curator_id: int, db: dbDep):
    curator = db.get(Curator, curator_id)
    if not curator:
        raise HTTPException(status_code=404, detail="Curator not found")
    db.delete(curator)
    db.commit()
    return {"ok": True}


class GroupCreate(BaseModel):
    curator_id: int
    name_number: str

class GroupResponse(GroupCreate):
    id: int

@app.post("/groups/", tags=["CRUD"], response_model=GroupResponse)
def create_group(group: GroupCreate, db: dbDep):
    group_db = Group.model_validate(group)
    db.add(group_db)
    db.commit()
    db.refresh(group_db)
    return group_db

@app.get("/groups/", tags=["CRUD"], response_model=List[GroupResponse])
def read_groups(db: dbDep):
    return db.query(Group).all()

@app.get("/groups/{group_id}", tags=["CRUD"])
def read_group(group_id: int, db: dbDep):
    group = db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group   

@app.put("/groups/{group_id}", tags=["CRUD"], response_model=GroupResponse)
def update_group(group_id: int, group: GroupCreate, db: dbDep):
    group_db = db.get(Group, group_id)
    if not group_db:
        raise HTTPException(status_code=404, detail="Group not found")
    group_db.name_number = group.name_number
    group_db.curator_id = group.curator_id  
    db.commit()
    db.refresh(group_db)
    return group_db

@app.delete("/groups/{group_id}", tags=["CRUD"])
def delete_group(group_id: int, db: dbDep):
    group = db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    db.delete(group)
    db.commit()
    return {"ok": True}


class StudentCreate(BaseModel):
    group_id: int
    name: str
    birthday: str

class StudentResponse(StudentCreate):
    id: int

@app.post("/students/", tags=["CRUD"], response_model=StudentResponse)
def create_student(student: StudentCreate, db: dbDep):
    student_db = Student.model_validate(student)
    db.add(student_db)
    db.commit()
    db.refresh(student_db)
    return student_db

@app.get("/students/", tags=["CRUD"], response_model=List[StudentResponse])
def read_students(db: dbDep):
    return db.query(Student).all()

@app.get("/students/{student_id}", tags=["CRUD"])
def read_student(student_id: int, db: dbDep):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student  

@app.put("/students/{student_id}", tags=["CRUD"], response_model=StudentResponse)
def update_student(student_id: int, student: StudentCreate, db: dbDep):
    student_db = db.get(Student, student_id)
    if not student_db:
        raise HTTPException(status_code=404, detail="Student not found")
    student_db.group_id = student.group_id
    student_db.name = student.name
    student_db.birthday = student.birthday
    db.commit()
    db.refresh(student_db)
    return student_db

@app.delete("/students/{student_id}", tags=["CRUD"])
def delete_student(student_id: int, db: dbDep):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(student)
    db.commit()
    return {"ok": True}


class CourseCreate(BaseModel):
    title: str

class CourseResponse(CourseCreate):
    id: int

@app.post("/courses/", tags=["CRUD"], response_model=CourseResponse)
def create_course(course: CourseCreate, db: dbDep):
    course_db = Course.model_validate(course)
    db.add(course_db)
    db.commit()
    db.refresh(course_db)
    return course_db

@app.get("/courses/", tags=["CRUD"], response_model=List[CourseResponse])
def read_courses(db: dbDep):
    return db.query(Course).all()

@app.get("/courses/{course_id}", tags=["CRUD"])
def read_course(course_id: int, db: dbDep):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course  

@app.put("/courses/{course_id}", tags=["CRUD"], response_model=CourseResponse)
def update_course(course_id: int, course: CourseCreate, db: dbDep):
    course_db = db.get(Course, course_id)
    if not course_db:
        raise HTTPException(status_code=404, detail="Course not found")
    course_db.title = course.title
    db.commit()
    db.refresh(course_db)
    return course_db

@app.delete("/courses/{course_id}", tags=["CRUD"])
def delete_course(course_id: int, db: dbDep):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    db.delete(course)
    db.commit()
    return {"ok": True}


class MarkCreate(BaseModel):
    course_id: int
    student_id: int
    mark: int

class MarkResponse(MarkCreate):
    id: int

@app.post("/marks/", tags=["CRUD"], response_model=MarkResponse)
def create_mark(mark: MarkCreate, db: dbDep):
    mark_db = Mark.model_validate(mark)
    db.add(mark_db)
    db.commit()
    db.refresh(mark_db)
    return mark_db

@app.get("/marks/", tags=["CRUD"], response_model=List[MarkResponse])
def read_marks(db: dbDep):
    return db.query(Mark).all()

@app.get("/marks/{mark_id}", tags=["CRUD"])
def read_mark(mark_id: int, db: dbDep):
    mark = db.get(Mark, mark_id)
    if not mark:
        raise HTTPException(status_code=404, detail="Mark not found")
    return mark  

@app.put("/marks/{mark_id}", tags=["CRUD"], response_model=MarkResponse)
def update_mark(mark_id: int, mark: MarkCreate, db: dbDep):
    mark_db = db.get(Mark, mark_id)
    if not mark_db:
        raise HTTPException(status_code=404, detail="Mark not found")
    mark_db.course_id = mark.course_id
    mark_db.student_id = mark.student_id
    mark_db.mark = mark.mark
    db.commit()
    db.refresh(mark_db)
    return mark_db

@app.delete("/marks/{mark_id}", tags=["CRUD"])
def delete_mark(mark_id: int, db: dbDep):
    mark = db.get(Mark, mark_id)
    if not mark:
        raise HTTPException(status_code=404, detail="Mark not found")
    db.delete(mark)
    db.commit()
    return {"ok": True}


class DegreeCreate(BaseModel):
    title: str

class DegreeResponse(DegreeCreate):
    id: int

@app.post("/degrees/", tags=["CRUD"], response_model=DegreeResponse)
def create_degree(degree: DegreeCreate, db: dbDep):
    degree_db = Degree.model_validate(degree)
    db.add(degree_db)
    db.commit()
    db.refresh(degree_db)
    return degree_db

@app.get("/degrees/", tags=["CRUD"], response_model=List[DegreeResponse])
def read_degrees(db: dbDep):
    return db.query(Degree).all()

@app.get("/degrees/{degree_id}", tags=["CRUD"])
def read_degree(degree_id: int, db: dbDep):
    degree = db.get(Degree, degree_id)
    if not degree:
        raise HTTPException(status_code=404, detail="Degree not found")
    return degree  

@app.put("/degrees/{degree_id}", tags=["CRUD"], response_model=DegreeResponse)
def update_degree(degree_id: int, degree: DegreeCreate, db: dbDep):
    degree_db = db.get(Degree, degree_id)
    if not degree_db:
        raise HTTPException(status_code=404, detail="Degree not found")
    degree_db.title = degree.title
    db.commit()
    db.refresh(degree_db)
    return degree_db

@app.delete("/degrees/{degree_id}", tags=["CRUD"])
def delete_degree(degree_id: int, db: dbDep):
    degree = db.get(Degree, degree_id)
    if not degree:
        raise HTTPException(status_code=404, detail="Degree not found")
    db.delete(degree)
    db.commit()
    return {"ok": True}


class PositionCreate(BaseModel):
    title: str

class PositionResponse(PositionCreate):
    id: int

@app.post("/positions/", tags=["CRUD"], response_model=PositionResponse)
def create_position(position: PositionCreate, db: dbDep):
    position_db = Position.model_validate(position)
    db.add(position_db)
    db.commit()
    db.refresh(position_db)
    return position_db

@app.get("/positions/", tags=["CRUD"], response_model=List[PositionResponse])
def read_positions(db: dbDep):
    return db.query(Position).all()

@app.get("/positions/{position_id}", tags=["CRUD"])
def read_position(position_id: int, db: dbDep):
    position = db.get(Position, position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position  

@app.put("/positions/{position_id}", tags=["CRUD"], response_model=PositionResponse)
def update_position(position_id: int, position: PositionCreate, db: dbDep):
    position_db = db.get(Position, position_id)
    if not position_db:
        raise HTTPException(status_code=404, detail="Position not found")
    position_db.title = position.title
    db.commit()
    db.refresh(position_db)
    return position_db

@app.delete("/positions/{position_id}", tags=["CRUD"])
def delete_position(position_id: int, db: dbDep):
    position = db.get(Position, position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    db.delete(position)
    db.commit()
    return {"ok": True}


class TeacherCreate(BaseModel):
    degree_id: int
    position_id: int
    name: str

class TeacherResponse(TeacherCreate):
    id: int

@app.post("/teachers/", tags=["CRUD"], response_model=TeacherResponse)
def create_teacher(teacher: PositionCreate, db: dbDep):
    teacher_db = Teacher.model_validate(teacher)
    db.add(teacher_db)
    db.commit()
    db.refresh(teacher_db)
    return teacher_db

@app.get("/teachers/", tags=["CRUD"], response_model=List[TeacherResponse])
def read_teachers(db: dbDep):
    return db.query(Teacher).all()

@app.get("/teachers/{teacher_id}", tags=["CRUD"])
def read_teacher(teacher_id: int, db: dbDep):
    teacher = db.get(Teacher, teacher_id)
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return teacher  

@app.put("/teachers/{teacher_id}", tags=["CRUD"], response_model=TeacherResponse)
def update_teacher(teacher_id: int, teacher: TeacherCreate, db: dbDep):
    teacher_db = db.get(Teacher, teacher_id)
    if not teacher_db:
        raise HTTPException(status_code=404, detail="Teacher not found")
    teacher_db.degree_id = teacher.degree_id
    teacher_db.position_id = teacher.position_id
    teacher_db.name = teacher.name
    db.commit()
    db.refresh(teacher_db)
    return teacher_db

@app.delete("/teachers/{teacher_id}", tags=["CRUD"])
def delete_teacher(teacher_id: int, db: dbDep):
    teacher = db.get(Teacher, teacher_id)
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    db.delete(teacher)
    db.commit()
    return {"ok": True}


class LessonCreate(BaseModel):
    group_id: int
    teacher_id: int
    course_id: int

class LessonResponse(LessonCreate):
    id: int

@app.post("/lessons/", tags=["CRUD"], response_model=LessonResponse)
def create_lesson(lesson: LessonCreate, db: dbDep):
    lesson_db = Lesson.model_validate(lesson)
    db.add(lesson_db)
    db.commit()
    db.refresh(lesson_db)
    return lesson_db

@app.get("/lessons/", tags=["CRUD"], response_model=List[LessonResponse])
def read_lessons(db: dbDep):
    return db.query(Lesson).all()

@app.get("/lessons/{lesson_id}", tags=["CRUD"])
def read_lesson(lesson_id: int, db: dbDep):
    lesson = db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson  

@app.put("/lessons/{lesson_id}", tags=["CRUD"], response_model=LessonResponse)
def update_lesson(lesson_id: int, lesson: LessonCreate, db: dbDep):
    lesson_db = db.get(Lesson, lesson_id)
    if not lesson_db:
        raise HTTPException(status_code=404, detail="Lesson not found")
    lesson_db.group_id = lesson.group_id
    lesson_db.teacher_id = lesson.teacher_id
    lesson_db.course_id = lesson.course_id
    db.commit()
    db.refresh(lesson_db)
    return lesson_db

@app.delete("/lessons/{lesson_id}", tags=["CRUD"])
def delete_lesson(lesson_id: int, db: dbDep):
    lesson = db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    db.delete(lesson)
    db.commit()
    return {"ok": True}
#-------------------------------------- JUST FOR CHILL --------------------------------------

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

class StudentAvgGrade(BaseModel):
    student_name: str
    average_grade: float
class ScheduleResponse(BaseModel):
    group_name: str
    course: str
    teacher: str
    lesson_time:str   

class TeacherCourseResponse(BaseModel):
    teacher: str
    course: str

class CuratorStudentsResponse(BaseModel):
    curator: str
    students: str
    stud_count: int

class TeacherInfoResponse(BaseModel):
    teacher: str
    degree: str

@app.get("/students/avg-grades/", response_model=List[StudentAvgGrade])
def get_students_avg_grades(db: Session = Depends(get_db)):
    
    
    result = db.query(
        Student.name.label("student_name"),
        func.round(func.avg(Mark.mark), 2).label("average_grade")
    ).join(
        Mark, Student.id == Mark.student_id
    ).group_by(
        Student.id
    ).all()
    

    return result

@app.get("/schedule/{group_id}",response_model=List[ScheduleResponse])
def schedule(group_id: int, db: Session = Depends(get_db)):
    # SELECT 
    # g.name_number AS group_name,
    # c.title AS course,
    # t.name AS teacher,
    # l.time AS lesson_time
    # FROM Lessons l
    # JOIN Groups g ON l.group_id = g.id
    # JOIN Courses c ON l.course_id = c.id
    # JOIN Teachers t ON l.teacher_id = t.id
    # WHERE g.id = 1 
    # ORDER BY l.time;
    result = db.query(
        Lesson.time.label("lesson_time"),
        Group.name_number.label("group_name"),
        Course.title.label("course"),
        Teacher.name.label("teacher"),
    ).join(
        Group, Lesson.group_id == Group.id
    ).join(
        Course, Lesson.course_id == Course.id
    ).join(
        Teacher, Lesson.teacher_id == Teacher.id
    ).where(
        Group.id == group_id
    ).order_by(Lesson.time).all()
    return result

@app.get("/teacher-load",response_model=List[TeacherCourseResponse])
def teacher_load(db: Session = Depends(get_db)):
    # SELECT DISTINCT
    # t.name AS teacher,
    # c.title AS course
    # FROM Teachers t
    # JOIN Lessons l ON t.id = l.teacher_id
    # JOIN Courses c ON l.course_id = c.id;

    result = db.query(
        Teacher.name.label("teacher"),
        Course.title.label("course"),
    ).join(
        Lesson, Teacher.id == Lesson.id
    ).join(
        Course, Lesson.course_id == Course.id
    ).all()
    return result

@app.get("/curator-load",response_model=List[CuratorStudentsResponse])
def curator_load(db: Session = Depends(get_db)):
    # SELECT 
    # c.name AS curator,
    # STRING_AGG(s.name, ', ') AS 'students',
    # COUNT(DISTINCT s.id) AS stud_count
    # FROM Curators c
    # JOIN `Groups` g ON c.id = g.curator_id
    # JOIN Students s ON g.id = s.group_id
    # GROUP BY c.name;

    result = db.query(
        Curator.name.label("curator"),
        func.aggregate_strings(Student.name, ", ").label("students"),
        func.count(distinct(Student.id)).label("stud_count"),
    ).join(
        Group, Curator.id == Group.curator_id
    ).join(
        Student, Group.id == Student.group_id
    ).group_by(
        Curator.name
    ).all()
    return result

@app.get("/teacher-info",response_model=List[TeacherInfoResponse])
def teacher_load(db: Session = Depends(get_db)):
    # SELECT
    # t.name AS teacher,
    # d.title AS degree,
    # p.title AS 'position'
    # FROM Degrees d
    # JOIN Teachers t ON d.id = t.degree_id
    # JOIN Positions p ON t.position_id = p.id;

    result = db.query(
        Degree.title.label("degree"),
        Teacher.name.label("teacher"),
        Position.title.label("position")
    ).join(
        Teacher, Degree.id == Teacher.degree_id
    ).join(
        Position, Teacher.position_id == Position.id
    ).all()
    return result

if __name__ == '__main__':
    uvicorn.run("main:app", reload=True)