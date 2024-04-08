import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from bs4 import BeautifulSoup
import sqlite3
import smtplib
from email.mime.text import MIMEText
from threading import Thread
import time

# Email settings
SMTP_SERVER = 'smtp.gmail.com'  
SMTP_PORT = 587  
SMTP_USERNAME = 'uwocoursenotifier@gmail.com'  
SMTP_PASSWORD = 'caom mczc amwy jwve'  
LOGIN_URL = 'https://draftmyschedule.uwo.ca/login.cfm?'  

DATABASE = 'class_subscribers.db'

app = Flask(__name__)
CORS(app)

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS subscribers (
                email TEXT NOT NULL,
                class_number TEXT NOT NULL
            )
        ''')
        conn.commit()

def send_email_notification(email, class_number):
    message = MIMEText(f'Class {class_number} has an open spot. Enroll now!')
    message['Subject'] = f'Class {class_number} Availability Notification'
    message['From'] = SMTP_USERNAME
    message['To'] = email

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(message)

def check_class_availability(session, headers):
    while True:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute('SELECT email, class_number FROM subscribers')
            subscriptions = c.fetchall()

        for email, class_number in subscriptions:
            response = session.get('https://draftmyschedule.uwo.ca/secure/summer_builder.cfm', headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            table = soup.find('table', {'class': 'table table-condensed table-hover'})
            if table:
                rows = table.find_all('tr')[1:]  
                for row in rows:
                    cells = row.find_all('td')
                    if class_number in cells[1].text.strip():
                        status = cells[7].text.strip()  # Status is in the 8th column
                    if status.lower() == 'not full':
                        send_email_notification(email, class_number)
                               
        time.sleep(300)  # Check every five minutes


@app.route('/subscribe', methods=['POST'])
def subscribe():
    data = request.json
    email = data['email']
    class_number = data['classNumber']
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('INSERT INTO subscribers (email, class_number) VALUES (?, ?)', (email, class_number))
        conn.commit()
    return jsonify({'status': 'success'}), 200

def log_in(session):
    session.cookies.set('CFID', '736869')
    session.cookies.set('CFTOKEN', '1c899509ac144be2%2DA87F1317%2DB1F7%2D1D69%2DD37AA0E35809AB64')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': 'https://draftmyschedule.uwo.ca/login.cfm',
        'Origin': 'https://draftmyschedule.uwo.ca'
    }

    
    return headers

if __name__ == '__main__':
    init_db()

    with requests.Session() as session: 
        headers = log_in( session)

        Thread(target=check_class_availability, args=(session, headers)).start()

        app.run(debug=True)