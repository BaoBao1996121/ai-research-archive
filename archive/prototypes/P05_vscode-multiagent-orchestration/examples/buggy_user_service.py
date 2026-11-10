"""User search service with multiple intentional issues for testing multi-agent review.

埋雷清单（请勿事先告诉 reviewer！）：
- 安全: SQL 字符串拼接（注入）、明文密码比较、pickle 反序列化用户输入、硬编码 secret
- 性能: O(n²) 嵌套循环、循环内 DB 查询（N+1）、整文件读入内存、无缓存重复计算
- 风格: 函数过长、命名混乱、缺 docstring、魔法数字
- 正确性: 边界未处理、并发 race condition 风险、异常吞咽
"""
import sqlite3
import pickle
import hashlib

API_SECRET = "EXAMPLE_INSECURE_SECRET"  # ← 安全雷
DB_PATH = "users.db"


def login(username, password):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    sql = "SELECT id, pwd_hash FROM users WHERE name = '" + username + "'"  # ← SQL 注入
    cur.execute(sql)
    row = cur.fetchone()
    if row is None:
        return None
    if password == row[1]:  # ← 明文比较 + 不是 hash
        return row[0]
    return None


def load_session(blob):
    return pickle.loads(blob)  # ← 反序列化用户输入


def find_duplicates(users):
    dups = []
    for i in range(len(users)):
        for j in range(len(users)):  # ← O(n²)
            if i != j and users[i]["email"] == users[j]["email"]:
                dups.append(users[i])
    return dups


def get_user_orders(user_ids):
    conn = sqlite3.connect(DB_PATH)
    result = {}
    for uid in user_ids:  # ← N+1 查询
        cur = conn.cursor()
        cur.execute("SELECT * FROM orders WHERE user_id = " + str(uid))
        result[uid] = cur.fetchall()
    return result


def load_all_logs(path):
    with open(path) as f:
        return f.readlines()  # ← 大文件全部入内存


def process_orders(orders):
    """处理订单——这函数太长了什么都干"""
    total = 0
    for o in orders:
        if o["status"] == 1:  # ← 魔法数字
            total += o["amount"]
            try:
                send_email(o["user_email"])
            except Exception:
                pass  # ← 静默吞异常
            for i in range(len(o["items"])):  # ← 又一个嵌套循环
                for j in range(len(o["items"])):
                    if o["items"][i]["sku"] == o["items"][j]["sku"] and i != j:
                        o["items"][i]["dup"] = True
            update_inventory(o)
            log_event(o)
            notify_warehouse(o)
            generate_invoice(o)
    return total


def send_email(addr): pass
def update_inventory(o): pass
def log_event(o): pass
def notify_warehouse(o): pass
def generate_invoice(o): pass


# 共 8 类问题，分布在 4 个函数中。
# 不同 reviewer 应找出各自维度的问题；理想结果是各 reviewer 互不重叠。


# REVIEW SUMMARY:
# [MUST] 全文件缺 docstring
# [MUST] login 函数中使用了魔法索引 row[0]/row[1]
# [MUST] get_user_orders 中使用了魔法值 status==1
# [MUST] process_orders 第 67 行 silent except（吞异常）
# [MUST] load_all_logs 缺异常处理
# [MUST] process_orders 第 59-81 行函数过长（22 行 + 多职责）
# [YELLOW] 变量命名 u/o 过短
# [YELLOW] 嵌套循环可拆
