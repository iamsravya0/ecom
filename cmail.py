import smtplib
from smtplib import SMTP 
from email.message import EmailMessage  
def sendmail(to,subject,body):
    server=smtplib.SMTP_SSL('smtp.gmail.com',465)
    server.login('sravyasravya729@gmail.com','lfrb kodi scyh vnni')
    msg=EmailMessage()
    msg['FROM']='sravyasravya729@gmail.com'
    msg['SUBJECT']=subject
    msg['TO']=to
    msg.set_content(body)
    server.send_message(msg)
    server.quit()