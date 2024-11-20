# convert csv to xlsx
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment
import os
import logging
import sys
from datetime import datetime

DIR = os.getcwd()
DOWNLOAD_DIR = "C:/Users/admin/Downloads"

SAVE_DIR = os.path.abspath(os.path.join(DIR, "history_file"))
CSV_PATH = os.path.abspath(os.path.join(DOWNLOAD_DIR, "all_repositories.csv"))
XLSX_PATH = os.path.abspath(os.path.join(SAVE_DIR, "all_repositories.xlsx"))
CURRENTDAY = datetime.now().strftime("%Y%m%d")
LOG_FILE = os.path.abspath(os.path.join(DIR, f"history_file/log/github_fork_{CURRENTDAY}.log"))

logging.basicConfig(filename=LOG_FILE, level=logging.INFO,encoding='utf-8',
                    format='%(asctime)s - %(levelname)s - %(message)s')

def convert_csv_to_xlsx(csv_file, xlsx_file):
    if os.path.exists(csv_file):
        try:
            logging.info(f"all_repositories.csv 檔案存在，開始轉換檔案成xlsx")
            data = pd.read_csv(csv_file, encoding='utf-8-sig')
            logging.info(f"all_repositories.csv 讀取成功")
            data.to_excel(xlsx_file, sheet_name='all_repositories', index=False)
            logging.info(f"all_repositories.xlsx 轉檔成功")
        except Exception as e:
            logging.error(f"轉換檔案失敗: {e}")
            sys.exit(1)

        try:
            logging.info(f"開始調整 all_repositories.xlsx 樣式")
            workbook = load_workbook(xlsx_file)
            worksheet = workbook.active
            for cell in worksheet[1]:
                cell.font = Font(bold=False) 
                cell.border = None
                cell.alignment = Alignment(horizontal='left')
            workbook.save(xlsx_file)
            workbook.close()
            logging.info(f"調整完成，可上傳至 onedrive")
        except Exception as e:
            logging.error(f"樣式調整失敗: {e}")
            sys.exit(1)

    else:
        logging.error(f"檔案 {csv_file} 不存在")
        sys.exit(1)

def main():
    convert_csv_to_xlsx(CSV_PATH, XLSX_PATH)

if __name__ == "__main__":
    main()