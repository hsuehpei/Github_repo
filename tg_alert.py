import requests
from datetime import datetime
import os
import sys
import re
import logging

CURRENTDAY = datetime.now().strftime("%Y%m%d")
# LOG_FILE = f"C:/Users/admin/Desktop/OPO/Github_fork/history_file/log/github_fork_{CURRENTDAY}.log"

def send_msg(logfile, token="7593431181:AAH--Rj_4njknzxJtAr5j_b0CyrlPWpZPqE", chatID="-1002472057533"): # -4276625396 data  # -1002472057533 meeee
    with open(logfile, mode="rt", encoding='utf-8') as inpf:
        latest = None
        log_lines = inpf.readlines()

        for i, line in enumerate(reversed(log_lines)):
            match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} -', line)
            if match:
                latest = len(log_lines) - i - 1
                break

    msg = log_lines[latest][33:]
    url = f'https://api.telegram.org/bot{token}/sendMessage?chat_id={chatID}&text={msg}'
    requests.get(url)
    logging.info(f"訊息({msg[:-1]})發送成功")

if __name__ == "__main__":
    logfile = sys.argv[1]
    logging.basicConfig(filename=logfile, level=logging.INFO,encoding='utf-8',
                    format='%(asctime)s - %(levelname)s - %(message)s')

    send_msg(logfile)
