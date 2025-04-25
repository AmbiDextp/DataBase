import sqlite3

con = sqlite3.connect("University.db")
cur = con.cursor()

for i in range(1000000):
    cur.execute("INSERT INTO Marks (course_id, student_id, mark) VALUES (ABS(RANDOM()) % 7 + 1, ABS(RANDOM()) % 315 + 1, ABS(RANDOM()) % 4 + 2);")
con.commit()