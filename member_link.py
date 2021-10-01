# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START gmail_quickstart]
from __future__ import print_function
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def member_links():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)

    # Call the Gmail API
    # results = service.users().labels().list(userId='me').execute()
    # labels = results.get('labels', [])
    #
    # if not labels:
    #     print('No labels found.')
    # else:
    #     print('Labels:')
    #     for label in labels:
    #         print(label['name'])

    # Get messages
    # import json
    import base64
    import re
    from bs4 import BeautifulSoup
    member_links = []
    results = service.users().messages().list(userId='me', q="from:noreply@youtube.com").execute()
    # print(results)
    messages = results.get('messages', [])
    member_notif = []
    # Get the latest 10 messages/emails
    for message in messages[0:10]:
        msg = service.users().messages().get(userId='me', id=message['id']).execute()
        # Find email messages(up to 10) that only contain member keywords
        # Optionally instead of regex decode result to utf-8
        if re.search('(Members|Member|member|members)', msg['snippet']) or re.search('(メンバ|メン限)', msg['snippet']):
            print(msg['snippet'])
            member_notif.append(msg)
        else:
            print("Not Member Stream")
    # print(json.dumps(array[0], indent=1, ensure_ascii=False).encode('utf8').decode())
    # print(json.dumps(array[0]["payload"]["parts"], indent=1, ensure_ascii=False).encode('utf-8').decode())
    #Now get data and decode body message
    # print(array[0]["payload"]["parts"][-1]["body"])
    # Look through all the member emails
    for notif in member_notif:
        # print(json.dumps(notif["payload"]["parts"], indent=1, ensure_ascii=False).encode('utf-8').decode())
        if notif["payload"]["parts"][-1]["body"]:
            msg_body = base64.urlsafe_b64decode(notif["payload"]["parts"][-1]["body"]["data"]).decode("utf-8")
            # print(msg_body)
            bsoup = BeautifulSoup(msg_body, "html.parser")

            # try to find link element using its class
            try:
                a_element = bsoup.find('a', class_="nonplayable")
                # try finding link element using the style's attribute
                if a_element is not None:
                    link = a_element['href']
                else:
                    print('Looking at another method')
                    # Note style's attribute value has some extra spaces compare to what's actually in the DOM
                    a_element = bsoup.find('a', style="text-decoration: inherit; color: inherit")
                    # print(a_element)
                    link = a_element['href']
            # Can't find link element possibly due to email just containing member post's text
            except:
                print("\nCan not find element with link\n")
                continue
            # Get video id and reconstruct video url
            id_re = re.compile(r"(&u=/watch%3Fv%3D)(.{11})")
            try:
                link = re.search(id_re, link).group(2)
                link = "https://youtube.com/watch?v=" + link
                if link not in member_links:
                    member_links.append(link)
                    print("Found " + link + "\n")
                else:
                    print("Link has already been added")
            except:
                # change exit to print
                exit("Couldn't get link, maybe url changed")
        else:
            exit("Couldn't decode message's body")
    return member_links
    # print(json.dumps(array, indent=1))
if __name__ == '__main__':
    links = member_links()
    print("\nLinks: ", links)
# [END gmail_quickstart]