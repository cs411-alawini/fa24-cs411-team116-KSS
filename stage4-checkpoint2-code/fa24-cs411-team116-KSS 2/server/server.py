from google.cloud.sql.connector import Connector
import sqlalchemy
import random

# Database configuration
INSTANCE_CONNECTION_NAME = "cs-411-project-440122:us-central1:group116-cs411"
DB_USER = "KSSJ"
DB_PASS = "KSSJ"
DB_NAME = "ClassoftheDay"

# Initialize the connector
connector = Connector()

# Function to connect securely
def get_connection():
    return connector.connect(
        INSTANCE_CONNECTION_NAME,
        "pymysql",
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME,
    )

# Use SQLAlchemy for connection pooling
pool = sqlalchemy.create_engine(
    "mysql+pymysql://",
    creator=get_connection,
)

query = sqlalchemy.text(
    "SELECT COUNT(*) FROM Courses",
)

# Query the database
conn = pool.connect()
# result = conn.execute(query).fetchall()
# for row in result:
#   print(row)

insert = sqlalchemy.text("INSERT INTO User (UserId, Email, EncryptedPassword, DateJoined) VALUES (:id, :email, :pw, :date)")

from datetime import datetime
from flask import Flask
from flask import request

app = Flask(__name__)

@app.after_request 
def after_request(response):
    header = response.headers
    header['Access-Control-Allow-Origin'] = '*'
    # Other headers can be added here if needed
    return response

def today():
  return datetime.today().strftime('%Y-%m-%d')

@app.route("/signup")
def signup():
    uid = request.args.get('username')
    email = request.args.get('email')
    password = request.args.get('password')
    try: 
      result = conn.execute(insert, parameters={"id": uid, "email": email, "pw": password, "date": today()})
      conn.commit()
    except:
      return "Duplicate detected, try a different username.", 400

    return "Signed up successfuly.", 200

login_query = sqlalchemy.text("SELECT UserId, Email, EncryptedPassword FROM User WHERE UserId = :uid AND EncryptedPassword = :pw")
@app.route("/login", methods=["GET", "POST"])
def login():
  uid = request.args.get('username')
  password = request.args.get('password')
  try: 
    result = conn.execute(login_query, parameters={"uid": uid, "pw": password})
    count = 0
    for row in result:
       count += 1
    if count != 1:
       return "Invalid credentials.", 400
  except:
    return "Error", 400

  return "Logged in successfuly.", 200

summarize = sqlalchemy.text("SELECT Description FROM CourseDescription WHERE CourseId = (SELECT Courses.CourseId FROM Courses WHERE Courses.DepartmentId = :dept AND Courses.Number = :num)")
def get_summary(dept, num):
  result = conn.execute(summarize, parameters={'dept': dept, 'num': num}).fetchone()
  if result == None:
    return "N/A"
  else:
    return result[0]

update = sqlalchemy.text("UPDATE User SET Email = :email WHERE UserId = :uid")
@app.route("/modify/email")
def modify_email():
  uid = request.args.get('username')
  email = request.args.get('email')
  try: 
    result = conn.execute(update, parameters={"uid": uid, "email": email})
    conn.commit()
  except:
    return "Error", 400

  return "Email updated successfuly.", 200

get_course_info = sqlalchemy.text("SELECT DepartmentId, Number, Name FROM Courses WHERE CourseId = :cid")
info_query = sqlalchemy.text("SELECT UserId, Email, DateJoined, MostGuessed FROM User WHERE UserId = :uid")
@app.route("/info")
def info():
  uid = request.args.get('username')
  try:
    result = conn.execute(info_query, parameters={"uid": uid}).fetchone()
    favorite = result[3]
    if favorite == None:
      favorite = 'None'
    else:
      favorite = conn.execute(get_course_info, parameters={'cid': favorite}).fetchone()
      favorite = f'{favorite[0]} {favorite[1]} {favorite[2]}'
    return {"UserId": result[0], "Email": result[1], "DateJoined": result[2], "MostGuessed": favorite}, 200
  except:
    return "Error", 400

delete_query = sqlalchemy.text("DELETE FROM User WHERE UserId = :uid AND EncryptedPassword = :pw;")
@app.route("/delete")
def delete():
  uid = request.args.get('username')
  password = request.args.get('password')
  try: 
    result = conn.execute(delete_query, parameters={"uid": uid, "pw": password})
    conn.commit()
    count = 0
  except:
    return "Error deleting account", 400

  return "Deleted account successfuly.", 200
#SELECT CourseId FROM Courses JOIN Departments ON Courses.DepartmentId = Departments.DepartmentId WHERE Departments.Name = 'CS' AND Courses.Number = 225
# get_crn = sqlalchemy.text("SELECT CourseId FROM Courses JOIN Departments ON Courses.DepartmentId = Departments.DepartmentId WHERE Departments.DepartmentId = :department AND Courses.Number = :number")
# guess_crn = sqlalchemy.text("INSERT INTO Guess Values (:gid, :uid, :date, :crn)")
# get_course_info = sqlalchemy.text("SELECT DepartmentId, Number, Name, Credits, GenEd FROM Courses WHERE CourseId = :cid")
get_correct_course = sqlalchemy.text("SELECT CorrectCourseId FROM DailyClass WHERE CurrentDate = :date")
random_course = sqlalchemy.text("SELECT CourseId FROM Courses ORDER BY RAND() LIMIT 1")
insert_correct = sqlalchemy.text("INSERT INTO DailyClass(CurrentDate, CorrectCourseId) VALUES (:date, :crn)")
make_guess = sqlalchemy.text("CALL MakeGuess(:uid, :dept, :num, :date);")
@app.route("/guess")
def guess():
  uid = request.args.get('username')
  department = request.args.get('department').upper()
  number = request.args.get('number')
  date = today()
  result = conn.execute(get_correct_course, parameters={"date": date}).fetchone()
  correct = None
  if result == None:
    result = conn.execute(random_course).fetchone()
    correct = result[0]
    result = conn.execute(insert_correct, parameters={"date": date, "crn": correct})
    conn.commit()
  else:
    correct = result[0]
  result = conn.execute(make_guess, parameters={"uid": uid, "dept": department, "num": number, "date": date})
  info = []
  for row in result:
    info.append(row)
  if len(info) < 2:
    print(info)
    return "Invalid guess", 400
  guessed_info = info[0]
  correct_info = info[1]
  ret = {"guess": 
         {"department": guessed_info[0], "number": guessed_info[1], "name": guessed_info[2], "credits": guessed_info[3], "genEd": guessed_info[4]},
         "values": {"department": "=" if guessed_info[0] == correct_info[0] else ">" if guessed_info[0] < correct_info[0] else "<", "number": ">" if guessed_info[1] < correct_info[1] else "<" if guessed_info[1] > correct_info[1] else "=",
                   "name": guessed_info[2] == correct_info[2], "credits": guessed_info[3] == correct_info[3], "genEd": guessed_info[4] == correct_info[4]},
         "summary": get_summary(department, number)
         }
  conn.commit()
  return ret, 200

app.run()

# Close the connector
connector.close()


