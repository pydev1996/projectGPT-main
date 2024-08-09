from email.mime.text import MIMEText
import os
import time
from typing import List
from app import helperAI
import httpx
from app.config import settings
from app.mail_service import send_email_async
from app.schemas import Developer, ProjectRequirements, User,InputRequirements
from fastapi import APIRouter, Depends, HTTPException
from app.database import get_database
from app.deps import get_current_user
from difflib import SequenceMatcher
from motor.motor_asyncio import AsyncIOMotorCollection
from app.config import settings
import boto3
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from fastapi.security import OAuth2PasswordBearer
import requests
from dotenv import load_dotenv
load_dotenv()

client_router = APIRouter()

reuseable_oauth = OAuth2PasswordBearer(
    tokenUrl="/api/v1/login",
    scheme_name="JWT"
)
magic_pattern_token= os.getenv('MAGICPATTERN_KEY')

@client_router.post("/developer/getpromptresponse",)
async def get_promptresponse(input: InputRequirements, key: str = magic_pattern_token):
    try:
      headers = {
            "x-mp-api-key": str(key)
           
        }
      files = {
          'prompt': (None, input.prompt),
          'designSystem': (None, input.designSystem),
          'styling': (None, input.styling),
          'numberOfGenerations': (None, input.numberOfGenerations),
          'shouldAwaitGenerations': (None, input.shouldAwaitGenerations),
          
      }
      print(magic_pattern_token)
      response = requests.post('https://api.magicpatterns.com/api/pattern', headers=headers, files=files)
      

      print(response.status_code)
      return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@client_router.post("/developer/sendEmail",)
async def get_developer(input: ProjectRequirements, token: str = Depends(reuseable_oauth), user: User = Depends(get_current_user)):
    try:
        databaseSkills = await fetch_developer_skills()
        title, skills = await helperAI.extract_skills_from_paragraph(input.requirements, settings.EXTRACTSKILLS_ASSISTANT_ID)
        matched_skills = set()
        for skill in skills:
            for dbSkill in databaseSkills:        
                if SequenceMatcher(None, skill.lower(), dbSkill.lower()).ratio() >= 0.6:
                    matched_skills.add(dbSkill)
        skills.extend(list(matched_skills))
        payload = {
            "clientId": input.client_id,
            "skills": skills,
            "title": title,
            "description": input.requirements
        }
        response = await request_developers(token, payload)
        await helperAI.update_emailsend_for_conv(input.conv_id)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def create_email_for_dev(name, emailList, client_name, client_connect_link, pdf_url):
    email_title = f'New Project Requirement for {name} - OneHourDeveloper'
    recipient_email = emailList
    email_content  = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional //EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
  <!--[if gte mso 9]>
    <xml>
      <o:OfficeDocumentSettings>
        <o:AllowPNG />
        <o:PixelsPerInch>96</o:PixelsPerInch>
      </o:OfficeDocumentSettings>
    </xml>
  <![endif]-->
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="x-apple-disable-message-reformatting" />
  <!--[if !mso]><!-->
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <!--<![endif]-->
  <title>Newsletter</title>
  <style type="text/css">
    a, a[href], a:hover, a:link, a:visited {{
      text-decoration: none !important;
      color: #0000ee;
    }}
    .link {{
      text-decoration: underline !important;
    }}
    p, p:visited {{
      font-size: 15px;
      line-height: 24px;
      font-family: "Helvetica", Arial, sans-serif;
      font-weight: 300;
      text-decoration: none;
      color: #000000;
    }}
    h1 {{
      font-size: 22px;
      line-height: 24px;
      font-family: "Helvetica", Arial, sans-serif;
      font-weight: normal;
      text-decoration: none;
      color: #000000;
    }}
    .ExternalClass p, .ExternalClass span, .ExternalClass font, .ExternalClass td {{
      line-height: 100%;
    }}
    .ExternalClass {{
      width: 100%;
    }}
  </style>
</head>
<body style="text-align: center; margin: 0; padding-top: 10px; padding-bottom: 10px; padding-left: 0; padding-right: 0; -webkit-text-size-adjust: 100%; background-color: #f2f4f6; color: #000000;" align="center">
  <div style="text-align: center">
  
    <table align="center" style="text-align: center; vertical-align: top; width: 600px; max-width: 600px; background-color: #ffffff;" width="600">
      <tbody>
        <tr>
          <td style="width: 596px; vertical-align: top; padding-left: 30px; padding-right: 30px; padding-top: 30px; padding-bottom: 40px;" width="596">
            <h1 style="font-size: 20px; line-height: 24px; font-family: 'Helvetica', Arial, sans-serif; font-weight: 600; text-decoration: none; color: #000000;">
              Dear {name} You have Received a Software requirement
            </h1>
            <p style="font-size: 15px; line-height: 24px; font-family: 'Helvetica', Arial, sans-serif; font-weight: 400; text-decoration: none; color: #919293;">
              {client_name} has requested you for quotation <a target="_blank" style="text-decoration: underline; color: #000000" href="{pdf_url}" download="SoftwareRequirement"><u>(See attached PDF)</u></a>
            </p>
            <a href="{client_connect_link}" target="_blank" style="background-color: #000000; font-size: 15px; line-height: 22px; font-family: 'Helvetica', Arial, sans-serif; font-weight: normal; text-decoration: none; padding: 12px 15px; color: #ffffff; border-radius: 5px; display: inline-block; mso-padding-alt: 0;">
              <span style="mso-text-raise: 15pt; color: #ffffff">Speak to client</span>
            </a>
          </td>
        </tr>
      </tbody>
    </table>

    <table align="center" style="text-align: center; vertical-align: top; width: 600px; max-width: 600px; background-color: #000000;" width="600">
      <tbody>
        <tr>
          <td style="width: 596px; vertical-align: top; padding-left: 30px; padding-right: 30px; padding-top: 30px; padding-bottom: 30px;" width="596">
            <img style="width: 180px; max-width: 180px; height: 85px; max-height: 85px; text-align: center; color: #ffffff;" alt="Logo" src="https://app.1hourdeveloper.com/images/logo-new.png" align="center" width="180" height="85" />
            <p style="font-size: 13px; line-height: 24px; font-family: 'Helvetica', Arial, sans-serif; font-weight: 400; text-decoration: none; color: #ffffff;">
              421 Tuscany dr, Centerton, Arkansas 72719, USA.
            </p>
            <p style="margin-bottom: 0; font-size: 13px; line-height: 24px; font-family: 'Helvetica', Arial, sans-serif; font-weight: 400; text-decoration: none; color: #ffffff;">
              <a target="_blank" style="text-decoration: underline; color: #ffffff" href="https://www.1hourdeveloper.com/">1hourDeveloper</a>
            </p>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</body>
</html>
"""
        # Format the email body with dynamic content
    email_body = email_content.format(name= name, client_name=client_name, client_connect_link= client_connect_link, pdf_url=pdf_url)
    return email_title,recipient_email,email_body

async def fetch_developer_skills():
    db = get_database()
    developersDB: AsyncIOMotorCollection = db['skills']
    developer_skills = await developersDB.find({"approved":True}, {"skill": 1}).to_list(length=None)
    developer_skills = [skill["skill"] for skill in developer_skills]
    return developer_skills

async def generate_pdf(text_input, file_path):
    doc = SimpleDocTemplate(file_path, pagesize=letter)
    styles = getSampleStyleSheet()
    content = [Paragraph(text_input, styles["Normal"])]
    doc.build(content)


async def upload_to_s3(file_path, bucket_name, file_name, aws_access_key_id, aws_secret_access_key):
    s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
    try:

        s3.upload_file(file_path, bucket_name, file_name)
        print
        # Delete the file from local filesystem after successful upload
        os.remove(file_path)
        s3_file_path = f"https://dev-1hourgpt.s3.us-east-2.amazonaws.com/{file_name}"
        print("S3 file path:", s3_file_path)
        print("File successfully uploaded to S3 and deleted from local filesystem.")
        return s3_file_path

    except Exception as e:
        # Handle upload error
        print(f"Error uploading file to S3: {e}")
        # Optionally, you can also delete the file from local filesystem in case of error
        os.remove(file_path)
        return None

async def request_developers(token, data):
    url = "https://app.dev.1hourdeveloper.com/api/gptService/requestDevelopers"
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }
    payload = {
        "clientId": data['clientId'],
        "skills": data['skills'],
        "title": data['title'],
        "description": data['description']
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return response.json()
    