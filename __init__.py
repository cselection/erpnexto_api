import os, sys
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
import pexpect
import random
import string
import json
import mariadb
import base64

app = Flask(__name__)
cors = CORS(app, resource={
    r"/*":{
        "origins":"http://127.0.0.1:3000"
    }
})
db_config = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': 'root',
    'database': 'erpnexto'
}
DEVELOPER_UPLOAD_FOLDER = os.getcwd()+'/uploads/developers'
IMPLEMENTER_UPLOAD_FOLDER = os.getcwd()+'/uploads/implementers'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app.config['CORS_HEADERS'] = 'Content-Type'
app.config['DEVELOPER_UPLOAD_FOLDER'] = DEVELOPER_UPLOAD_FOLDER
app.config['IMPLEMENTER_UPLOAD_FOLDER'] = IMPLEMENTER_UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'mbendary577@gmail.com'
app.config['MAIL_PASSWORD'] = 'MohamedBendary@577'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_ASCII_ATTACHMENTS'] = True   
mail = Mail(app)

## COMMAND TO RUN THE APP : python -m flask run / flask run
@app.route("/")
@cross_origin()
def erpnexto():
    return "<h2>hello erpnexto</h2>"

@app.route("/signup", methods=['POST'])
@cross_origin()
def signup():
    #accept request data
    request_data = request.get_json()
    company_name=None
    site_name = None
    email = None
    phone = None
    role = 'manager'
    plan = 'free'
    if request_data:
        if 'company_name' in request_data:
            company_name = request_data['company_name']
        if 'site_name' in request_data:
            site_name = request_data['site_name']
        if 'email' in request_data:
            email = request_data['email']
        if 'phone' in request_data:
            phone = request_data['phone']
        if 'plan' in request_data['plan']:
            plan = request_data['plan']
    confirmation_code = generate_confirmation_random_code()
    #add data to database
    try:
        connection = mariadb.connect(**db_config)
        cursor = connection.cursor()
        sql="insert into users(company_name, email, phone, role, plan, confirmation_code) values('{}','{}','{}','{}','{}','{}')".format(company_name, email, phone, role, plan, confirmation_code) 
        cursor.execute(sql)
        connection.commit()
    except Exception as e: 
        print('DB EXCEPTION =========================================== '+ str(e))
    #add data to mautic
    #send confirmation mail with code
    try:
        msg = Message("ERPNexto Installation Confirm", sender = 'mbendary577@gmail.com', recipients = ['mohamedyossif577@gmail.com'])
        msg.body = "please use this code "+confirmation_code+" to confirm your erpnexto installation"
        mail.send(msg)
    except Exception as e:
       print('MAIL EXCEPTION =========================================== '+ str(e))
    return {"message": "you have successfully registered in our system"}, 200

@app.route("/check-confirmation-code", methods=['POST'])
@cross_origin()
def check_confirmation_code():
    request_data = request.get_json()
    code = None
    email = None
    if request_data:
        if 'code' in request_data:
            code = request_data['code']
        if 'email' in request_data:
            email = request_data['email']
            print("email is " + email)
        #fetch user by mail and get code
        try:       
            connection = mariadb.connect(**db_config)
            cursor = connection.cursor()
            sql="select confirmation_code from users where email = '"+email+"'"
            print(sql)
            cursor.execute(sql)
            rows = cursor.fetchall()
            for row in rows:
                if code == row[0]:
                    #set confirmation code to user as null
                    return {"message": "confirmation code is valid"}, 200
            return {"message": "confirmation code is not valid"}, 400
        except Exception as e:
            print('DB EXCEPTION =========================================== '+ str(e))
    return {"message": "please submit confirmation code"}, 422

@app.route("/install-erpnexto", methods=['POST'])
@cross_origin()
def install_erpnexto():
    os.chdir("/var/www/ErpnextoApp/")
    file_path = "/home/cselection"
    my_file = os.path.join(file_path, "file.txt")
    f = open(my_file, "w") 
    f.write(os.getcwd())
    request_data = request.get_json()
    site_name = None
    email = None
    password = None
    plan = 'free'
    if request_data:
        if 'site_name' in request_data:
            site_name = request_data['site_name']
        if 'email' in request_data:
            email = request_data['email']
        if 'password' in request_data:
            password = request_data['password']
        if 'plan' in request_data['plan']:
            plan = request_data['plan']
        os.system('python script.py '+site_name+" "+email+" "+password+" "+plan)
        return jsonify(message="you have successfully registered in our system")

@app.route("/send-quote", methods=['POST'])
@cross_origin()
def processCustomizationPlanQuote():
    request_data = request.get_json()
    companyName = None
    email = None
    phone = None
    if request_data:
        if 'email' in request_data: 
            email = request_data['email']
        if 'phone' in request_data: 
            phone = request_data['phone']
        if 'companyName' in request_data:
            companyName = request_data['companyName']
        #send a notification mail that a client requested a quote
        try:
            msg = Message("ERPNexto Customization Plan Quote Request", sender = 'mbendary577@gmail.com', recipients = ['mohamedyossif577@gmail.com'])
            msg.body = "a new customer has sent a quote request for ERPnexto custmomization plan "\
                       "company name : "+companyName+" "\
                       "email : "+email+" "\
                       "phone : "+phone+" "
            mail.send(msg)
        except Exception as e:
            print('MAIL EXCEPTION =========================================== '+ str(e))
        return {"message": "your quote has been sent successfully, you will receive a mail from us as soon as possible"}, 200


@app.route("/developer-CV", methods=['POST'])
@cross_origin()
def precessDeveloperCV():
        if 'developer_cv' not in request.files:
            return {"message": "no files selected"}, 400
        file_data = request.files['developer_cv']
        if file_data.filename == '':
            return {"message": "no files selected"}, 400
        if file_data and allowed_file(file_data.filename):
            filename = secure_filename(file_data.filename)
            file_path = os.path.join(app.config['DEVELOPER_UPLOAD_FOLDER'], filename)
            file_data.save(file_path)
            #send developer resume in mail to recruiters
            try:
                developer_cv = app.config['DEVELOPER_UPLOAD_FOLDER']+'/'+filename
                msg = Message("ERPNexto Technical Partnership Request", sender = 'mbendary577@gmail.com', recipients = ['mohamedyossif577@gmail.com'])
                msg.body = "a new developer requested ERPNexto technical partnership"
                with app.open_resource(file_path) as cv_file:
                    msg.attach(developer_cv, "text/plain", cv_file.read())
                mail.send(msg)
            except Exception as e:
                print('MAIL EXCEPTION =========================================== '+ str(e))
            return {"message": "your resume was sent successfully, we will contact you soon"}, 200
        else:
            return {"message": "Allowed file types are txt, pdf, png, jpg"}, 400


@app.route("/implementer-CV", methods=['POST'])
@cross_origin()
def processImplementerCV():
    # get implementer personal data
    name = request.args.get('name')
    companyName = request.args.get('companyName')
    email = request.args.get('email')
    if 'implementer_cv' not in request.files:
        return {"message": "no files selected"}, 400
    file_data = request.files['implementer_cv']
    if file_data == None:
        return {"message": "no files selected"}, 400 
    if file_data.filename == '':
        return {"message": "no files selected"}, 400
    if file_data and allowed_file(file_data.filename):
        filename = secure_filename(file_data.filename)
        file_path = os.path.join(app.config['IMPLEMENTER_UPLOAD_FOLDER'], filename)
        file_data.save(file_path)
        #send implementer resume in mail to recruiters
        try:
            implementer_cv = app.config['IMPLEMENTER_UPLOAD_FOLDER']+'/'+filename
            msg = Message("ERPNexto Implementation Partnership Request", sender = 'mbendary577@gmail.com', recipients = ['mohamedyossif577@gmail.com'])
            msg.body = "a new request for ERPNexto implementation partnership, name : "+name+" company : "+companyName+" email : "+email+""
            with app.open_resource(file_path) as cv_file:
                msg.attach(implementer_cv, "text/plain", cv_file.read())
            mail.send(msg)
        except Exception as e:
            print('MAIL EXCEPTION =========================================== '+ str(e))
        return {"message": "your resume was sent successfully, we will contact you soon"}, 200


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_confirmation_random_code():
    letters = string.digits
    code = ''.join(random.choice(letters) for i in range(4)) 
    return code
