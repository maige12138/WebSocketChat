import sqlite3

# 登录用户
def login(username, password):
    conn = sqlite3.connect('./mydb.sqlite3')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()

    conn.close()

    if user:
        return True
    else:
        return False

# 注册用户
def register(username, password):
    conn = sqlite3.connect('mydb.sqlite3')
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()

    cursor.execute("INSERT INTO friends (username, friend_count) VALUES (?, ?)", (username, 0))

    if result[0] > 0:
        # 用户名已经存在
        conn.close()
        return False

    # 如果用户名不存在，将新用户的用户名和密码存储在数据库中。
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    conn.close()
    return True

# 获取当前用户的ID
def get_current_user_id(username):
    conn = sqlite3.connect('mydb.sqlite3')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    user_id = cursor.fetchone()[0]
    print(user_id)
    conn.close()
    return user_id

# 实现添加好友的功能
def add_friend(username, friendname):
    conn = sqlite3.connect('mydb.sqlite3')
    cursor = conn.cursor()

    # 检查用户名是否存在或者好友是否已经存在
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    cursor.execute("SELECT COUNT(*) FROM friend_details WHERE username = ? and friend_name = ?", (username, friendname))
    result2 = cursor.fetchone()
    if result[0] == 0 or result2[0] > 0:
        # 用户名不存在
        conn.close()
        return False, False
    else:
        # 如果用户名存在或还未加好友，将新好友存在双方的数据库中。
        cursor.execute("INSERT INTO friend_details (username, friend_name) VALUES (?, ?)", (username, friendname))
        cursor.execute("INSERT INTO friend_details (username, friend_name) VALUES (?, ?)", (friendname, username))

        # 更新对方的好友数量
        cursor.execute("SELECT COUNT(*) FROM friend_details WHERE username = ?", (friendname,))
        friend_count = cursor.fetchone()[0]
        cursor.execute('UPDATE friends SET friend_count = ? WHERE username = ?', (friend_count, friendname))

        # 获取当前用户的好友数量和好友列表
        cursor.execute("SELECT COUNT(*) FROM friend_details WHERE username = ?", (username,))
        friend_count = cursor.fetchone()[0]
        cursor.execute("SELECT friend_name FROM friend_details where username = ?", (username,))
        friendList = list(cursor.fetchall())

        # 更新好友数量
        cursor.execute("UPDATE friends SET friend_count = ? WHERE username = ?", (friend_count, username))

        conn.commit()
        conn.close()
        return friendList, friend_count

# 获取好友列表
def getFriendList(username):
    conn = sqlite3.connect('mydb.sqlite3')
    cursor = conn.cursor()

    # 获取当前用户的好友数量和好友列表
    cursor.execute("SELECT COUNT(*) FROM friend_details WHERE username = ?", (username,))
    friend_count = cursor.fetchone()[0]
    cursor.execute("SELECT friend_name FROM friend_details where username = ?", (username,))
    friendList = list(cursor.fetchall())

    conn.close()
    return friendList, friend_count
