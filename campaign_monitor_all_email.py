"""
Campaign Monitor API connection that creates a csv that contains all email recipients.
"""
import sys
import datetime
import csv
import configparser
import hashlib

from createsend import *
from dateutil.relativedelta import *

# Prompt user for date range
today = datetime.datetime.now().date()
last_month = today - relativedelta(months=1)
print("Enter date range - start date to end date")
start_date = input(f'Enter start date (hit enter for: {last_month}): ') or str(last_month)
end_date = input(f'Enter end date (hit enter for: {today}): ') or str(today)

# Set csv filename and format dates
csv_name = ['campus_email', start_date, end_date + '.csv']
csv_file_name = '_'.join(csv_name)
start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()

# Open csv file and write first header row
csv_file = open(csv_file_name, 'w')
writer = csv.writer(csv_file, delimiter=',')
heading_row = 'sent_datetime', 'client_id', 'client_name','campaign_id', 'campaign_name', 'campaign_subject', 'email_address_hashed', 'list_id'
writer.writerow(heading_row)

# Set api key in config.ini
config = configparser.ConfigParser()
config.read('config.ini')
api_key = config['CREDENTIALS']['apiKey']
auth = {'api_key': api_key}
cs = CreateSend(auth)
clients = cs.clients()

# Loops through clients and writes campaigns and email lists to csv
for cl in clients:
    client_id = cl.ClientID
    client_name = cl.Name
    client = Client(auth, client_id)

    for cm in client.campaigns():
        recipient_count = 0
        sent_datetime = datetime.datetime.strptime(cm.SentDate, '%Y-%m-%d %H:%M:%S')
        split_datetime = cm.SentDate.split(' ')
        sent_date = split_datetime[0]
        sent_date = datetime.datetime.strptime(sent_date, '%Y-%m-%d').date()

        if sent_date >= start_date and sent_date <= end_date:
            campaign_id = cm.CampaignID
            campaign_name = cm.Name
            campaign_subject = cm.Subject
            campaign_recipient_total = cm.TotalRecipients
            campaign = Campaign(auth, campaign_id)
            number_of_pages = campaign.recipients().NumberOfPages
            print(f"\nNOW WRITING TO CSV: \nClient ID: {client_id}\nClient name: {client_name}\nCampaign ID: {campaign_id}\nCampaign name: {campaign_name}\nSubject: {campaign_subject}\nSent date: {sent_datetime}\nRecipients: {campaign_recipient_total}")

            for page in range(number_of_pages + 1):
                recipients = campaign.recipients(page=page+1).Results

                for recipient in recipients:
                    email_address_hashed = hashlib.sha1(recipient.EmailAddress.encode('utf-8')).hexdigest()
                    list_id = recipient.ListID
                    row = sent_datetime, client_id, client_name, campaign_id, campaign_name, campaign_subject, email_address_hashed, list_id
                    writer.writerow(row)
                    recipient_count += 1

            print(f"> {recipient_count} recipients added from {campaign_name}")

        else:
            continue


csv_file.close()

print(f"\nDONE! {csv_file_name} now ready for use")
