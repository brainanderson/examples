#!/usr/bin/python3
"""
Automates folder creation and image resizing for web and email.
Finds images in the incoming directory.
"""

import os, shutil, datetime, httplib2, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import PIL
from PIL import Image

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from apiclient.http import MediaFileUpload

import credentials

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# Directories
BASE_DIR = '/test/test' # Change to base dir on system
INCOMING_DIR = '___INCOMING___' # Name of dir to use

# Email recipeient
EMAIL_RECIP = 'test@test.com' # Email address to be sent to when task completed
EMAIL_ACCOUNT = credentials.email['account']
EMAIL_PASSWORD = credentials.email['password']

# Google drive config
SCOPES = 'https://www.googleapis.com/auth/drive.file'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Copy to Drive'

# Checks if files are in the incoming folder and moves to a new or existing folder
def main():
    dirs = os.listdir(os.path.join(BASE_DIR, INCOMING_DIR))

    if dirs != []:
        for filename in dirs:
            filename = filename.lower()
            f_name, f_ext = os.path.splitext(filename)

            # Checks if dirctory named after the file already exists
            if os.path.isdir(os.path.join(BASE_DIR, f_name)):
                print(f'{f_name} directory already exists.')
                move_copy(filename)

            else:
                os.mkdir(os.path.join(BASE_DIR, f_name))
                print(f'Directory named {f_name} created')
                move_copy(filename)

    else:
        print('No files found')

# Moves and copies files to desitnation directory
def move_copy(filename):
    f_name, f_ext = os.path.splitext(filename)
    shutil.move(os.path.join(BASE_DIR, INCOMING_DIR, filename), os.path.join(BASE_DIR, f_name))

    print(f'{filename} moved to {f_name} directory')

    img_resize(f_name, f_ext)

def img_resize(f_name, f_ext):
    print(f'Resizing image {f_name + f_ext}')

    today = datetime.date.today()
    month = today.month
    year = today.year

    image = f_name + f_ext
    widths = [1200, 2400]

    for width in widths:
        img = Image.open(os.path.join(BASE_DIR, f_name, image))
        wpercent = (width / float(img.size[0]))
        hsize = int((float(img.size[1]) * float(wpercent)))
        img = img.resize((width, hsize), PIL.Image.ANTIALIAS)
        resized_image = '_'.join((f_name, str(width))) + 'px' + f_ext
        resized_img_path = os.path.join(BASE_DIR, f_name, resized_image)
        img.save(resized_img_path)

        # Rename original file
        #shutil.copy(os.path.join(f_name, filename), '%s/%s_web.%s' % (d_path, f_name, f_ext))
        copy_to_drive(resized_img_path, resized_image)

        print('Image resized!')

        email_send(f_name)




def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'drive-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def copy_to_drive(resized_img_path, resized_image):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    drive_service = discovery.build('drive', 'v3', http=http)

    folder_id = 'id_of_google_drive_folder' # Enter id of drive folder
    file_metadata = {
      'name' : resized_image,
      'parents': [ folder_id ]
    }
    media = MediaFileUpload(resized_img_path,
                            mimetype='image/jpeg',
                            resumable=True)
    file = drive_service.files().create(body=file_metadata,
                                        media_body=media,
                                        fields='id').execute()
    print(f'File ID: {file.get('id')}')

# Sends email when files are copied and resized
def email_send(f_name):
    msg = MIMEMultipart()
    msg['From'] = 'Email Name and Address' # Add email name and address
    msg['To'] = EMAIL_RECIP
    msg['Subject'] = 'NOTIFICATION: Test Send of email'

    body = f'<h3>{f_name} has been copied to the folder</h3>'
    msg.attach(MIMEText(body, 'html'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
    text = msg.as_string()
    server.sendmail(EMAIL_ACCOUNT, EMAIL_RECIP, text)
    server.quit()

    print(f'Email sent to {EMAIL_RECIP}')



if __name__ == '__main__':
    main()
