import time

from googleapiclient.discovery import build
from google.oauth2 import service_account

from config import spreadsheet_id, cred_file
from db import check_queue, delete_queue, select_all_user_data, select_user_field
from service_file import work_types, regions

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]

credentials = service_account.Credentials.from_service_account_file(
    cred_file, scopes=SCOPES
)

drive_service = build('drive', 'v3', credentials=credentials, cache_discovery=False)
sheet_service = build('sheets', 'v4', credentials=credentials)

SHEET_NAME = "Активные волонтеры"

def get_row_number_by_user_id(user_id, sheet_name=SHEET_NAME):
    print(sheet_name)
    result = sheet_service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=sheet_name
    ).execute()

    rows = result.get('values', [])
    
    for i, row in enumerate(rows[1:], start=2):
        if len(row) > 0 and row[0] == str(user_id):
            return i
    return None


def add_or_update_row_in_google_sheet(values, sheet_name=SHEET_NAME):
    id_to_find = str(values[0])  
    row_number = get_row_number_by_user_id(id_to_find)

    if row_number:
        
        range_to_update = f"{sheet_name}!A{row_number}:Z{row_number}"
        body = {
            'values': [values]
        }
        sheet_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_to_update,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        print(f"Строка с user_id={id_to_find} обновлена (строка {row_number}).")
    else:
        
        body = {
            'values': [values]
        }
        sheet_service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=sheet_name,
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        print(f"Добавлена новая строка с user_id={id_to_find}.")


def delete_row_in_google_sheet(user_id, sheet_name=SHEET_NAME):
    
    row_number = get_row_number_by_user_id(user_id)
    if not row_number:
        print(f"Строка с user_id={user_id} не найдена в Google Sheets.")
        return

    
    spreadsheet = sheet_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = spreadsheet.get('sheets', [])
    
    sheet_id = None
    for s in sheets:
        props = s.get('properties', {})
        if props.get('title') == sheet_name:
            sheet_id = props.get('sheetId')
            break

    if sheet_id is None:
        print(f"Не удалось найти лист с названием '{sheet_name}' в таблице {spreadsheet_id}.")
        return

    
    requests = [{
        "deleteDimension": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "ROWS",
                "startIndex": row_number - 1,  
                "endIndex": row_number
            }
        }
    }]

    body = {'requests': requests}
    sheet_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=body
    ).execute()

    print(f"Строка с user_id={user_id} (строка {row_number}) удалена из Google Sheets.")


def format_rows(values, all_values):
    values = values.split(', ')

    result = list()
    for item in all_values:
        if item in values:
            result.append('Да')
        else:
            result.append('Нет')
    return result

while True:
    
    record = check_queue()
    if record:
        queue_id, user_id, action, sheet_name = record
        
        if action == 'add':
            username, user_id, name, phone, area, wanted_work, with_car, is_activ = select_all_user_data(user_id)  
            
            row = [
                str(user_id),
                username or '',
                name or '',
                phone or '',
                'Да' if with_car else 'Нет'
            ] + format_rows(values=wanted_work, all_values=work_types) + format_rows(values=area, all_values=regions)
            
            add_or_update_row_in_google_sheet(row)

        elif action == 'delete':
            delete_row_in_google_sheet(user_id)

        
        delete_queue(queue_id)

    time.sleep(1)
