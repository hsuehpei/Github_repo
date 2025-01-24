from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import time
import sys
import os
import logging
import re
from datetime import datetime
from changeXlsxName import change_file_name

DIR = os.getcwd()
DOWNLOAD_DIR = "C:/Users/admin/Downloads"

CURRENTDAY = datetime.now().strftime("%Y%m%d")
BACKEND_LOG_FILE = os.path.abspath(os.path.join(DIR, f'Backend/history_log/backend_{CURRENTDAY}.log'))
LOG_FILE = os.path.abspath(os.path.join(DIR, f'history_file/permission/log/github_fork_{CURRENTDAY}.log'))

logging.basicConfig(filename=LOG_FILE, level=logging.INFO,encoding='utf-8',
                    format='%(asctime)s - %(levelname)s - %(message)s')

def open_browser():
    try:
        logging.info("開始執行，開啟 localhost:4000")
        global driver
        driver = webdriver.Chrome()
        driver.get("http://localhost:4000")
        time.sleep(10)
    except WebDriverException as e:
        logging.error(f"無法開啟瀏覽器: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"程式錯誤: {e}")
        sys.exit(1)
    

def click_download_button():
    try:
        export_all_button = driver.find_element(By.CLASS_NAME, "el-button")
        export_all_button.click()
        time.sleep(3)
    except Exception as e:
        logging.error(f"點選下載按鈕失敗: {e}")
        sys.exit(1)

    try:
        export_button = driver.find_element(By.XPATH, "/html/body/div/div/section/header/div[2]/div/div/div/div/div/div/button")
        export_button.click()
        logging.info("成功點選下載按鈕")
        wait_for_download_start(DOWNLOAD_DIR)
        logging.info("CSV檔案下載完成")
        time.sleep(20)

    except Exception as e:
        logging.error(f"點選確定下載按鈕失敗: {e}")    
        sys.exit(1)
        
    finally:
        driver.quit()

def wait_for_download_start(download_dir, timeout=700):
    seconds = 0
    file_path = os.path.abspath(os.path.join(download_dir, "all_repositories.csv"))
    while seconds < timeout:
        if os.path.exists(file_path):
            print("Download completed")
            return True
        else:
            print("waiting for download ...")
            time.sleep(10)
            seconds += 10

    logging.error("Timeout waiting for download")
    return False


# 從log檔抓error
## socket hang up
def check_socket_error(log_path):
    logging.info("開始檢查 backend log 檔的 socket hang out")
    flag = False
    
    with open(log_path, mode="rt", encoding='utf-8') as inpf:
        latest = None
        log_lines = inpf.readlines()

        for i, line in enumerate(reversed(log_lines)):
            match = re.search('GET /user/orgs', line)
            if match:
                latest = len(log_lines) - i - 1
                break

    if latest is None:
        logging.error("沒有找到日誌條目")
        return flag

    latest_log = ''.join(log_lines[latest:])
    logging.info('找出最近一次日誌並開始檢查')

    matches = re.findall(r"^無法獲取倉庫.*Error: socket hang up$", latest_log, flags=re.MULTILINE)
    if matches:
        logging.error("以下倉庫獲取失敗" + '\n'.join(matches))
        flag = True
        change_file_name(DOWNLOAD_DIR, "all_repositories", "csv", date=count)
    else:
        logging.info("所有倉庫獲取成功")

    return flag

## token
def check_token_error(log_path):
    logging.info("開始檢查 backend log 檔的 token")
    flag = False
    
    with open(log_path, mode="rt", encoding='utf-8') as inpf:
        latest = None
        log_lines = inpf.readlines()

        for i, line in enumerate(reversed(log_lines)):
            match = re.search('> node app.js', line)
            if match:
                latest = len(log_lines) - i - 1
                break

    if latest is None:
        logging.info("沒有找到最近的日誌條目")
        return flag

    latest_log = ''.join(log_lines[latest:])
    logging.info('找出最近一次日誌並開始檢查')

    token_matches = re.findall(r"Error fetching details for organization (.+?): \{", latest_log)

    if token_matches:
        logging.error(f"{token_matches}倉庫token過期，請更新後再執行")
        sys.exit(1)

    else:
        logging.info("token 獲取成功")

    return flag


if __name__ == "__main__":
    count = 1
    try:
        open_browser()
        check_token_error(BACKEND_LOG_FILE)
        click_download_button()
        error_flag = check_socket_error(BACKEND_LOG_FILE)
    except Exception as e:
        logging.error(f'第一次下載後錯誤:\n {e}')
        sys.exit(1)

    if not error_flag:
        pass
    else :
        try:
            logging.error("獲取倉庫時錯誤，30分鐘後再次執行")
            while count <= 6:
                count += 1
                time.sleep(1800) 
                logging.info(f"第{count}次任務執行開始")
                open_browser()
                click_download_button()
                if check_socket_error(BACKEND_LOG_FILE) == 0:
                    logging.info(f"第{count}次執行CSV無錯誤")
                    break
            else:
                logging.error(f"任務失敗超過{count}次({count/2:.1f}HR)，結束")
                sys.exit(1)

        except Exception as e:
            logging.error(f'重複執行下載時錯誤:\n{e}')
            sys.exit(1)
    sys.exit(0)