# convert csv to xlsx and change file name
from datetime import datetime
import os
import logging
import glob
import time

DIR = os.getcwd()
CURRENTDAY = datetime.now().strftime("%Y%m%d")

SAVE_DIR = os.path.abspath(os.path.join(DIR, "history_file"))
LOG_FILE = os.path.abspath(os.path.join(DIR, f"history_file/log/github_fork_{CURRENTDAY}.log"))
LOG_FOLDER = os.path.abspath(os.path.join(DIR, "history_file/log"))
BACKEND_LOG_FOLDER = os.path.abspath(os.path.join(DIR, "Backend/history_log"))

N = 14
N_DAYS_AGO = time.time() - (N * 86400)

logging.basicConfig(filename=LOG_FILE, level=logging.INFO,encoding='utf-8',
                    format='%(asctime)s - %(levelname)s - %(message)s')

def change_file_name(path, fname, ext, date=0):
    logging.info(f'變更 {fname} 檔案名稱為今天日期')
    old_name = os.path.abspath(os.path.join(path, fname + f'.{ext}'))
    fname_len = len(fname) + 1 + len(ext)

    if date==0:
        current_date = datetime.now().strftime("%Y%m%d")
        new_name = path + f'/{fname}_{current_date}.{ext}'
    else:
        new_name = path + f'/{fname}_{date}.{ext}'

    if os.path.exists(old_name):
        try:
            os.rename(old_name, new_name)
            logging.info(f"檔案 {old_name[-fname_len:]} 更名為 {new_name[-fname_len-9:]}")
        except FileExistsError:
            logging.error(f"檔案 {new_name[-fname_len-9:]} 已存在")
        except Exception as e:
            logging.error(f"更名失敗: {e}")
    else:
        logging.error(f"檔案 {old_name} 不存在")


def del_files(folder):
    for file in os.listdir(folder):
        file_path = os.path.join(folder, file)

        if os.path.isfile(file_path):
            file_mtime = os.path.getmtime(file_path)
            if file_mtime < N_DAYS_AGO:
                logging.info(f"刪除{N}天前編輯的檔案: {file_path}")
                os.remove(file_path)
        
        if os.path.isdir(file_path):
            del_files(file_path)

def main():
    change_file_name(SAVE_DIR, "all_repositories", "xlsx")
    del_files(LOG_FOLDER)
    del_files(BACKEND_LOG_FOLDER)
    del_files(SAVE_DIR)
    logging.info("今日任務結束")


if __name__ == "__main__":
    main()