import json
import smtplib
import time
from datetime import date, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import schedule as schedule

from media.coin_telegraph import CoinTelegraph

USER = "thomas.bouamoud@gmail.com"
SENDER = "Crypto Newsletter"
TO = ["thomasbs17@yahoo.fr"]
with open("credentials.json") as credentials_file:
    credentials = json.loads(credentials_file.read())
start_date = date.today() - timedelta(days=1)
end_date = date.today() - timedelta(days=8)


def prepare_email_content() -> str:
    scraper = CoinTelegraph(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    most_viewed_articles, most_shared_articles = scraper.top_articles(top=10)
    content = f"<h1>Most viewed articles</h1>:<br>{most_viewed_articles.to_html()}<br><br><h1>Most shared articles</h1>:{most_shared_articles.to_html()} "
    return content


def send_email():
    msg = MIMEMultipart()
    msg["Subject"] = f"{date.today()} newsletter"
    msg["From"] = SENDER
    content = prepare_email_content()
    body = MIMEText(content, "html")
    msg.attach(body)
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    server.login(credentials["username"], credentials["password"])
    server.sendmail(SENDER, TO, msg.as_string())
    server.close()


schedule.every().day.at("23:59").do(send_email)
while True:
    schedule.run_pending()
    time.sleep(1)
