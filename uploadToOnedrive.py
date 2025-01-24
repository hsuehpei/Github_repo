"""
This script automates the process of logging into OneDrive, navigating to a shared folder, 
and uploading an Excel file using Selenium WebDriver and AutoIt for handling Windows file dialogs.

Main features:
1. Logs into OneDrive using the provided credentials securely stored in environment variables.
2. Navigates to the shared folder named "Github儀錶板用".
3. Uploads the specified Excel file by interacting with the Windows file selection dialog via AutoIt.
4. Handles potential file overwrite scenarios by confirming the replacement.
5. Implements retry logic to handle login failures and ensures a maximum number of attempts.
6. Captures screenshots and logs error messages for easier monitoring and debugging.
7. Ensures proper logging of each step to facilitate troubleshooting and process validation.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import autoit
from datetime import datetime
import sys
import time
import os
import logging

DIR = os.getcwd()
CURRENTDAY = datetime.now().strftime("%Y%m%d")
ACCOUNT = "dorispeiyu@gmail.com"
PASSWORD = os.environ.get('ONEDRIVE_PASSWORD')

SAVE_DIR = os.path.abspath(os.path.join(DIR, "history_file/permission"))
SAVE_PATH = os.path.abspath(os.path.join(SAVE_DIR, "all_repositories.xlsx"))
LOG_FILE = os.path.abspath(os.path.join(SAVE_DIR, f"log/github_fork_{CURRENTDAY}.log"))


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
        # EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div[2]/div/div/div[1]/div/nav/div[1]/div[1]/div/span/button"))
        EC.element_to_be_clickable((By.XPATH, '//button[@data-id="AddNew" and @title="新增新的"]'))

    )
    add_button.click()
    
    time.sleep(3)
    file_upload = WebDriverWait(driver, 15).until(
        # EC.element_to_be_clickable((By.XPATH, "//button[contains(@title, '檔案上傳')]"))
        # EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/div/div/div/div/div/div/div/ul/li[3]/button"))
        EC.element_to_be_clickable((By.XPATH, '//button[@title="檔案上傳" and @data-automationid="UploadFileCommand"]'))

    )
    file_upload.click()

    logging.info("成功點選上傳檔案按鈕，彈出win檔案選擇視窗")
    time.sleep(3)

except Exception as e:
    driver.save_screenshot(os.path.join(SAVE_DIR, f'log/{CURRENTDAY}_selectFolderError.png'))
    logging.error("擷取螢幕畫面")    
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
        driver.save_screenshot(os.path.join(SAVE_DIR, f'log/{CURRENTDAY}_activateWindowError.png'))
        logging.error("擷取螢幕畫面")        
        logging.error(f'喚醒開啟視窗錯誤{e}')
    

    autoit.control_send("開啟", "Edit1", SAVE_PATH)
    logging.info('輸入檔案位置')
    time.sleep(3)
    file_entered = autoit.control_get_text("開啟", "Edit1")
    autoit.control_click("開啟", "Button1")
    logging.info(f"點選開啟，成功在win視窗選擇檔案 : {file_entered}")
    time.sleep(5)
    
except Exception as e:
    driver.save_screenshot(os.path.join(SAVE_DIR, f'log/{CURRENTDAY}_selectFileError.png'))
    logging.error("擷取螢幕畫面")
    logging.error(f"在win視窗選擇檔案失敗: {e}")  
    sys.exit(1)

try:
    time.sleep(5)
    # if autoit.win_exists("開啟"):
    #     logging.error(f"檔名輸入錯誤或檔案不存在，輸入為{file_entered}")
    #     sys.exit(1)
    
    # else:
    upload_confirm = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, "//span[text()='取代']"))
    )
    upload_confirm.click()
    logging.info("成功上傳並取代舊檔")
    time.sleep(10)
    sys.exit(0)

except Exception as e:
    driver.save_screenshot(os.path.join(SAVE_DIR, f'log/{CURRENTDAY}_uploadError.png'))
    logging.error("擷取螢幕畫面")
    logging.error(f"開啟或取代檔案失敗: {e}")
    sys.exit(1)


