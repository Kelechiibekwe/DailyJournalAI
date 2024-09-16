import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.openai_helper import generate_prompt
import imaplib
from email.utils import make_msgid
import email
from email.header import decode_header
from app.models import db, Prompts, Responses, User_Prompt


from config import Config

def send_journal_email(user_id):
    # Get user email and generate a prompt
    sender_email = Config.EMAIL_ADDRESS
    receiver_email = Config.EMAIL_ADDRESS  # Replace with user's email
    password = Config.EMAIL_PASSWORD

    # Generate the journal prompt
    prompt_text = generate_prompt()

    # Create the email message
    message = MIMEMultipart("alternative")
    message["Subject"] = "Your Daily Journal Prompt"
    message["From"] = sender_email
    message["To"] = receiver_email

    msg_id = make_msgid()  # Generate unique Message-ID
    message["Message-ID"] = msg_id

    html = f"""\
    <html>
      <body>
        <p>Hi,<br>
           It's time to journal! Here's your prompt for today:<br>
           <b>"{prompt_text}"</b><br>
           Keep up the great habit!
        </p>
      </body>
    </html>
    """
    part = MIMEText(html, "html")
    message.attach(part)

    # Send the email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())

    # Store the prompt in the database
    new_prompt = Prompts(user_id=user_id, prompt_text=prompt_text)
    db.session.add(new_prompt)
    db.session.commit()

    # Store the User_Prompt with the Message-ID
    user_prompt = User_Prompt(user_id=user_id, prompt_id=new_prompt.prompt_id, message_id=msg_id)
    db.session.add(user_prompt)
    db.session.commit()

    return msg_id



def check_for_reply(message_id):
    default_email = Config.EMAIL_ADDRESS  # Replace with user's email
    password = Config.EMAIL_PASSWORD
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(default_email, password)
    mail.select("inbox")

    # Search for emails with 'In-Reply-To' matching the original Message-ID
    status, messages = mail.search(None, f'HEADER In-Reply-To "{message_id}"')

    for msg_id in messages[0].split():
        status, msg_data = mail.fetch(msg_id, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else "utf-8")

                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode()
                            print(f"Subject: {subject}\nBody: {body}")

                            # Save the response in the Responses table
                            user_prompt = User_Prompt.query.filter_by(message_id=message_id).first()
                            if user_prompt:
                                response = Responses(user_id=user_prompt.user_id, prompt_id=user_prompt.prompt_id, response_text=body)
                                db.session.add(response)
                                db.session.commit()
                else:
                    body = msg.get_payload(decode=True).decode()
                    print(f"Subject: {subject}\nBody: {body}")

                    # Save the response in the Responses table
                    user_prompt = User_Prompt.query.filter_by(message_id=message_id).first()
                    if user_prompt:
                        response = Responses(user_id=user_prompt.user_id, prompt_id=user_prompt.prompt_id, response_text=body)
                        db.session.add(response)
                        db.session.commit()

    mail.logout()