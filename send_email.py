import os.path
import base64
import html

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def markdown_to_basic_html(text):
    escaped = html.escape(text)

    escaped = escaped.replace("\n", "<br>")

    escaped = escaped.replace("### ", "<h3>")
    escaped = escaped.replace("**", "<strong>")

    return escaped


def build_html_email(body):
    body_html = markdown_to_basic_html(body)

    return f"""
<html>
  <body style="margin:0; padding:0; background-color:#f6f7f9; font-family:Arial, sans-serif; color:#111827;">
    <div style="max-width:900px; margin:0 auto; padding:32px;">
      <div style="background-color:#ffffff; border-radius:14px; padding:32px; border:1px solid #e5e7eb;">
        <div style="border-bottom:1px solid #e5e7eb; padding-bottom:16px; margin-bottom:24px;">
          <h1 style="margin:0; font-size:24px; color:#111827;">
            Morning Intelligence Brief
          </h1>
          <p style="margin:8px 0 0 0; color:#6b7280; font-size:14px;">
            AI-Enabled Services • Roll-Ups • Operational Transformation
          </p>
        </div>

        <div style="font-size:14px; line-height:1.6;">
          {body_html}
        </div>

        <div style="border-top:1px solid #e5e7eb; margin-top:32px; padding-top:16px; color:#6b7280; font-size:12px;">
          Generated automatically by Deal Intel Agent.
        </div>
      </div>
    </div>
  </body>
</html>
"""


def send_email(subject, body, to_email):
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file(
            "token.json",
            SCOPES
        )

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json",
                SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    service = build("gmail", "v1", credentials=creds)

    message = MIMEMultipart("alternative")
    message["to"] = to_email
    message["subject"] = subject

    plain_part = MIMEText(body, "plain")
    html_part = MIMEText(build_html_email(body), "html")

    message.attach(plain_part)
    message.attach(html_part)

    raw_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    service.users().messages().send(
        userId="me",
        body={"raw": raw_message}
    ).execute()

    print("Email sent successfully.")