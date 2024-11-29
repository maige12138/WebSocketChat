from flask import Flask, render_template, redirect, url_for, jsonify, session, request, g
from flask_socketio import SocketIO, emit
from collections import defaultdict
from static.function import user
from datetime import datetime
import sqlite3, base64, uuid, os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

users_list = {'Channel 1': {}, 'Channel 2': {}, 'Channel 3': {}}
online_users = defaultdict(int)

# 创建数据库连接
conn = sqlite3.connect('messages.sqlite3', check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS messages (\
            id INTEGER PRIMARY KEY AUTOINCREMENT, \
            channel TEXT NOT NULL, \
            sender TEXT NOT NULL, \
            message TEXT NOT NULL, \
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, \
            is_image TEXT NOT NULL, \
            image_path TEXT NOT NULL, \
            image_type TEXT NOT NULL)")
conn.commit()

# 获取数据库连接
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('messages.sqlite3', check_same_thread=False)
        g.db.row_factory = sqlite3.Row
    return g.db

# 关闭数据库连接
@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'db'):
        g.db.close()

# 获取当前活动的频道
def get_active_channel():
    return session.get('active_channel', 'Channel 1')

# 获取指定频道的聊天历史记录
def get_messages_for_channel(channel):
    rows = get_db().execute("SELECT sender, message, timestamp, channel, is_image, image_path FROM messages WHERE channel = ? ORDER BY timestamp", (channel,)).fetchall()
    messages = [{'sender': row[0], 'message': row[1], 'timestamp': row[2], 'channel': row[3], 'is_image': row[4], 'image_path': row[5]} for row in rows]
    return messages

# 登录页面
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # 获取提交的用户名和密码
        username = request.form['login-username']
        password = request.form['login-password']

        # 在这里添加登录逻辑，根据数据库检查用户的用户名和密码。
        if user.login(username, password):
            session['username'] = username
            session['logged_in'] = True
            session.permanent = True
            session['active_channel'] = 'Channel 1'
            return redirect(url_for('index'))
        else:
            # 如果验证失败，向用户显示一条错误消息
            error="用户名或密码错误"
            return render_template("login.html", error=error)

    return render_template("login.html")

# 注册页面
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # 获取提交的用户名和密码
        username = request.form['register-username']
        password = request.form['register-password']

        # 在这里添加注册逻辑，将用户的用户名和密码存储到数据库中。
        if user.register(username, password):
            session['username'] = username
            session['logged_in'] = True
            session.permanent = True
            session['active_channel'] = 'Channel 1'
            return redirect(url_for('index'))
        else:
            # 如果验证失败，向用户显示一条错误消息
            error="用户名已存在"
            return render_template("login.html", error=error)

# 注销页面
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('login'))

# 主页
@app.route('/', methods=['GET', 'POST'])
def index():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))

    username = session.get('username')
    if username is None:
        return redirect(url_for('login'))
    
    current_channel = get_active_channel()

    return render_template("index.html", username=username, current_channel=current_channel)

# 服务端接收客户端消息
@socketio.on('message')
def handle_message(message):
    print('received message: ' + message)
    channel = get_active_channel()
    sender = session.get('username', 'Anonymous')
    timestamp = datetime.now().strftime('%m-%d %H:%M:%S')
    db = get_db()
    db.execute("INSERT INTO messages (channel, sender, message, timestamp) VALUES (?, ?, ?, ?)", (channel, sender, message, timestamp))
    db.commit()
    emit('message', {'sender': sender, 'message': message, 'timestamp': timestamp}, broadcast=True)

    # 更新会话中的 active_channel 键
    if 'active_channel' in session:
        session['active_channel'] = channel
    else:
        session['active_channel'] = 'Channel 1'

# 服务端接收客户端图片
@socketio.on('image')
def handle_image(image_data):
    
    # 提示服务端接收到图片
    print('received image')
    channel = get_active_channel()
    sender = session.get('username', 'Anonymous')
    timestamp = datetime.now().strftime('%m-%d %H:%M:%S')  # 获取当前时间戳
    image_name = str(uuid.uuid4()) + '_' + timestamp.replace(' ', '_').replace(':', '') + os.path.splitext(image_data['name'])[1]
    image_type = image_name.split('.')[-1]
    image_data = image_data['dataUrl'].split(',')[1]
    
    
    with open(f'static/uploads/{image_name}', 'wb') as f:
        f.write(base64.b64decode(image_data))
    db = get_db()
    db.execute("INSERT INTO messages (channel, sender, message, timestamp, is_image, image_path, image_type) VALUES (?, ?, ?, ?, ?, ?, ?)", (channel, sender, '', timestamp, 1, f'uploads/{image_name}', image_type))
    db.commit()
    emit('image', {'sender': sender, 'timestamp': timestamp,'dataUrl': f'uploads/{image_name}', 'name': image_name}, broadcast=True)

# 显示聊天室在线用户
# 当有用户连接或断开连接时，更新在线用户列表，向当前用户发送聊天记录
@socketio.on('connection')
def on_connect(userId):
    channel = session.get('active_channel')
    if channel:
        username = session.get('username', 'Anonymous')
        messages = get_messages_for_channel(channel)
        friendList, friend_count = user.getFriendList(username)

        if username not in users_list[channel]:
            online_users[channel] += 1
            users_list[channel][username] = userId

        print("\n"+"*"*30)
        print("users: {} joined {}".format(username, channel))
        print("{} Online users: {}".format(channel, online_users[channel]))
        print("{} Users list: {}".format(channel, users_list[channel]))

        emit('renderMessage', {'messages': messages})
        emit('update_online_users', {'online_users': online_users[channel]}, broadcast=True)
        emit('update_online_status',{'username': username,'status': 'online'}, broadcast=True)
        emit('update_friendList',{'friendList': friendList,'friendCount': friend_count})

        # 当前用户上线时，向所有好友发出一个信息，检测哪些好友在线，如果在线则向当前用户发送上线通知
        if friendList is not None:
          for friend in friendList[0]:
            if friend in users_list[channel].keys():
              emit("I'Online",{'friendName': friend, 'userID': userId},room=users_list[channel][friend])
            else :
              emit('update_online_status',{'username': friend,'status': 'offline'})


@socketio.on('disconnect')
def on_disconnect():
    channel = session.get('active_channel')
    if channel:
        username = session.get('username', 'Anonymous')
        if username in users_list[channel]:
            online_users[channel] -= 1
            del users_list[channel][username]

        print("\n"+"*"*30)
        print("users: {} left {}".format(username, channel))
        print("{} Online users: {}".format(channel, online_users[channel]))
        print("{} Users list: {}".format(channel, users_list[channel]))

        emit('update_online_users', {'online_users': online_users[channel]}, broadcast=True)
        emit('update_online_status',{'username': username,'status': 'offline'}, broadcast=True)

# 返回当前在线用户
@socketio.on('get_online_users')
def get_online_users():
    channel = session.get('active_channel')
    if channel:
        emit('userList', {'users_list': list(users_list[channel].keys())})

# 实现加好友功能
@socketio.on('add_friend')
def add_friend(friend):
    username = session.get('username', 'Anonymous')
    friendList, friend_count = user.add_friend(username, friend)
    if friend_count: 
        emit('add_friend', {'status': 'success', 'friend_count': friend_count, 'friendList': friendList})
        # emit('update_friendList',{'friendList': friendList,'friendCount': friend_count})
        emit('update_friendList',{'friendList': [username],'friendCount': friend_count},room=users_list[session['active_channel']][friend])
    else: 
        emit('add_friend', {'status': 'failed'})

@socketio.on("update_online_status")
def update_online_status(data):
    emit("update_online_status", data, room=data['userID'])

# 实现频道切换功能
@app.route('/channel/<channel_name>')
def set_active_channel(channel_name):
  session['active_channel'] = channel_name
  messages = get_messages_for_channel(channel_name)
  return render_template('index.html', username=session['username'], messages=messages, current_channel = channel_name)

if __name__ == '__main__':
    print('http://127.0.0.1:5000')
    socketio.run(app, debug=False, host='0.0.0.0', port=5000)