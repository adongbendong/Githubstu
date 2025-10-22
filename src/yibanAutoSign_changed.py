"""
new Env(易班自动签到)
cron: 59 20 * * *
"""

import os
import sys
import threading
import time

from serverChan import ServerChan
from userData import user_data
from yiban import Yiban

count = 3
LOG_FILE = 'yibanAutoSign.log'


def write_log(text: str):
    """将日志写入本地文件"""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        timestamp = time.strftime("[%Y-%m-%d %H:%M:%S] ", time.localtime())
        f.write(f"{timestamp}{text}\n")

def start_sign(user: dict):
    server_chan = ServerChan("易班签到详情", user["SendKey"])
    for i in range(count):
        yb = Yiban(user["Phone"], user["PassWord"])
        try:
            time_range = yb.task_feedback.get_sign_task()
        except Exception as e:
            error_msg = f"{user['Phone']} 出现错误, 尝试重新启动流程({i + 1}/{count})，错误信息：{e}"
            print(error_msg)
            write_log(error_msg)
            time.sleep(2)
            continue
        while not time_range["StartTime"] < time.time() < time_range["EndTime"]:
            time.sleep(1)
        try:
            back = yb.submit_sign_feedback(user["Address"])
            message = f'{user["Phone"]}: {back}'
            server_chan.log(message).send_msg()
            write_log(message)
        except Exception as e:
            error_msg = f"{user['Phone']} 签到提交失败：{e}"
            print(error_msg)
            write_log(error_msg)
        return

        retry_msg = f'{user["Phone"]} 重试机会使用完'
        server_chan.log(retry_msg).send_msg()
        write_log(retry_msg)


DEBUG = True if sys.gettrace() else False

if __name__ == "__main__":
    env = os.getenv("skip")
    if env is not None:
        env = env.split(",")
    else:
        env = ""

    for user in user_data:
        if user["Phone"] in env or not user.get("enable", True):
            skip_msg = f'用户 {user["Phone"]} 在跳过列表'
            print(skip_msg)
            write_log(skip_msg)
            continue
        if DEBUG:
            start_sign(user)
        else:
            threading.Thread(target=start_sign, args=(user,)).start()
