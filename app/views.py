from app import app
from flask import jsonify, request
from flask_cors import CORS, cross_origin
import os

cors = CORS(app, resource={
    r"/*":{
        "origins":"http://127.0.0.1:3000"
    }
})
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route("/signup", methods=['POST'])
@cross_origin()
def signup():
    request_data = request.get_json()
    site_name = None
    business_mail = None
    phone = None
    password = None
    plan = None
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
        os.system('python script.py')
        return jsonify(message="you have successfully registered in our system")



