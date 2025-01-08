'''
get department by display name
'''

import pandas as pd
import re
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment
import os
import sys

FILENAME = sys.argv[1]
DIR = os.getcwd()
FILE = f'參考檔案\{FILENAME}.xlsx'
print(f'欲新增部門的檔案: {FILE}')
df_dept = pd.read_excel(os.path.join(DIR, '參考檔案/組織中英對照表.xlsx'))

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

df_OrgOwner = pd.read_excel(FILE)
df_OrgOwner['部門'] = df_OrgOwner['存取人員'].apply(getDept)
df_OrgOwner = getDeptByOrg(df_OrgOwner)
df_OrgOwner.to_excel(FILE, index=False)

# edit excel style
workbook = load_workbook(FILE)
worksheet = workbook.active
for cell in worksheet[1]:
    cell.font = Font(bold=False) 
    cell.border = None
    cell.alignment = Alignment(horizontal='left')
workbook.save(FILE)
workbook.close()
