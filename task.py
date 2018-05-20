from datetime import datetime,timedelta
from flask import Flask,request,jsonify,render_template
from time import strftime
import time
import os
import requests
import json
import sqlite3
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from flask_mail import Mail, Message

basedir=os.path.abspath(os.path.dirname(__file__))

def send_push_notification(target,notification_msg):
    """to send push notification to specific target"""
    header = {
                "Content-Type": "application/json; charset=utf-8",
                "Authorization": "Basic OWIyYWUyZGEtODhiMS00M2EwLWFiNzItZTJkODI0YmRjYjMz"
            }
    payload = {
                "app_id": "e9af5911-ad44-4157-bd6c-6cfabf2374de",
                "include_player_ids": target,
                "contents": {"en": notification_msg}
            } 
    req = requests.post(
                            "https://onesignal.com/api/v1/notifications",
                            headers=header,
                            data=json.dumps(payload)
                        )
    print(req.status_code, req.reason)

app =Flask(__name__)
@app.route('/registerNotification',methods=['POST'])
def registerNotify():
    """to register user for push notification"""
    if request.method=='POST':
        try:
            user=str(request.form['user'])
            notify_id=str(request.form["notify_id"])
            sql_db = sqlite3.connect(basedir+'/assignment.db')
            sql_cursor = sql_db.cursor()
            sql_cursor.execute(
            "SELECT id from teacher where name=?",(user,))
            teacher_data=sql_cursor.fetchall()
            teacher_id=str(teacher_data[0][0])#to parse value from tuple returned
            if(teacher_data):
                try:
                    sql_cursor.execute("UPDATE teacher set notify_id=? where id=?",
                                        (notify_id,teacher_id,))
                except Exception as e:
                    return str(e)
            else:
                return("No user found.")
            sql_db.commit()
            sql_cursor.close()
            sql_db.close()
        except Exception as e:
            return(str(e))
        return ("User Registered for notification.")

@app.route('/')
def index():
    return render_template('index.html')

# mail configuration
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'mailmeonpunit@gmail.com'
app.config['MAIL_PASSWORD'] = 'stephen@123'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

def task():
    """task to be checked repeatedly in order to fetch teacher's schedule and notify"""
    sql_db = sqlite3.connect(basedir+'/assignment.db')
    sql_cursor = sql_db.cursor()
    currTime=str(strftime("%H:%M:%S",time.localtime(time.time()+300)))
    # to notify 5 minutes prior to class start
    sql_cursor.execute(
                            "SELECT DISTINCT teacher.id,teacher.name,teacher.email,\
                            teacher.notify_id,schedule.subject,schedule.classFrom,\
                            schedule.classTo FROM teacher LEFT JOIN schedule ON \
                            teacher.id=schedule.id where schedule.classFrom=?", 
                            (currTime,)
                        )
    data=[]
    for row in sql_cursor.fetchall():
        record={
                    "id" : row[0],
                    "name" : row[1],
                    "email" : row[2],
                    "notify_id":row[3],
                    "subject" : row[4],
                    "classFrom" : row[5],
                    "classTo" : row[6]
                }
        data.append(record)
        for dataCount in range (0,len(data)):
            print(data[dataCount])
            with app.app_context():
                #mail code
                msg = Message(
                                'Class schedule alert', 
                                sender = 'mailmeonpunit@gmail.com', 
                                recipients = [data[dataCount]["email"]]
                            )
                msg.body = "Hello Mr. "\
                            +data[dataCount]["name"]\
                            +", Its time for the class of subject "\
                            +data[dataCount]["subject"]\
                            +" from "+data[dataCount]["classFrom"]\
                            +" to "+data[dataCount]["classTo"]+"."
                try:
                    mail.send(msg)
                except Exception as e:
                    print(e)
                print("Sent")
                # notification code
                send_push_notification([data[dataCount]["notify_id"]],msg.body)
                
    # to notify 5 minutes prior to class end
    sql_cursor.execute(
                            "SELECT DISTINCT teacher.id,teacher.name,teacher.email,\
                            teacher.notify_id,schedule.subject,schedule.classFrom,\
                            schedule.classTo FROM teacher LEFT JOIN schedule ON \
                            teacher.id=schedule.id where schedule.classTo=?", 
                            (currTime,)
                       )
    data=[]
    for row in sql_cursor.fetchall():
        record={
                    "id" : row[0],
                    "name" : row[1],
                    "email" : row[2],
                    "notify_id":row[3],
                    "subject" : row[4],
                    "classFrom" : row[5],
                    "classTo" : row[6]
                }
        data.append(record)
        for dataCount in range (0,len(data)):
            print(data[dataCount])
            with app.app_context():
                #mail code
                msg = Message(
                                'Class schedule alert', 
                                sender = 'mailmeonpunit@gmail.com', 
                                recipients = [data[dataCount]["email"]]
                             )
                msg.body = "Hello Mr. "\
                            +data[dataCount]["name"]\
                            +", Its time to wrap up class as this class will end on: "\
                            +data[dataCount]["classTo"]+"."
                try:
                    mail.send(msg)
                except Exception as e:
                    print(e)
                print("Sent")
                # notification code
                send_push_notification([data[dataCount]["notify_id"]],msg.body)
                
    sql_db.commit()
    sql_cursor.close()
    sql_db.close()
    print('The time is:', strftime("%H:%M:%S",time.localtime(time.time())))


if __name__ == '__main__':
    sql_db = sqlite3.connect(basedir+'/assignment.db')
    sql_cursor = sql_db.cursor()
    sql_cursor.execute(
                        '''CREATE TABLE IF NOT EXISTS teacher(
                        id INT PRIMARY KEY, name TEXT, email TEXT,notify_id TEXT)'''
                    )
    sql_cursor.execute(
                        '''CREATE TABLE IF NOT EXISTS schedule(
                        id INT, subject TEXT, classFrom TIME,classTo TIME)'''
                        )
    sql_db.commit()
    sql_cursor.close()
    sql_db.close()
    scheduler = BackgroundScheduler()
    scheduler.add_job(task, 'interval', seconds=1,max_instances=10)
    scheduler.start()
    app.run()
    print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

 
    try:
        # This is here to simulate application activity (which keeps the main thread alive).
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        # Not strictly necessary if daemonic mode is enabled but should be done if possible
        scheduler.shutdown()