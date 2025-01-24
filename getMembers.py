'''
This script fetches all members and outside collaborators of the organizations listed in the .env file.
It interacts with the GitHub API to retrieve member information, including login names and display names.
The fetched data is saved in an Excel file with the current date in its filename.

Main steps:
1. Read organization names and tokens from the .env file.
2. For each organization, retrieve:
   - All members using the GitHub members API.
   - All outside collaborators using the GitHub outside collaborators API.
3. Map and update display names if missing in previous records.
4. Convert organization names from English to Chinese using a reference table.
5. Save the final consolidated data into an Excel file with proper formatting and logging.
'''

import pandas as pd
import os
import requests
import time
from datetime import datetime
import logging
import pandas as pd
import re
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment
import os
import sys

DIR = os.getcwd()
CURRENTDAY = datetime.now().strftime("%Y%m%d")
LAST_WEEK = int(CURRENTDAY)-7
MEMBER_FILE = f'參考檔案\各組織members_{CURRENTDAY}.xlsx'
LOG_FILE = f"參考檔案\各組織members_{CURRENTDAY}.log"

logging.basicConfig(filename=LOG_FILE, level=logging.INFO,encoding='utf-8',
                    format='%(asctime)s - %(levelname)s - %(message)s')

df_dept = pd.read_excel(os.path.join(DIR, '參考檔案\組織中英對照表.xlsx'))
df_before = pd.read_excel(f'參考檔案\各組織members_{LAST_WEEK}.xlsx')

def fetch_all_members(orgName, token):
    url = f"https://api.github.com/orgs/{orgName}/members"
    headers = {
        'Authorization': f'token {token}'
    }
    members = []
    page = 1
    per_page = 50
    max_retries = 5

    while True:
        params = {
            'per_page': per_page,
            'page': page
        }
        retries = 0
        while retries < max_retries:
            try:
                response = requests.get(url, headers=headers, params=params)
                if response.status_code != 200:
                    print(f"Error: {response.status_code}, {response.json()}")
                    logging.error(f"Error: {response.status_code}, {response.json()}")
                    return []
                if response.status_code == 200:
                    
                    data = response.json()
    
                    if not data:
                        return members

                    members.extend(data)
                    if len(data) < per_page:
                        return members   
                    page += 1
                    break

            except requests.exceptions.Timeout:
                retries += 1
                print(f"Timeout occurred. Retrying ({retries}/{max_retries})...")
                time.sleep(2)

            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}")
                logging.error(f"Request failed: {e}")
                return members
            retries += 1
            logging.info(f'retrying...{retries}/{max_retries}')


        if retries == max_retries:
            print("Max retries reached.")
            logging.error(f"Max retries reached in {orgName}.")
            return members

def get_display_name(row):
    url_name = f"https://api.github.com/users/{row['帳號名稱']}"
    response_name = requests.get(url_name, headers=headers).json()
    logging.info(f"打API帳號: {row['帳號名稱']:10s} ")
    return response_name['name'] if response_name['name'] else response_name['login']

allToken = []
with open(DIR + "\Backend\.env", encoding='utf8') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            key, value = line.split('=', 1)
            key = key[4:-6]
            allToken.append({'組織': key.strip(), 'token': value.strip()})

df_token = pd.DataFrame(allToken)[1:]
logging.info(f"共有{len(df_token)}個組織")

df_OrgOwner = pd.DataFrame(columns=['組織', '帳號名稱'])
# df_OrgOwner = pd.read_excel(MEMBER_FILE)
logging.info(f"{'-'*10}組織成員{'-'*10}")

for orgName, token in df_token.values:
    print(orgName)
    logging.info(f"開始處理 {orgName:35s} ")
    all_members = fetch_all_members(orgName, token)
    headers = {
        'Authorization': f'token {token}'
    }

    member = [all['login'] for all in all_members]
    # print(member)
    newrow = pd.DataFrame({'組織':[orgName]*len(member),
                           '帳號名稱':member,})
    df_OrgOwner = pd.concat([df_OrgOwner, newrow], ignore_index=True)
    # for i in range(len(member)):
    #     try:
    #         url_role = f"https://api.github.com/orgs/{orgName}/memberships/{member[i]}" # role
    #         response_role = requests.get(url_role, headers=headers).json()
    
    #         # get display name
    #         # url_name = f"https://api.github.com/users/{member[i]}" # name
    #         # response_name = requests.get(url_name, headers=headers).json()
            
    #         newrow = pd.DataFrame({'組織':[orgName], 
    #                             '帳號名稱':[member[i]],
    #                             # '存取人員':[response_name['name'] if response_name['name'] else response_name['login']], 
    #                             })
    #         print(i, newrow.values)
    #         df_OrgOwner = pd.concat([df_OrgOwner, newrow], ignore_index=True)

    #     except Exception as e:
    #         print(f'ERROR: \n {e}')
    #         df_OrgOwner.to_excel(MEMBER_FILE, index=False)
    #         logging.error(f"ERROR: {e}")
    #         logging.error(f'組織: {orgName}, 帳號: {member[i]} 處理錯誤')
    #         logging.error(response_role)
    #         break
    logging.info(f"組織 {orgName:35s} 共 {len(member)} 位成員")
    time.sleep(2)

df_OrgOwner.to_excel(MEMBER_FILE, index=False)
logging.info(f"組織成員獲取結束")


# outside collaborators
logging.info(f"{'-'*10}外部協作者{'-'*10}")
for orgName, token in df_token.values:
    logging.info(f"開始處理 {orgName:35s} ")
    headers = {
        'Authorization': f'token {token}'
    }
    url = f"https://api.github.com/orgs/{orgName}/outside_collaborators" 
    response_outside = requests.get(url, headers=headers).json()
    
    outside = [all['login'] for all in response_outside]
    newrow = pd.DataFrame({'組織':[orgName]*len(outside),
                           '帳號名稱':outside,})
    df_OrgOwner = pd.concat([df_OrgOwner, newrow], ignore_index=True)
    # if response_outside:
    #     print(orgName)    
           
    #     for i in response_outside:
    #         # url_name = f"https://api.github.com/users/{i['login']}" # name
    #         # response_name = requests.get(url_name, headers=headers).json()

    #         # get display name
    #         newrow = pd.DataFrame({'組織':[orgName], 
    #                             '帳號名稱' :[i['login']],
    #                             # '存取人員' : [response_name['name'] if response_name['name'] else response_name['login']],
    #                             })
    #         print(newrow.values)
    #         df_OrgOwner = pd.concat([df_OrgOwner, newrow], ignore_index=True)
    time.sleep(2)
    logging.info(f"組織 {orgName:35s} 共 {len(response_outside)} 位外部協作者")
df_OrgOwner.to_excel(MEMBER_FILE, index=False)
print('API request finished')

# mapping display name
df_before.drop(columns=['組織', '部門'], inplace=True)
df_before = df_before.drop_duplicates(subset=['帳號名稱'])

df_name = pd.DataFrame(columns=['帳號名稱'])
df_name['帳號名稱'] = df_OrgOwner['帳號名稱'].unique()

df_name = pd.merge(df_name, df_before, on=['帳號名稱'], how='left')
df_name['存取人員'] = df_name.apply( lambda row:
    get_display_name(row) if pd.isna(row['存取人員']) else row['存取人員'],
    axis=1
)
df_OrgOwner = pd.merge(df_OrgOwner, df_name, on=['帳號名稱'], how='left')

df_OrgOwner['存取人員'] = df_OrgOwner['存取人員'].apply(lambda x: ''.join(x.split(' ')) if isinstance(x, str) else x)
logging.info(f"存取人員名稱處理結束")
df_OrgOwner['組織'] = df_OrgOwner['組織'].apply(lambda x: df_dept.loc[df_dept['org_EN']==x, 'org_CN'].values[0] if x in df_dept['org_EN'].values else x)
logging.info(f"組織轉中文結束")
df_OrgOwner.to_excel(MEMBER_FILE, index=False)

# get department by display name
def getDept(name):
    # 用regex抓英文
    # print(name)
    name = name.strip()
    dept = re.findall(r'^[a-zA-Z0-9_-]+', name)
    if dept:
        en = dept[0].upper().replace('-', '_')
    else:
        en = name
    en = re.sub(r'_$', '', en)
    en = en.replace('ACD_RA2', 'ACD_RD2')
    en = en.replace('OLR_ART', 'OLD_ART')
    en = en.replace('ADM_MISSW', 'ADM_MIS')
    return en

def getDeptByOrg(df):
    df['部門'] = df['部門'].str.replace(r'_$', '', regex=True)
    df['部門'] = df.apply(
        lambda row: df_dept.loc[df_dept['org_CN'] == row['組織'], 'dep'].values[0]
        if row['部門'] not in df_dept['dep'].values #and row['組織'] in df_dept['org_CN'].values
        else row['部門']
        , axis=1
    )
    return df

df_OrgOwner['部門'] = df_OrgOwner['存取人員'].apply(getDept)
df_OrgOwner = getDeptByOrg(df_OrgOwner)
df_OrgOwner.to_excel(MEMBER_FILE, index=False)
logging.info(f"獲取存取人員部門")

# edit excel style
workbook = load_workbook(MEMBER_FILE)
worksheet = workbook.active
for cell in worksheet[1]:
    cell.font = Font(bold=False) 
    cell.border = None
    cell.alignment = Alignment(horizontal='left')

    for col in worksheet.columns:
        col_letter = col[0].column_letter
        worksheet.column_dimensions[col_letter].width = 16

workbook.save(MEMBER_FILE)
workbook.close()


