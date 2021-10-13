import os, sys
from flask import Flask
from flask import jsonify, request
from flask_cors import CORS, cross_origin
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
import pexpect

app = Flask(__name__)
cors = CORS(app, resource={
    r"/*":{
        "origins":"http://127.0.0.1:3000"
    }
})
app.config['CORS_HEADERS'] = 'Content-Type'

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
#if os.path.exists(filename):
UPLOAD_FOLDER = '/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


'''app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'mohamedyossif577@gmail.com'
app.config['MAIL_PASSWORD'] = 'hammadmohamed577'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True'''

app.config['MAIL_SERVER']='smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = 'd223e3f997f1fa'
app.config['MAIL_PASSWORD'] = 'ac5e70df019193'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail= Mail(app)

## COMMAND TO RUN THE APP : python -m flask run / flask run

@app.route("/signup", methods=['POST'])
@cross_origin()
def signup():
    file_path = "/home/cselection"
    my_file = os.path.join(file_path, "file.txt")
    f = open(my_file, "w") 
    f.write(os.getcwd())
    request_data = request.get_json()
    site_name = None
    business_mail = None
    phone = None
    password = None
    plan = 'free'
    if request_data:
        if 'site_name' in request_data:
            site_name = request_data['site_name']
        if 'business_mail' in request_data:
            business_mail = request_data['business_mail']
        if 'phone' in request_data:
            phone = request_data['phone']
        if 'password' in request_data:
            password = request_data['password']
        if 'plan' in request_data['plan']:
            plan = request_data['plan']
        sys.path.append('/var/www/ErpnextoApp/ErpnextoApp')
        os.system('python script.py '+site_name+" "+business_mail+" "+phone+" "+password+" "+plan)
        return jsonify(message="you have successfully registered in our system")

'''
@app.route("/send-quote", methods=['POST'])
@cross_origin()
def processCustomizationPlanQuote():
    request_data = request.get_json()
    email = None
    phone = None
    companyName = None
    if request_data:
	    if 'email' in request_data:
            email = request_data['email']
        if 'phone' in request_data: 
            phone = request_data['phone']
        if 'companyName' in request_data:
            companyName = request_data['companyName']
        msg = Message('a new customer has requested an ERPNexto customization plan quote... customer mail is '+email+' customer phone is '+ph>
        msg.body = "new erpnexto customization plan quote request"
        mail.send(msg)
        return jsonify(message="you have send the mail successfully")
'''

@app.route("/developer-CV", methods=['POST'])
@cross_origin()
def precessDeveloperCV():
        if 'developer_cv' not in request.files:
            return jsonify({"response": "no files selected"})
        file = request.files['developer_cv']
        if file.filename == '':
            return jsonify({"response": "no files selected"})
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return jsonify({"response": "success"})
'''
@app.route("/implementer-CV", methods=['POST'])
@cross_origin()
def processImplementerCV():
        # get implementer personal data
        request_data = request.get_json()
        name = None
        company_name = None
	    email = None
        if request_data:
            if 'name' in request_data:
                name = request_data['name']
            if 'companyName' in request_data:
                company_name = request_data['companyName']
            if 'email' in request_data:
                email = request_data['email']
        # get implementer cv file
        if 'implementer-cv' not in request.files:
            return jsonify({"response": "no files selected"})
        file = request.files['developer_cv']
        if file.filename == '':
            return jsonify({"response": "no files selected"})
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return jsonify({"response": "success"})


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
'''

if __name__ == "__main__":
    app.run()
