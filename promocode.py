import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import datetime


SCOPES = ["https://www.googleapis.com/auth/spreadsheets", 'https://www.googleapis.com/auth/drive']

def authenticate():
    creds = None
    if os.path.exists('token.json'):
        with open('token.json', 'r') as token:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('sheets', 'v4', credentials=creds)
    return service

def update_sheet():
    service = authenticate()
    sheet_id = '1FHagsLA0Qbz9TDkPfGVhmA52S_u99D61ZPbvxR97iDs'
    sheet = service.spreadsheets()

    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=sheet_id, range='A2:C')
        .execute()
    )

    

    rows = result.get("values", [])
    promo = ''
    for i, row in enumerate(rows):
        if row[1].lower() == 'нет':

            row_number = i + 2
            promo = row[0]

            today_date = datetime.datetime.today().strftime('%Y-%m-%d')
            range_update = f'B{row_number}:C{row_number}'
            body = {
                'values': [['Да', today_date]]
            }
            result_update = (
                service.spreadsheets()
                .values()
                .update(
                    spreadsheetId=sheet_id,
                    range=range_update,
                    valueInputOption="USER_ENTERED",
                    body=body,
                )
                .execute()
            )


            break

    if promo == "":
        return "Нет промокода"
    else:
        return promo

if __name__ == '__main__':
    print(update_sheet())