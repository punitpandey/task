from datetime import datetime,timedelta
from time import strftime
import time
import os
from flask import Flask,request,jsonify
import requests
import json
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from flask_mail import Mail, Message

app =Flask(__name__)
mail=Mail(app)

@app.route('/registerNotification',methods=['POST'])
def registerNotify():
    if request.method=='POST':
        try:
            user=str(request.form['user'])
            notify_id=str(request.form["notify_id"])
            basedir=os.path.abspath(os.path.dirname(__file__))
            sql_db = sqlite3.connect(basedir+'/assignment.db')
            sql_cursor = sql_db.cursor()
            sql_cursor.execute(
            "SELECT id from teacher where name=?",(user,))
            teacher_data=sql_cursor.fetchall()
            teacher_id=str(teacher_data[0][0])#to parse value from tuple returned
            if(teacher_data):
                try:
                    sql_cursor.execute("UPDATE teacher set notify_id=? where id=?",(notify_id,teacher_id,))
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
    
    function getNotify(){
        let name=document.getElementById("name").value;
        // alert(name);
        // push notify
        OneSignal.push(function() {
            OneSignal.on('subscriptionChange', function(isSubscribed) {
                if (isSubscribed) {
                // The user is subscribed
                //   Either the user subscribed for the first time
                //   Or the user was subscribed -> unsubscribed -> subscribed
                OneSignal.getUserId( function(userId) {
                    $.ajax({
                        url:"/registerNotification",
                        type:"POST",
                        data:{
                            "user":document.getElementById("name").value,
                            "notify_id":userId
                        },
                        success:function(res){
                            //alert(res);
                            $('#notifyDiv').hide();
                            $('#activeDiv').show();
                        }
                    });
                    // Make a POST call to your server with the user ID
                });
                }
            });
            OneSignal.init({
            appId: "e9af5911-ad44-4157-bd6c-6cfabf2374de",
            autoRegister: false,
            notifyButton: {
                enable: true,
            },
            welcomeNotification: {
                "title": "Task",
                "message": "Thank You! You will be notified with the updates now.",
                // "url": "" /* Leave commented for the notification to not open a window on Chrome and Firefox (on Safari, it opens to your webpage) */
            }
            });
        });
    }
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
      <div class="container">
          <div id="notifyDiv" class="row">
            <div class="input-field col s12">
              <input value="punit" id="name" type="text" class="validate">
              <label class="active" for="name">Name</label>
            </div>
            <button class="btn waves-effect waves-light red lighten-2" type="submit" id="getAlert" name="action" onclick="getNotify()" name="action">Submit
                <i class="material-icons right">send</i>
              </button>
          </div>
          <div id="activeDiv" style="display: none;">
            <center><h3>Ready to receive Notifications.</h3></center>
          </div>
      </div>
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
app.config['MAIL_PASSWORD'] = 'stephenhawking'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

def tick():
    basedir=os.path.abspath(os.path.dirname(__file__))
    sql_db = sqlite3.connect(basedir+'/assignment.db')
    sql_cursor = sql_db.cursor()
    currTime=str(strftime("%H:%M:%S",time.localtime(time.time()+300)))
    # to notify 5 minutes prior to class start
    sql_cursor.execute(
    "SELECT DISTINCT teacher.id,teacher.name,teacher.email,teacher.notify_id,schedule.subject,schedule.classFrom,schedule.classTo FROM teacher LEFT JOIN schedule ON teacher.id=schedule.id where schedule.classFrom=?", (currTime,))
    data=[]
    for row in sql_cursor.fetchall():
        record={"id" : row[0],"name" : row[1],"email" : row[2],"notify_id":row[3],"subject" : row[4],"classFrom" : row[5],"classTo" : row[6]}
        data.append(record)
        for dataCount in range (0,len(data)):
            print(data[dataCount])
            with app.app_context():
                #mail code
                msg = Message('Hello', sender = 'mailmeonpunit@gmail.com', recipients = [data[dataCount]["email"]])
                msg.body = "Hello Mr. "+data[dataCount]["name"]+", Its time for the class of subject "+data[dataCount]["subject"]+" from "+data[dataCount]["classFrom"]+" to "+data[dataCount]["classTo"]+"."
                try:
                    mail.send(msg)
                except Exception as e:
                    print(e)
                print("Sent")
                # notification code
                header = {"Content-Type": "application/json; charset=utf-8","Authorization": "Basic OWIyYWUyZGEtODhiMS00M2EwLWFiNzItZTJkODI0YmRjYjMz"}

                payload = {"app_id": "e9af5911-ad44-4157-bd6c-6cfabf2374de","include_player_ids": [data[dataCount]["notify_id"]],"contents": {"en": msg.body}}
                    
                req = requests.post("https://onesignal.com/api/v1/notifications", headers=header, data=json.dumps(payload))
                print(req.status_code, req.reason)
    # to notify 5 minutes prior to class end
    sql_cursor.execute(
    "SELECT DISTINCT teacher.id,teacher.name,teacher.email,teacher.notify_id,schedule.subject,schedule.classFrom,schedule.classTo FROM teacher LEFT JOIN schedule ON teacher.id=schedule.id where schedule.classTo=?", (currTime,))
    data=[]
    for row in sql_cursor.fetchall():
        record={"id" : row[0],"name" : row[1],"email" : row[2],"notify_id":row[3],"subject" : row[4],"classFrom" : row[5],"classTo" : row[6]}
        data.append(record)
        for dataCount in range (0,len(data)):
            print(data[dataCount])
            with app.app_context():
                #mail code
                msg = Message('Hello', sender = 'mailmeonpunit@gmail.com', recipients = [data[dataCount]["email"]])
                msg.body = "Hello Mr. "+data[dataCount]["name"]+", Its time to wrap up class as this class will end on: "+data[dataCount]["classTo"]+"."
                try:
                    mail.send(msg)
                except Exception as e:
                    print(e)
                print("Sent")
                # notification code
                header = {"Content-Type": "application/json; charset=utf-8","Authorization": "Basic OWIyYWUyZGEtODhiMS00M2EwLWFiNzItZTJkODI0YmRjYjMz"}

                payload = {"app_id": "e9af5911-ad44-4157-bd6c-6cfabf2374de","include_player_ids": [data[dataCount]["notify_id"]],"contents": {"en": msg.body}}
                    
                req = requests.post("https://onesignal.com/api/v1/notifications", headers=header, data=json.dumps(payload))
                print(req.status_code, req.reason)
    sql_db.commit()
    sql_cursor.close()
    sql_db.close()
    print('The time is:', strftime("%H:%M:%S",time.localtime(time.time())))


if __name__ == '__main__':
    import sqlite3
    basedir=os.path.abspath(os.path.dirname(__file__))
    sql_db = sqlite3.connect(basedir+'/assignment.db')
    sql_cursor = sql_db.cursor()
    sql_cursor.execute(
    '''CREATE TABLE IF NOT EXISTS teacher(
       id INT PRIMARY KEY, name TEXT, email TEXT,notify_id TEXT)''')
    sql_cursor.execute(
    '''CREATE TABLE IF NOT EXISTS schedule(
       id INT, subject TEXT, classFrom TIME,classTo TIME)''')
    sql_db.commit()
    sql_cursor.close()
    sql_db.close()
    scheduler = BackgroundScheduler()
    scheduler.add_job(tick, 'interval', seconds=1,max_instances=10)
    scheduler.start()
    app.run(port = 5800,debug=True)
    print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

 
    try:
        # This is here to simulate application activity (which keeps the main thread alive).
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        # Not strictly necessary if daemonic mode is enabled but should be done if possible
        scheduler.shutdown()