import os
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

load_dotenv()

def send_email(subject, content):
    message = Mail(
        from_email="rpars27@gmail.com",
        to_emails="rpars27@gmail.com",
        subject=subject,
        plain_text_content=content,
    )

    sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
    response = sg.send(message)

    print("Email sent.")
    print(response.status_code)