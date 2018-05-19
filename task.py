from datetime import datetime,timedelta
from time import strftime
import time
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from flask_mail import Mail, Message

app =Flask(__name__)
mail=Mail(app)

@app.route('/')
def index():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>Dashboard</title>
    <!--Import Google Icon Font-->
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <!-- Compiled and minified CSS -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/materialize/1.0.0-beta/css/materialize.min.css">

    <!-- Compiled and minified JavaScript -->
    <script src="https://code.jquery.com/jquery-3.3.1.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/materialize/1.0.0-beta/js/materialize.min.js"></script>
    <script src="https://cdn.onesignal.com/sdks/OneSignalSDK.js" async=""></script>
    <script>
    var OneSignal = window.OneSignal || [];
    OneSignal.push(function() {
        OneSignal.init({
        appId: "10b49cf0-9f1a-4dab-a272-2c0264225ce2",
        });
    });
    </script>
</head>
<body>
    <nav>
        <div class="nav-wrapper">
          <a href="#!" class="brand-logo"></a>
          <a href="#" data-target="mobile-demo" class="sidenav-trigger"><i class="material-icons">menu</i></a>
          <ul class="right hide-on-med-and-down">
            <li><a href="/">Home</a></li>
          </ul>
        </div>
      </nav>
    
      <ul class="sidenav" id="mobile-demo">
        <li><a href="/">Home</a></li>
      </ul>
</body>
<script>
    $( document ).ready(function(){
        $('.sidenav').sidenav();
    });
</script>
</html>"""

# mail configuration
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'mailmeonpunit@gmail.com'
app.config['MAIL_PASSWORD'] = '*************'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

def tick():
    basedir=os.path.abspath(os.path.dirname(__file__))
    sql_db = sqlite3.connect(basedir+'/assignment.db')
    sql_cursor = sql_db.cursor()
    currTime=str(strftime("%H:%M:%S",time.localtime(time.time()-300)))
    # to notify 5 minutes prior to class start
    sql_cursor.execute(
    "SELECT DISTINCT teacher.id,teacher.name,teacher.email,schedule.subject,schedule.classFrom,schedule.classTo FROM teacher LEFT JOIN schedule ON teacher.id=schedule.id where schedule.classFrom=?", (currTime,))
    data=[]
    for row in sql_cursor.fetchall():
        record={"id" : row[0],"name" : row[1],"email" : row[2],"subject" : row[3],"classFrom" : row[4],"classTo" : row[5]}
        data.append(record)
        for dataCount in range (0,len(data)):
            print(data[dataCount])
            with app.app_context():
                #mail code
                msg = Message('Hello', sender = 'mailmeonpunit@gmail.com', recipients = [data[dataCount]["email"]])
                msg.body = "Hello Mr. "+data[dataCount]["name"]+", Its time for the class of subject "+data[dataCount]["subject"]+" from "+data[dataCount]["classFrom"]+" to "+data[dataCount]["classTo"]+"."
                try:
                    mail.send(msg)
                except e:
                    print("Error: ",e)
                print("Sent")
    # to notify 5 minutes prior to class end
    sql_cursor.execute(
    "SELECT DISTINCT teacher.id,teacher.name,teacher.email,schedule.subject,schedule.classFrom,schedule.classTo FROM teacher LEFT JOIN schedule ON teacher.id=schedule.id where schedule.classTo=?", (currTime,))
    data=[]
    for row in sql_cursor.fetchall():
        record={"id" : row[0],"name" : row[1],"email" : row[2],"subject" : row[3],"classFrom" : row[4],"classTo" : row[5]}
        data.append(record)
        for dataCount in range (0,len(data)):
            print(data[dataCount])
            with app.app_context():
                #mail code
                msg = Message('Hello', sender = 'mailmeonpunit@gmail.com', recipients = [data[dataCount]["email"]])
                msg.body = "Hello Mr. "+data[dataCount]["name"]+", Its time to wrap up class as this class will end on: "+data[dataCount]["classTo"]+"."
                try:
                    mail.send(msg)
                except e:
                    print("Error: ",e)
                print("Sent")
    sql_db.commit()
    sql_cursor.close()
    sql_db.close()
    print('Tick! The time is:', strftime("%H:%M:%S",time.localtime(time.time()-300)))


if __name__ == '__main__':
    import sqlite3
    basedir=os.path.abspath(os.path.dirname(__file__))
    sql_db = sqlite3.connect(basedir+'/assignment.db')
    sql_cursor = sql_db.cursor()
    sql_cursor.execute(
    '''CREATE TABLE IF NOT EXISTS teacher(
       id INT PRIMARY KEY, name TEXT, email TEXT)''')
    sql_cursor.execute(
    '''CREATE TABLE IF NOT EXISTS schedule(
       id INT, subject TEXT, classFrom TIME,classTo TIME)''')
    sql_db.commit()
    sql_cursor.close()
    sql_db.close()
    scheduler = BackgroundScheduler()
    scheduler.add_job(tick, 'interval', seconds=1,max_instances=10)
    scheduler.start()
    print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

    try:
        # This is here to simulate application activity (which keeps the main thread alive).
        while True:
            time.sleep(1)
            app.run(debug=True)
    except (KeyboardInterrupt, SystemExit):
        # Not strictly necessary if daemonic mode is enabled but should be done if possible
        scheduler.shutdown()