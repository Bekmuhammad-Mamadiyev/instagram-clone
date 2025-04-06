import re
import threading
from multiprocessing.connection import Client

from decouple import config
import phonenumbers
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from rest_framework.exceptions import ValidationError

email_regex = re.compile(r"[^@ \t\r\n]+@[^@ \t\r\n]+\.[^@ \t\r\n]+")
# phone_regex = re.compile(r"^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$")

def check_email_or_phone(email_or_phone):
    # phone_number = phonenumbers.parse(email_or_phone)
    if re.fullmatch(email_regex,email_or_phone):
        email_or_phone = "email"

    elif phonenumbers.is_valid_number(email_or_phone):
        email_or_phone = "phone"

    else:
        data = {
            "success":False,
            "message":"enter your email address or phone number"
        }
        raise ValidationError(data)

    return email_or_phone


class EmailThread(threading.Thread):
    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send()
        print(f"Sending email to {self.email}")



class Email:
    @staticmethod
    def send_email(data):
        email = EmailMessage(
            subject=data['subject'],
            body=data['body'],
            to=[data['to_email']]
        )
        if data.get('content_type') == "html":
            email.content_subtype ='html'
        EmailThread(email).start()

def send_email(email,code):
    html_content = (render_to_string
                    ('user_signup/email_send/code_email.html',
                                    {"code":code
                                    }))

    Email.send_email({
        "subject":"Ro'yhatdan o'tish",
        "to_email":email,
        "body":html_content,
        "content_type":"html"
    })
    # print(a)
    return


# def send_phone(phone,code):
#     account_sid = config('account_sid')
#     auth_token= config('auth_token')
#     client = Client(account_sid,auth_token)
#     client.messages.create(
#         body='code',
#         from_ = '',
#         to = 'phone'
#     )