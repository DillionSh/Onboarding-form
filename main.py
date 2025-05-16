from flask import Flask, render_template, request, flash, send_from_directory, url_for, redirect
from dotenv import load_dotenv
import os
from simple_salesforce import Salesforce, SalesforceMalformedRequest
from flask_mail import Mail, Message
import datetime

from flask_bootstrap import Bootstrap5
import base64
from difflib import SequenceMatcher
import re
import pandas as pd


app = Flask(__name__)
bootstrap = Bootstrap5(app)
app.secret_key = "random_secret_key"

load_dotenv()
sf_username = os.getenv('SF_USERNAME')
sf_password = os.getenv('SF_PASSWORD')
sf_security_token = os.getenv('SF_SECURITY_TOKEN')



# Salesforce login
sf = Salesforce(
    username=os.getenv('SF_USERNAME'),
    password=os.getenv('SF_PASSWORD'),
    security_token= os.getenv('SF_SECURITY_TOKEN'),
    domain='test'
)

# def normalize_name(name):
#     # Convert to lowercase
#     name = name.lower()
#     # Remove extra spaces
#     name = re.sub(r'\s+', ' ', name).strip()
#     return name
#
#
# # Function to check if names are similar
# def are_names_similar(name1, name2, threshold=0.9):
#     if pd.isna(name1) or pd.isna(name2):
#         return True
#     name1_normalized = normalize_name(name1)
#     name2_normalized = normalize_name(name2)
#
#     # Check if one name contains the other
#     if name1_normalized in name2_normalized or name2_normalized in name1_normalized:
#         return True
#
#     # Use SequenceMatcher to get a similarity ratio
#     similarity_ratio = SequenceMatcher(None, name1_normalized, name2_normalized).ratio()
#
#     return similarity_ratio >= threshold

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/submit-form', methods=['POST'])
def submit_form():
    nric = request.form.get("nric")
    first_shirt = request.form.get('first_shirt')
    second_shirt = request.form.get('second_shirt')
    reason = request.form.get('others')

    # input_name = normalize_name(name)

    # Queries to get Internship and Contact records
    query_name = "SELECT Id, Name, Name__c FROM Internship__c"
    query_name_2 = "SELECT Id, Name,Client_NRIC__c FROM Contact"

    query_name_result = sf.query(query_name)
    query_name_result_2 = sf.query(query_name_2)

    best_match_contact_id = None
    best_match_internship_id = None

    if 'records' in query_name_result and 'records' in query_name_result_2:
        internship_records = query_name_result['records']
        contact_records = query_name_result_2['records']

        for contact in contact_records:
            contact_id = contact.get("Id")
            contact_name = contact.get("Name")
            contact_nric = contact.get("Client_NRIC__c")

            # normalized_contact_name = normalize_name(contact_name)
            # similarity_ratio = are_names_similar(normalized_contact_name, input_name, threshold=0.8)
            # print(f"Contact ID: {contact_id}, Contact Name: {contact_name}, Similarity: {similarity_ratio}")

            if nric == contact_nric:
                best_match_contact_id = contact_id
                best_match_contact_name = contact_name
                 # Stop after finding the best match (if required, adjust this logic)
                print(best_match_contact_name)
                print(best_match_contact_id)
        if best_match_contact_id:
            for internship in internship_records:
                internship_id = internship.get('Id')
                internship_name_c = internship.get('Name__c')
                print(internship_id)
                print(internship_name_c)

                if internship_name_c == best_match_contact_id:
                    best_match_internship_id = internship_id


    if best_match_internship_id:
        try:

            # Prepare data to update
            update_data = {
                'Start_Date__c': datetime.date.today().isoformat(),
                'Not_issued_reason__c': reason,

            }
            if first_shirt != 'Not Issued':
                update_data['Volunteer_T_Shirt_Status__c']= first_shirt
                update_data['Volunteer_T_Shirt_Issued_Date__c'] = datetime.date.today().isoformat()
            if second_shirt != 'Not Issued':
                update_data[ 'Volunteer_2nd_T_Shirt_Status__c']= second_shirt
                update_data['Volunteer_2nd_T_Shirt_Issued_Date__c'] = datetime.date.today().isoformat()

            # Update the record in Salesforce using the Internship record ID
            result = sf.Internship__c.update(best_match_internship_id, update_data)

            return render_template('success.html')
        except SalesforceMalformedRequest as e:

                error_content = e.content
                for error_dict in error_content:
                    error_message = error_dict.get('message')
                    if error_message:
                        flash(f"{error_message}")
                        return redirect(url_for('index'))

    else:
        flash("User not found, please ensure correct spelling of name")

        return render_template("index.html")


if __name__ == '__main__':
    app.run(debug=True)
