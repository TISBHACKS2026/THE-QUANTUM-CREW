import smtplib
import datetime as dt
import random
now= dt.datetime.now()
weekday=now.weekday()
print(weekday)
my_email = "raysinita8@gmail.com"
password = "ecqhldtxksfrimql"
if weekday==4:
    with open("quotes.txt") as quote_file:
        all_quotes=quote_file.readlines()
        quote=random.choice(all_quotes)
        with smtplib.SMTP("smtp.gmail.com", port=587) as connection:
            connection.starttls()
            connection.login(user=my_email, password=password)
            connection.sendmail(from_addr=my_email, to_addrs="sinitaray07@gmail.com",
                                msg=f"Subject:Motivational quote of the week\n\n,{quote}"
                                )

