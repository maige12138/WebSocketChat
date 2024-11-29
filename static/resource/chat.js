function get_active_channel() {
  const channelList = document.querySelector('#channel-list');
  if (channelList) {
    const activeChannel = channelList.querySelector('.active');
    if (activeChannel) {
      return activeChannel.dataset.channel;
    }
  }
  return null;
}


document.addEventListener('DOMContentLoaded', () => {

  // 连接到flask后端服务器
  const socket = io();
  const friendListContainer = document.querySelector("#friend-list-container");
  
  // 监听连接事件
  socket.on('connect', () => {
    socket.emit('connection', socket.id);
  });

  // 监听在线用户数量
  socket.on('update_online_users', (data) => {
    const onlineUsersElement = document.querySelector('#online-users');
    if (onlineUsersElement) {
      onlineUsersElement.textContent = '当前在线人数：' + data.online_users;
    }
  });

  // 监听用户在线状态
  socket.on('update_online_status', (data) => {
    const userStatus = document.querySelector(`[id="online-status ${data.username}"]`);
    console.log(data);
    if (userStatus) {
      if (data.status === 'online') {
        userStatus.classList.remove('bg-danger');
        userStatus.classList.add('bg-success');
        userStatus.textContent = '在线';
      }
      else if (data.status === 'offline') {
        userStatus.classList.remove('bg-success');
        userStatus.classList.add('bg-danger');
        userStatus.textContent = '离线';
      }
    }
  });

  // 用户上线时更新好友列表
  socket.on('update_friendList', (data) => {
    const friendCount = document.querySelector('#friend-count');
    friendCount.textContent = data.friendCount;
    friendListContainer.innerHTML = '';
    data.friendList.forEach((item) => {
        const li = document.createElement('li');
        li.setAttribute("name", item);
        li.className = 'list-group-item d-flex justify-content-between align-items-center m-4';
        li.innerHTML =`
            <span class="float-start">${item}</span>
            <span class="badge bg-success rounded-pill float-end" id="online-status ${item}">在线</span>
        `;
        friendListContainer.appendChild(li);
    });
  });

  // 好友上线时更新好友列表
  socket.on("I'Online", (data) => {
    socket.emit('update_online_status', {username: data.friendName, userID: data.userID, status: 'online'});
  });


  // -----------实现监听服务器发送来的信息----------- //
  socket.on('message', (data) => {
    const li = document.createElement('li');
    li.className = 'list-group-item';
    li.innerHTML = `            
    <div class="card chat-message">
      <div class="card-header">
        <span class="sender font-weight-bold">${data.sender}: </span>
        <span class="timestamp text-muted float-end">${data.timestamp}</span>
      </div>
      <div class="card-body">
        <span class="message">${data.message}</span>
      </div> 
    </div>`;
    messageList.appendChild(li);
    messageList.scrollTop = messageList.scrollHeight;
  });
  socket.on('image', (data) => {
    const li = document.createElement('li');
    const uniqueId = `modal-${data.timestamp.replace(/[^0-9]/g, '')}`;
    li.className = 'list-group-item';
    li.innerHTML = `
        <div class="card chat-message">
          <div class="card-header">
            <span class="sender font-weight-bold">${data.sender}: </span>
            <span class="timestamp text-muted float-end">${data.timestamp}</span>
          </div>
          <div class="card-body text-center">
            <span class="message"><img src="../static/${data.dataUrl}" alt="" style="cursor:pointer;max-width:200px;" data-bs-toggle="modal" data-bs-target="#${uniqueId}" /></span>
          </div>
        </div>
        <div class="modal fade" id="${uniqueId}" tabindex="-1" aria-labelledby="${uniqueId}-label" aria-hidden="true">
          <div class="modal-dialog modal-dialog-centered modal-lg">
            <div class="modal-content">
              <div class="modal-body">
                <img src="../static/${data.dataUrl}" class="img-fluid" alt="" />
              </div>
            </div>
          </div>
        </div>`;
    messageList.appendChild(li);
    messageList.scrollButtom = messageList.scrollHeight;
  });

  // -----------实现监听服务器发送来的频道信息----------- //
  socket.on('renderMessage', (data) => {
    data.messages.forEach((item) => {
      const li = document.createElement('li');
      li.className = 'noshow';
      if (item.is_image === 1) {
        const uniqueId = `modal-${item.timestamp.replace(/[^0-9]/g, '')}`;
        li.innerHTML = `
        <div class="card chat-message">
          <div class="card-header">
            <span class="sender font-weight-bold">${item.sender}: </span>
            <span class="timestamp text-muted float-end">${item.timestamp}</span>
          </div>
          <div class="card-body text-center">
            <span class="message"><img src="../static/${item.image_path}" alt="" style="cursor:pointer;max-width:200px;" data-bs-toggle="modal" data-bs-target="#${uniqueId}" /></span>
          </div>
        </div>
        <div class="modal fade" id="${uniqueId}" tabindex="-1" aria-labelledby="${uniqueId}-label" aria-hidden="true">
          <div class="modal-dialog modal-dialog-centered modal-lg">
            <div class="modal-content">
              <div class="modal-body">
                <img src="../static/${item.image_path}" class="img-fluid" alt="" />
              </div>
            </div>
          </div>
        </div>`;
      } else {
        li.innerHTML = `
        <div class="card chat-message">
          <div class="card-header">
            <span class="sender font-weight-bold">${item.sender}: </span>
            <span class="timestamp text-muted float-end">${item.timestamp}</span>
          </div>
          <div class="card-body">
            <span class="message">${item.message}</span>
          </div>
        </div>`;
      }
      messageList.appendChild(li);
    });
    messageList.scrollTop = messageList.scrollHeight;
  });



  // -----------各类按钮的实现----------- //
  const sendBtn = document.getElementById('send-btn');
  const clearBtn = document.getElementById('clear-btn');
  const logoutBtn = document.getElementById('logout-btn');
  const messageInput = document.getElementById('message-input');
  const imageInput = document.getElementById('image-input');
  const messageList = document.querySelector('#message-list');
  
  // 发送按钮功能
  sendBtn.addEventListener('click', function(event) {
      event.preventDefault();
      
      const message = messageInput.value;
      const imageFile = imageInput.files[0];

      if (message != null && message != '')
        socket.emit('message', message);

      if (imageFile != null && imageFile != ''){
          const reader = new FileReader();
          reader.onload = () => {
            socket.emit('image', {dataUrl: reader.result, name: imageFile.name});
          };
          reader.readAsDataURL(imageFile);
      }

      // 清空输入框
      messageInput.value = '';
      imageInput.value = '';
  });
  
  // 清除按钮功能
  clearBtn.addEventListener('click', function(event) {
    event.preventDefault();
    // 清空消息列表
    messageList.innerHTML = '';
     // 清空输入框
    messageInput.value = '';
    imageInput.value = '';
     // 创建提示框
    const alertContainer = document.getElementById('alertContainer');
    const alertDiv = document.createElement('div');
    alertDiv.classList.add('alert', 'alert-success', 'alert-dismissible', 'fade', 'show');
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
      <strong>清除成功！</strong>
    `;
    alertContainer.appendChild(alertDiv);
    setTimeout(() => {alertContainer.innerHTML='';}, 1000);
  });
  
  // 登出按钮功能
  logoutBtn.addEventListener('click', function(event) {
      event.preventDefault();
  
      // 在此处处理登出的逻辑，例如重定向到登出页面
      console.log('用户登出');
      window.location.href = '/logout'; // 请根据实际情况修改登出URL
  });

  // -----------实现点击在线人数时显示模态框----------- //
  const userList = document.querySelector('#userList');

  // 监听 'show.bs.modal' 事件，当 #userList 元素显示时触发
  userList.addEventListener('show.bs.modal', () => {
    socket.emit('get_online_users');
    socket.on('userList', (data) => {
      const list = userList.querySelector('ul');
      list.innerHTML = '';
      data.users_list.forEach(user => {
        const li = document.createElement('li');
        li.className = 'list-group-item d-flex justify-content-between align-items-center';
        
        const userName = document.createElement('span');
        userName.textContent = user;
        li.appendChild(userName);
        
        // 实现加好友的按钮
        const addButton = document.createElement('button');
        addButton.className = 'btn btn-primary btn-sm';
        addButton.textContent = '加好友';
        addButton.addEventListener('click', () => {
          socket.emit('add_friend', user);
          socket.on('add_friend', (data) => {
            if (data.status === 'success') {
              const friendItem = document.createElement('li');
              addButton.textContent = '已添加';
              addButton.disabled = true;
              friendItem.className = 'list-group-item d-flex justify-content-between align-items-center';
              friendItem.innerHTML =`
                <span class="float-start">${user}</span>
                <span class="badge bg-success rounded-pill float-end" id="online-status ${user}">在线</span>
              `;
              friendListContainer.appendChild(friendItem);
            }
            else if (data.status === 'failed'){
              alert('添加好友失败');
            }
          })
        });
        li.appendChild(addButton);
  
        list.appendChild(li);
      });
    });
  });  
  userList.addEventListener('hide.bs.modal', () => {
    const list = userList.querySelector('ul');
    list.innerHTML = '<div class="spinner-border spinner-border-md text-success"></div>';
  });
});

