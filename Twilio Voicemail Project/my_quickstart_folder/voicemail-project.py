'''
Project Briefing:-

Step 1: Sign up for a number through Twilio.com and record a voicemail with it.
Step 2: Write a program to download the voicemail in mp3 format and then upload it to the Amazon S3 bucket.
Step 3: Document a report of all the steps in the project and share the URL of the voicemail in the S3 bucket 
        along with the code as a result.

Submitted By: Kriti Gupta
'''
import requests
import sys
from requests import get
import boto3
import os
from twilio.rest import Client
from dotenv import load_dotenv
from credentials import account_sid, auth_token, aws_access_key_id, aws_access_key_secret, aws_bucket_name
from twilio.twiml.voice_response import VoiceResponse
from flask import Flask, request

#Starting the Flask server
app = Flask(__name__)

#Global variable for the url of mp3 file
recording_url = ''

#Webpage /answer is first loaded
@app.route("/answer", methods=['GET', 'POST'])
def answer_call():
    """
    Respond to incoming phone calls with a brief message.
    """
    # Start the TwiML response
    response = VoiceResponse()

    # Electronic voice is programmed to greet the user and ask them to leave a message
    response.say("Please leave a message after the beep. Press star when finished", voice='alice')

    # The voice main is being recorded and then the webpage is redirected to /end-call
    response.record(finishOnKey='*', action='/end_call')

    return str(response)

# This is to notify the user that their voicemail has been recorded and hanging up the call
@app.route("/end_call", methods=['GET', 'POST'])
def message():
    """
    Hang up the call once the recording is finished.
    """
    # Start the TwiML response
    response = VoiceResponse()

    # Electronic voice to end up the call with the user
    response.say("Thank you for calling. Have a nice day.", voice='alice')

    # Method to hang up the call in Twilio.com
    response.hangup()
    print('Voicemail recorded successfully...')

    # Generating a client object to access the recorded files from Twilio.com
    client = Client(account_sid, auth_token)

    # A list of recorded objects
    recordings = client.recordings.list()

    # Fetching the top most or the latest recorded voicemail from the recorded list
    latest_recording = recordings[0]
    
    # In order to download the voicemail in mp3 format the .json extention of uri needs to be replaced with .mp3
    mp3_file = latest_recording.uri.replace("json", "mp3")

    # A url is created from where the mp3 file can be downloaded
    recording_url = "https://api.twilio.com"+mp3_file
    
    # This function would download the mp3 file into the system
    mp3_file = retrieve_mp3_file(recording_url)
    print('mp3 File Downloaded...')

    print('Uploading File...')
    # The function will upload the downloaded file from the system to the AWS S3 bucket
    upload_file_to_s3(mp3_file)
    print('File uploaded successfully...')
    return(str(response))

def upload_file_to_s3(complete_file_path):
    """
    Uploads a file to AWS S3
    """

    # A session is created using Boto3 module in order to access the AWS S3 bucket
    session = boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_access_key_secret,
    )

    # S3 resource is assigned here
    s3 = session.resource('s3')

    # The mp3 file is opened
    data = open(os.path.normpath(complete_file_path), 'rb')

    # The name of the mp3 file is extracted
    file_basename = os.path.basename(complete_file_path)

    # The mp3 is uploaded to the AWS S3 bucket
    s3.Bucket(aws_bucket_name).put_object(Key=file_basename, Body=data)

def retrieve_mp3_file(mp3_link):
    '''
    Downloads a file from a url to the system
    '''
    # A name is assigned to the mp3 file
    # This would override a pre-existing recording and save space in the disk
    # Also, we would have the most recent voicemail with this technique
    # A programmar can rename the name variable to download the file with their desired naming convention
    name = 'voicemail-recording'
    file_name = str(name) + ".mp3"

    # A file if created in the system in which the mp3 file contents are written
    with open(file_name,'wb') as file:
        response = get(mp3_link)
        file.write(response.content)
    # Finally the path to this file is returned so that it can be used to upload the file to AWS S3 bucket.
    return "./" + name +".mp3"

# Driver Function
if __name__ == "__main__":
    app.run(debug=True)
