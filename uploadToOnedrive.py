from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
import autoit
from datetime import datetime
import ctypes
import sys
import time
import os
import logging

# ChromeDriver 
# CHROME_DRIVER_PATH = "C:/Program Files/Google/Chrome/Application/chrome.exe"
DIR = os.getcwd()
CURRENTDAY = datetime.now().strftime("%Y%m%d")
ACCOUNT = "dorispeiyu@gmail.com"
PASSWORD = os.environ.get('ONEDRIVE_PASSWORD')

SAVE_DIR = os.path.abspath(os.path.join(DIR, "history_file"))
SAVE_PATH = os.path.abspath(os.path.join(SAVE_DIR, "all_repositories.xlsx"))
LOG_FILE = os.path.abspath(os.path.join(DIR, f"history_file/log/github_fork_{CURRENTDAY}.log"))


logging.basicConfig(filename=LOG_FILE, level=logging.INFO,encoding='utf-8',
                    format='%(asctime)s - %(levelname)s - %(message)s')

max_retries = 3
retry_count = 0

while retry_count < max_retries:
    try:
        driver = webdriver.Chrome()
        driver.get("https://onedrive.live.com/login/")

        iframe = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "iframe"))
        )
        driver.switch_to.frame(iframe)

        # account
        email_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div/main/div[2]/div[2]/div/input"))
        )
        time.sleep(3)
        email_input.send_keys(ACCOUNT)
        next_button = driver.find_element(By.XPATH, "/html/body/div[2]/div/main/div[2]/div[4]/input")
        next_button.click()
        logging.info(f"成功輸入帳號 : {ACCOUNT}")

        # pwd
        time.sleep(5)
        driver.switch_to.active_element.send_keys(PASSWORD)
        login_button = driver.find_element(By.XPATH, "/html/body/div[1]/div/div/div/div[2]/div[1]/div/div/div/div/div[2]/div[2]/div/form/div[5]/div/div/div/div/button")
        login_button.click()
        logging.info("成功輸入密碼")

        # keep login window
        no_button = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div/div/div[2]/div[1]/div/div/div/div/div[2]/div[2]/div/form/div[3]/div[2]/div/div[1]/button"))
        )
        no_button.click()
        logging.info("登入成功")

        break

    except Exception as e:
        retry_count += 1
        logging.error(f"登入帳號 {ACCOUNT} 失敗: {e}. 正在重試 ({retry_count}/{max_retries})")

        if retry_count >= max_retries:
            logging.error(f"達到最大重試次數 ({max_retries})，停止嘗試")
            sys.exit(1)

        driver.quit()
        time.sleep(3)

# in onedrive
try: # into shared window
    time.sleep(5)
    share_link = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//a[@title='已共用']"))
    )
    share_link.click()

    # into shared folder
    time.sleep(3)
    shared_folder = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, "//button[@title='Github儀錶板用']"))
    )
    shared_folder.click()
    logging.info("成功進入共用資料夾")
    time.sleep(3)    

except Exception as e:
    logging.error(f"進入共用資料夾失敗: {e}")
    sys.exit(1)

try: # upload file
    time.sleep(3)
    add_button = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, '//button[@data-id="AddNew" and @title="新增新的"]'))

    )
    add_button.click()
    
    time.sleep(3)
    file_upload = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, '//button[@title="檔案上傳" and @data-automationid="UploadFileCommand"]'))

    )
    file_upload.click()

    logging.info("成功點選上傳檔案按鈕，彈出win檔案選擇視窗")
    time.sleep(3)

except Exception as e:
    logging.error(f"點選上傳檔案失敗: {e}")  
    sys.exit(1)

try:
    time.sleep(3)
    try:
        autoit.win_activate("開啟") # 轉成活動狀態
        # autoit.win_wait_active("開啟") # 英文系統要改
        if not autoit.win_wait_active("開啟", 10):
            autoit.win_activate("開啟")
        logging.info('喚醒開啟視窗')
    except Exception as e:
        logging.error(f'喚醒開啟視窗報錯{e}')   
    

    autoit.control_send("開啟", "Edit1", SAVE_PATH)
    logging.info('輸入檔案位置')
    time.sleep(3)
    file_entered = autoit.control_get_text("開啟", "Edit1")
    autoit.control_click("開啟", "Button1")
    logging.info(f"點選開啟，成功在win視窗選擇檔案 : {file_entered}")
    time.sleep(5)
    
except Exception as e:
    logging.error(f"在win視窗選擇檔案失敗: {e}")  
    sys.exit(1)

try:
    time.sleep(5)

    upload_confirm = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, "//span[text()='取代']"))
    )
    upload_confirm.click()
    logging.info("成功上傳並取代舊檔")
    time.sleep(10)
    sys.exit(0)

except Exception as e:
    logging.error(f"開啟或取代檔案失敗: {e}")  
    sys.exit(1)


