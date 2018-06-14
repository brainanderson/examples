import csv

from mailchimp3 import MailChimp

client = MailChimp('account_name', 'API_KEY')

campaigns = client.campaigns.all(get_all=True)

csv_file = open('outreach.csv', 'w')
writer = csv.writer(csv_file, delimiter=',')

for campaign in campaigns['campaigns']: #[:1]
    try:
        campaign_subject = campaign['settings']['subject_line']
    except KeyError:
        print(f"\n{campaign} does not have a subject line assigned\n")
        continue

    try:
        segment_id = str(campaign['recipients']['segment_opts']['saved_segment_id'])
    except KeyError:
        print(f"\n{campaign_subject} does not have a segment assigned\n")
        continue

    try:
        folder_id = str(campaign['settings']['folder_id'])
    except KeyError:
        print(f"\n{campaign_subject} does not have a folder assigned\n")
        continue

    # list_count = str(campaign['emails_sent'])
    folder = client.campaign_folders.get(folder_id=folder_id)

    outreach_code = folder.get('name')
    list_members = client.lists.segments.members.all(list_id='abcd12345', segment_id=segment_id, fields='members.merge_fields.MMERGE3', get_all=True)
    member_count = 0

    for member in list_members['members']:
        send_date = campaign['send_time'].split('T')[0]
        member_id = member['merge_fields']['MMERGE3']
        row = member_id, "", outreach_code, send_date, 'A', 'X', campaign_subject

        writer.writerow(row)
        member_count += 1

    print(f"{campaign_subject} - Member count: {member_count}")

csv_file.close()
