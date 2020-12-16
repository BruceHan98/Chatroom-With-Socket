import select
import threading
import logging
from ui.login import *
from ui.chatroom import *


IP = '127.0.0.1'
PORT = 1234
BUFFER_SIZE = 4096

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', level=logging.INFO)


def receive():
    while True:
        # 开始select 监听, 对input_list 中的服务器端server 进行监听
        readable, writable, exceptional = select.select([sock], [], [])

        # 循环判断是否有客户端连接进来, 当有客户端连接进来时select将触发
        # s是client的socket，sendall发送c_开头的请求
        for s in readable:
            data = s.recv(BUFFER_SIZE)

            if data == '':
                continue

            splt = data.decode('utf-8').split('\r\r')
            # print(splt)
            if splt[0] == '':
                continue
            header = int(splt[0])
            # 在线用户
            if header == s_online_users:
                username_list = splt[1].split('\t')
                for username in username_list:
                    if username != '':
                        # print(username)
                        ui_chat.ADD_BOX.emit(str(username))
            # 有客户端登出
            elif header == s_logout:
                username = splt[1]
                logging.info(f'{username} has logged out')
                ui_chat.APPEND.emit(f"<font color='red'> {username} 下线了")
                ui_chat.DEL_BOX.emit(username)
            # 账号密码错误
            elif header == s_password_wrong:
                ui_login.PASSWORD_WRONG.emit()
                logging.info('Wrong password')
            # 重复登录
            elif header == s_login_repeat:
                ui_login.LOGIN_REPEAT.emit()
                logging.warning('You have already logged in')
            # 登录成功
            elif header == s_login_success:
                ui_login.CLOSE.emit()
                logging.info('Login success')
                username = splt[1]
                # print(username)
                ui_chat.SHOW.emit()
                ui_chat.WELCOME.emit(username)
                s.sendall(str(c_get_online_users).encode('utf-8'))
            # 注册成功
            elif header == s_register_success:
                ui_login.REGISTER_SUCCESS.emit()
                logging.info('Register success')
            # 重复注册
            elif header == s_register_repeat:
                ui_login.REGISTER_REPEAT.emit()
                logging.info('Repeat registering')
            # 新用户登录
            elif header == s_new_login:
                username = splt[1]
                logging.info(f'{username} has logged in')
                ui_chat.APPEND.emit(f"<font color='red'> {username} 上线了")
                ui_chat.ADD_BOX.emit(username)
            # 接收文件
            elif header == s_send_file:  # 由服务端发来文件
                raw_data = splt[1]  # 服务端发来文件格式：header + \r\r + raw_data
                file_name, data = raw_data.split('\t')  # 这里是 utf-8 编码
                # print("data type:", type(data))
                # print("file_name type:", type(file_name))
                ui_chat.REV_FILE.emit(str(file_name), bytes(data, encoding='utf-8'))
                continue
            # 接受消息
            elif header == s_send_msg:  # 服务端发来文件格式：header + sender + msg
                sender = splt[1]
                msg = splt[2]
                data = sender + '\r\r' + msg  # 发个ui的数据格式
                ui_chat.REVMSG.emit(data)  # 注意这里传入的格式

            else:
                logging.error('Receiving error')


if __name__ == '__main__':
    sock = socket.socket()  # 客户端的socket
    try:
        sock.connect((IP, PORT))
        logging.info(f'Connected to server {IP}:{PORT}')
    except Exception as e:
        logging.error("Fail to connect (%s, %s) due to" % (IP, PORT), e)
        sock.close()
        sys.exit()
        exit()

    app = QApplication(sys.argv)

    login_get_sock(sock)
    ui_login = LoginWindow()

    # ui_chat = ChatWindow(sock)
    ui_chat = ChatRoom(sock)

    listen = threading.Thread(target=receive, args=(), daemon=True)
    listen.start()

    ui_login.show()
    app.exec_()

    if Exception:
        sock.close()
        sys.exit()
