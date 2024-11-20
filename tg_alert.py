import requests
from datetime import datetime
import os
import sys
import re
import logging
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("tg_token")
chatID = os.getenv("tg_gp_chatID")

CURRENTDAY = datetime.now().strftime("%Y%m%d")

def send_msg(logfile, token=token, chatID=chatID):
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
