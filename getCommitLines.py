'''
This script retrieves the commit list of multiple organizations from the GitHub API within a specified time range and outputs the processed results as Excel files.
Main features:
1. Retrieves all repositories for each organization using multiple tokens.
2. Fetches commit records within the specified time period for each repository.
3. Extracts commit details, including the committer, commit message, modified files, 
   and change statistics (additions, deletions, changes).
4. Matches committers with internal access personnel records to complete the information.
5. Translates organization names to Chinese and writes the results to Excel files.
6. Logs the entire execution process, including errors, for easier monitoring and debugging.
7. Combines files from each organization.

'''

import pandas as pd
import os
import requests
import time
from datetime import datetime, date, timedelta
import requests
import time
import logging
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment
import re


today = date.today()- timedelta(days=6)
yesterday = today - timedelta(days=1)
TODAY = today.strftime("%Y%m%d")
YESTERDAY = yesterday.strftime("%Y%m%d")
end = yesterday.strftime('%Y-%m-%dT23:59:59Z')
start = yesterday.strftime('%Y-%m-01T00:00:00Z')

options = {
    "since" : {
        "datetime" : start
        },
    "until" : {
        "datetime" : end
        }
}

DIR = os.getcwd()
LOG_FILE = os.path.abspath(os.path.join(DIR, f"history_file/commit/log/commit_{TODAY}.log"))
COMMIT_FOLDER = os.path.abspath(os.path.join(DIR, "history_file/commit"))
COMMIT_FOLDER_MONTH = os.path.abspath(os.path.join(COMMIT_FOLDER, yesterday.strftime('%Y%m')))
os.makedirs(COMMIT_FOLDER_MONTH, exist_ok=True)

logging.basicConfig(filename=LOG_FILE, level=logging.INFO,encoding='utf-8',
                    format='%(asctime)s - %(levelname)s - %(message)s')

logging.info(f"開始時間: {options['since']['datetime']}，結束時間: {options['until']['datetime']}")

df_dept = pd.read_excel(os.path.join(DIR, '參考檔案/組織中英對照表.xlsx'))
df_login = pd.read_excel('參考檔案/各組織contributors_20250106.xlsx')

df_login = df_login[['帳號名稱', '存取人員']].drop_duplicates()
name_to_person_map = df_login.set_index('帳號名稱')['存取人員']

allToken = []
with open(DIR + "\Backend\.env", encoding='utf8') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            key, value = line.split('=', 1)
            key = key[4:-6]
            allToken.append({'org': key.strip(), 'token': value.strip()})
df_token = pd.DataFrame(allToken)[1:]

def fetch_all_page(url, headers):
    content = []
    page = 1  # 分頁起始頁
    per_page = 75
    max_retries = 5  # 最大重試次数

    while True:
        params = {
            'per_page': per_page,
            'page': page
        }
        retries = 0
        while retries < max_retries:
            try:
                response = requests.get(url, headers=headers, params=params, timeout=10)
                if response.status_code == 409: # 空repo
                    return []
                elif response.status_code != 200:
                    logging.error(f"Error: {response.status_code}, {response.json()}")
                    logging.error(f"url: {url}")
                    return content
                
                if response.status_code == 200:
                    data = response.json()
                    if not data:
                        return content
                    
                    content.extend(data)
                    if len(data) < per_page:
                        return content
                    page += 1
                    break

            except requests.exceptions.Timeout:
                retries += 1
                print(f"Timeout occurred. Retrying ({retries}/{max_retries})...")
                time.sleep(2)

            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}")
                return content
            # logging.info(f'retrying...{retries}/{max_retries}')
        if retries == max_retries:
            logging.error("Max retries reached.")
            return content
        
def get_commits(orgName, token):
    try:
        logging.info(f"組織: {orgName:35s} 開始")
        start_org = datetime.now()
        COMMIT_FILE = os.path.abspath(os.path.join(COMMIT_FOLDER_MONTH, f"commit_lines_{orgName}_{YESTERDAY}.xlsx"))
        df_sha = pd.DataFrame()
        headers = {
            'Authorization': f'token {token}'
        }
        
        url = f"https://api.github.com/orgs/{orgName}/repos" 
        all_repo = fetch_all_page(url, headers)
        repos = [all['name'] for all in all_repo]
        
        logging.info(f"{orgName:35s} 有 {len(repos):3d} 個repo\n{repos}")

        for repo in repos:
            ls_to_concat = []
            url = f'https://api.github.com/repos/{orgName}/{repo}/commits?since={options["since"]["datetime"]}&until={options["until"]["datetime"]}'
            all_commit = fetch_all_page(url, headers)
            logging.info(f"{repo:55s} 共 {len(all_commit):3d} 個commit")
            
            if all_commit:
                for i, commit in enumerate(all_commit):
                    retries = 0
                    sha_json = None
                    while retries < 3:
                        try:
                            url = f"https://api.github.com/repos/{orgName}/{repo}/commits/{commit['sha']}"
                            response = requests.get(url, headers=headers)
                            if response.status_code == 200:
                                sha_json = response.json()
                                break

                            # logging.info(sha_json)
                            logging.error(f"Error: {response.status_code}, {response.text}")
                            logging.error(f"url: {url}")
                            retries += 1
                            time.sleep(10)
                            logging.info('retrying')
                            continue

                                
                        except requests.exceptions.Timeout:
                            retries += 1
                            logging.error(f"Timeout occurred. Retrying ({retries}/3)...")
                            time.sleep(5)
                        except requests.exceptions.ChunkedEncodingError:
                            retries += 1
                            logging.error(f"ChunkedEncodingError occurred. Retrying ({retries}/3)...")
                            time.sleep(5) 
                        except Exception as e:
                            retry += 1
                            logging.error(f"other exceptions {e}. Retrying ({retries}/3)...")
                            time.sleep(5)

                    if not sha_json:
                        logging.warning(f"[{commit['sha']}] Failed after retries. Skipping commit.")
                        continue

                    files = sha_json.get('files', [])
                    if files:
                        status = [file.get('status') for file in files]
                        file_names = [file.get('filename') for file in files]
                        additions = [file.get('additions') for file in files]
                        deletions = [file.get('deletions') for file in files]
                        changes = [file.get('changes') for file in files]
                    else:
                        # 如果 files 為空，則初始化為 None
                        status = file_names = additions = deletions = changes = [None]

                    new_row = pd.DataFrame({
                        '組織': [orgName] * len(status),
                        '分倉項目': [repo] * len(status),
                        'committer1': [sha_json.get('commit', {}).get('author', {}).get('name')] * len(status),
                        'committer2': [(sha_json.get('committer') or {}).get('login', None)] * len(status),
                        'message': [sha_json.get('commit', {}).get('message', '')] * len(status),
                        'parents': [len(sha_json.get('parents', []))] * len(status),
                        '日期': [pd.to_datetime(sha_json.get('commit', {}).get('committer', {}).get('date')).tz_convert('Asia/Taipei').tz_localize(None)] * len(status),
                        'status': status,
                        'file': file_names,
                        'add': additions,
                        'del': deletions,
                        'changes': changes,
                    })
                    print(f'new_row:{new_row.values}')
                    ls_to_concat.append(new_row)

                # in a repo
                df_new = pd.concat(ls_to_concat, ignore_index=True)
                ls_to_concat = []
                df_sha = pd.concat([df_sha, df_new], ignore_index=True)
                df_sha.to_excel(COMMIT_FILE, index=False, engine='xlsxwriter') # 每個repo寫一次
        if not df_sha.empty: # 有的整個組織無近期commit
            logging.info(f"{orgName} len(repos): {len(repos)}")
            logging.info(f"{orgName} 共 {df_sha['message'].nunique()} 次commit")
            logging.info(f"{orgName} 共 {df_sha.shape[0]} 列")
            logging.info(f"{orgName} 花費時間: {datetime.now() - start_org}")
        else:
            global no_commit_org
            no_commit_org.append(orgName)
            logging.info(f"{orgName} 無commit")

    except Exception as e:
        logging.error(f"Error: {e}")
        if sha_json:
            logging.error(f'sha_json: {sha_json}')
            logging.error(f'respone code: {response.status_code}')
        if ls_to_concat:
            df_sha = pd.concat(ls_to_concat, ignore_index=True)
            logging.info(f"Error 後 concat {len(ls_to_concat)} 筆資料")
        df_sha.to_excel(COMMIT_FILE, index=False, engine='xlsxwriter')
        logging.info(f"except 存檔完成")
        raise e


def assign_person(row):
    """對每個 row 進行判斷並賦值"""
    if row['committer1'] in df_login['存取人員'].values:  # 檢查 committer1 是否在 df_login['存取人員'] 中
        return row['committer1']
    elif row['committer2'] in df_login['存取人員'].values:
        return row['committer2']
    elif row['committer1'] in df_login['帳號名稱'].values:
        return name_to_person_map.get(row['committer1'], row['存取人員'])
    elif row['committer2'] in df_login['帳號名稱'].values:
        return name_to_person_map.get(row['committer2'], row['存取人員'])
    elif row['committer2'] == 'web-flow':
        return row['committer1']
    
    elif isinstance(row['committer1'], str) and (row['committer1'].startswith('OLD') or row['committer1'].startswith('ACD')):
        return row['committer1']
    elif isinstance(row['committer2'], str) and (row['committer2'].startswith('OLD') or row['committer1'].startswith('ACD')):
        return row['committer2']
    elif row['committer1'] == 'System':
        return 'System'    
    
def name_api(row, headers):
    if not pd.isna(row['committer2']):
        try:
            url_name = f"https://api.github.com/users/{row['committer2']}"
            logging.info(f"打api:{row['committer2']}")
            # print(url_name)
            response_name = requests.get(url_name, headers=headers).json()
            # print(response_name)
            if response_name['name'] is not None:
                return response_name['name']
        except Exception as e:
            logging.error(url_name, e)

    else:
        try:
            url_name = f"https://api.github.com/users/{row['committer1']}"
            logging.info(f"打api:{row['committer1']}")
            response_name = requests.get(url_name, headers=headers).json()
            if response_name.get('name', None) is not None:
                return response_name['name']
        except Exception as e:
            logging.error(url_name, e)

    return row['committer1']

def get_person(orgName, token):
    logging.info(f"{orgName:20s} 檔案處理")
    headers = {
        'Authorization' : f'token {token}',
    }

    COMMIT_FILE = os.path.abspath(os.path.join(COMMIT_FOLDER_MONTH, f"commit_lines_{orgName}_{YESTERDAY}.xlsx"))
    df_commit = pd.read_excel(COMMIT_FILE)
    
    # 處理displayname空格等問題
    df_commit['committer1'] = df_commit['committer1'].apply(lambda x: ''.join(x.split(' ')) if isinstance(x, str) else x)
    df_commit['committer2'] = df_commit['committer2'].apply(lambda x: ''.join(x.split(' ')) if isinstance(x, str) else x)

    df_commit['存取人員'] = None
    df_commit['存取人員'] = df_commit.apply(assign_person, axis=1)

    # 要打API的人
    df_filtered = df_commit.loc[df_commit['存取人員'].isna(), ['committer1', 'committer2']]
    df_strange = df_filtered.drop_duplicates(subset='committer1', keep='first').reset_index(drop=True)
    if not df_strange.empty:
        df_strange['存取人員'] = df_strange.apply(lambda row: name_api(row, headers), axis=1)
        df_strange_filtered = df_strange[['committer1', '存取人員']]
        df_commit = df_commit.merge(df_strange_filtered, on='committer1', how='left', suffixes=('', '_strange'))

        df_commit['存取人員'] = df_commit['存取人員'].fillna(df_commit['存取人員_strange'])
        df_commit.drop(columns=['存取人員_strange'], inplace=True)


    df_commit['組織'] = df_commit['組織'].apply(lambda x: df_dept.loc[df_dept['org_EN']==x, 'org_CN'].values[0] if x in df_dept['org_EN'].values else x)
    logging.info(f"組織轉中文結束")

    df_commit.to_excel(COMMIT_FILE, index=False)
    logging.info(f"寫入{COMMIT_FILE}完成")    

no_commit_org = []
ls_to_concat = []

for orgName, token in df_token.values:
    get_commits(orgName, token)
    logging.info(f'處理{orgName}')

    if orgName in no_commit_org:
        logging.info(f"{orgName:20s} 無commit，不處裡檔案")
    else:
        get_person(orgName, token)

logging.info(f"組織 {no_commit_org} 無commit")
logging.info(f"組織數量: {df_token.shape[0]}")

xlsx_files = [f for f in os.listdir(COMMIT_FOLDER_MONTH) if f.endswith('.xlsx') and f.startswith('commit_lines')]
logging.info(f'{len(xlsx_files)}個檔案待合併')

# 合併所有檔案
df_combined = pd.DataFrame()
for file in xlsx_files:
    file_path = os.path.join(COMMIT_FOLDER_MONTH, file)
    df = pd.read_excel(file_path)
    df_combined = pd.concat([df_combined, df], ignore_index=True)

output_file = os.path.join(COMMIT_FOLDER_MONTH, f'combined_{YESTERDAY}.xlsx')
df_combined.to_excel(output_file, index=False)
logging.info('檔案合併成功')

# 新增部門
def getDept(name):
    name = name.strip()
    dept = re.findall(r'^[a-zA-Z0-9_-]+', name)
    if dept:
        en = dept[0].upper().replace('-', '_')
    else:
        en = name
    en = re.sub(r'_$', '', en)
    en = re.sub(r'-$', '', en)
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

try:
    df_OrgOwner = pd.read_excel(output_file)
    df_OrgOwner['部門'] = df_OrgOwner['存取人員'].apply(getDept)
    logging.info('成功取得 display name 前的部門')
    df_OrgOwner = getDeptByOrg(df_OrgOwner)
    logging.info('成功取得 org 部門')
    df_OrgOwner.to_excel(output_file, sheet_name='all_repositories', index=False)
except Exception as e:
    logging.error(f'取得部門失敗{e}')

workbook = load_workbook(output_file)
worksheet = workbook.active
for cell in worksheet[1]:
    cell.font = Font(bold=False) 
    cell.border = None
    cell.alignment = Alignment(horizontal='left')
workbook.save(output_file)
workbook.close()


# each_month = [int(f) for f in os.listdir(COMMIT_FOLDER) if f!='log']
# for folder in each_month:
#     if folder not in sorted(each_month)[:3]:
#         os.remove(os.path.join(COMMIT_FOLDER, str(folder)))
#         logging.info(f"刪除{folder}資料夾")
