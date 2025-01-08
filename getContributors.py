'''
This script retrieves the contributor list of multiple organizations from the GitHub API and outputs the processed results as Excel files.
Main features:
1. Retrieves all repositories for each organization using multiple tokens.
2. Fetches all contributors for each repository, including both internal members and external contributors, along with their commit counts.
3. Extracts contributor details, such as account name and display name, by making additional API calls.
4. Matches contributors with internal access personnel records to calculate the number of repositories each contributor has access to.
5. Translates organization names to Chinese using a reference table and formats the results before exporting.
6. Implements error handling and retry mechanisms for API requests, ensuring stability and data integrity during execution.
7. Logs the execution process, including progress and errors, for easier monitoring and debugging.
'''

import pandas as pd
import os
import requests
import time
from datetime import datetime
import requests
import time

CURRENTDAY = datetime.now().strftime("%Y%m%d")
DIR = os.getcwd()
CONTRIBUTE_FILE = f'參考檔案\各組織contributors_{CURRENTDAY}.xlsx'

def fetch_all_page(url, headers):
    content = []
    page = 1
    per_page = 50
    max_retries = 5  # 最大重试次数

    while True:
        params = {
            'per_page': per_page,
            'page': page
        }
        retries = 0
        while retries < max_retries:
            try:
                response = requests.get(url, headers=headers, params=params, timeout=10)
                if response.status_code not in [200, 204]:
                    print(f"Error: {response.status_code}, {response.json()}")
                    return content
                
                if response.status_code == 200:
                    data = response.json()
                    if not data:  # 当前页无数据，结束循环
                        return content
                    
                    content.extend(data)  # 添加数据到总列表
                    if len(data) < per_page:  # 当前页数据不足 per_page，说明是最后一页
                        return content

                    page += 1
                    break

                if response.status_code == 204:
                    return content

            except requests.exceptions.Timeout:
                retries += 1
                print(f"Timeout occurred. Retrying ({retries}/{max_retries})...")
                time.sleep(2)  # 等待 2 秒后重试

            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}")
                return content

        if retries == max_retries:
            print("Max retries reached.")
            return content

def get_display_name(row):
    url_name = f"https://api.github.com/users/{row['帳號名稱']}"
    response_name = requests.get(url_name, headers=headers).json()
    row['存取人員'] = response_name['name'] if response_name['name'] else response_name['login']
    return row


df_dept = pd.read_excel('參考檔案\組織中英對照表.xlsx')
allToken = []
with open(DIR + "\Backend\.env", encoding='utf8') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            key, value = line.split('=', 1)
            key = key[4:-6]
            allToken.append({'org': key.strip(), 'token': value.strip()})
df_token = pd.DataFrame(allToken)[1:]



df_OrgOwner = pd.DataFrame(columns=['組織', '分倉項目', '帳號名稱', 'commit_times'])
# df_OrgOwner = pd.read_excel(CONTRIBUTE_FILE)

for orgName, token in df_token.values:
    if orgName in df_OrgOwner['組織'].values:
        print(f'{orgName} is already in the list')

    print(orgName)
    headers = {
        'Authorization': f'token {token}'
    }
    
    url = f"https://api.github.com/orgs/{orgName}/repos" 
    all_repo = fetch_all_page(url, headers)
    repos = [all['name'] for all in all_repo]

    for i, repo in enumerate(repos):
        if repo in df_OrgOwner['分倉項目'].values:
            print(f'{orgName} - {repo} is already in the list')
            continue
        
        url_contributors = f"https://api.github.com/repos/{orgName}/{repo}/contributors" # 獲取所有貢獻者，無論是成員還是外部貢獻者

        response_contributors = fetch_all_page(url_contributors, headers)
        if response_contributors: # 如果有貢獻者
            all_contributors = [all['login'] for all in response_contributors]
            all_contributor_times = [all['contributions'] for all in response_contributors]

            if all_contributors :
                newrow = pd.DataFrame({'組織':orgName, 
                                    '分倉項目':repo,
                                    '帳號名稱': all_contributors,
                                    # '存取人員':[response_name['name'] if response_name['name'] else response_name['login']], 
                                    'commit_times':all_contributor_times
                                    })
                print(newrow.values[0])
                df_OrgOwner = pd.concat([df_OrgOwner, newrow], ignore_index=True)

            if i % 3 == 0:
                df_OrgOwner.to_excel(CONTRIBUTE_FILE, index=False)

df_commiter = pd.DataFrame(columns=['存取人員', '帳號名稱', '具有repo權限數量'])
df_commiter['帳號名稱'] = df_OrgOwner['帳號名稱'].unique()
df_commiter = df_commiter.apply(get_display_name, axis=1)

df_all = pd.read_excel(f'參考檔案/all_repositories_20241231.xlsx')
df_commiter['具有repo權限數量'] = df_commiter['存取人員'].apply(lambda x: sum(df_all['存取人員']==x))
df_OrgOwner = pd.merge(df_OrgOwner, df_commiter, on=['帳號名稱'], how='left')

df_OrgOwner['存取人員'] = df_OrgOwner['存取人員'].apply(lambda x: ''.join(x.split(' ')) if isinstance(x, str) else x)
df_OrgOwner['組織'] = df_OrgOwner['組織'].apply(lambda x: df_dept.loc[df_dept['org_EN']==x, 'org_CN'].values[0] if x in df_dept['org_EN'].values else x)
df_OrgOwner.to_excel(CONTRIBUTE_FILE, index=False)
