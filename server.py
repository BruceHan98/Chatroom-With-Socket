import os
import socket
import sqlite3
import select
import sys
from utils.header import *
import logging

IP = '127.0.0.1'
PORT = 1234
BUFFER_SIZE = 4096

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', level=logging.INFO)


# s发送给所有其他的socket
def send_to_others(s, data):
    for c in connections:
        if c != sock and c != s:  # 除了服务端和发送者
            c.sendall(data.encode('utf-8'))


# 对client发来的data进行处理，s是client的socket
def handle(s, data):
    """
    定义data结构:
    0. header
    1. users to be send
    2. data

    数据用 utf-8 编码
    每个部分用'\r\r'隔开，每个部分中不同元素用'\t'隔开
    """
    if data == '':
        return

    # 从客户端收到的数据信息
    splt = data.decode('utf-8').split('\r\r')
    # print(splt)

    # 要确保传来的信息都有header
    if splt[0] == '':
        return
    header = int(splt[0])

    # 获取在线用户 header
    if header == c_get_online_users:
        logging.info('Get online users...')
        ol_user = ''
        for co in users.keys():
            if users[co] != users[s]:
                ol_user = ol_user + users[co] + '\t'
        send_data = str(s_online_users) + '\r\r' + ol_user
        logging.info(ol_user)
        s.sendall(send_data.encode('utf-8'))
    # 客户端登出 header
    elif header == c_logout:
        logging.info('User logging out...')
        out_user = users[s]
        msg = str(s_logout) + '\r\r' + str(out_user)
        send_to_others(s, msg)
        connections.remove(s)
        # users[s] = None
        # connects[out_user] = None
        del users[s]
        del connects[out_user]
    # 客户端登录 header
    elif header == c_login:
        # 在数据库中查找user
        cursor.execute("select * from user where username = '{0}' and password = '{1}'".format(splt[1], splt[2]))
        user = cursor.fetchone()
        if user is None:
            # 账号密码错误
            s.sendall(str(s_password_wrong).encode('utf-8'))
            logging.warning('Wrong password')
        elif user[0] in connects.keys():
            # 用户已经登陆了
            s.sendall(str(s_login_repeat).encode('utf-8'))
            logging.warning('Already logged in')
        else:
            # 登录成功
            connects[user[0]] = s
            users[s] = user[0]
            # 给这个socket发送login_success
            s.sendall((str(s_login_success) + '\r\r' + user[0]).encode('utf-8'))
            logging.info(f"[{user[0]}] has logged in")
            # s向其他socket发送新登录的用户名
            send_to_others(s, str(s_new_login) + '\r\r' + str(user[0]))
            logging.info('New login send to others')
    # 注册 header
    elif header == c_register:
        cursor.execute("select * from user where username = '{0}'".format(splt[1]))
        user = cursor.fetchone()
        if user is None:
            cursor.execute("insert into user (username, password) values ('{0}', '{1}')".format(splt[1], splt[2]))
            db.commit()
            # 注册成功
            s.sendall(str(s_register_success).encode('utf-8'))
        else:
            s.sendall(str(s_register_repeat).encode('utf-8'))
    # 发送文件 header \r\r usernames \r\r data
    elif header == c_send_file:
        logging.info('Sending file...')
        sender = users[s]  # sender是发消息的客户端
        username_list = splt[1].split('\t')
        user_list = []
        for user in username_list:
            if user != '':
                user_list.append(user)
        raw_data = ''
        for i in splt[2:]:
            raw_data = raw_data + i + '\r\r'
        # print(raw_data)
        logging.info(f'{sender} is sending file to {user_list}')
        file_data = str(s_send_file) + '\r\r' + raw_data  # 文件内容包括文件名和文件数据，中间用\t隔开
        for user in user_list:
            rev = connects[user]
            if rev is not None:
                rev.sendall(file_data.encode('utf-8'))
        logging.info('Sending file complete')
        return
    # 发送消息 header \r\r usernames \r\r msg
    elif header == c_send_msg:
        sender = users[s]  # sender是发消息的客户端
        username_list = splt[1].split('\t')
        user_list = []
        for user in username_list:
            if user != '':
                user_list.append(user)
        msg = splt[2]
        logging.info(f'{sender} is sending message to {user_list}')
        msg = (str(s_send_msg) + '\r\r' + sender + '\r\r' + msg).encode('utf-8')  # 发送给client的格式
        for user in user_list:
            # print(user)
            rev = connects[user]
            if rev is not None:
                rev.sendall(msg)
        logging.info('Sending message complete')


if __name__ == '__main__':
    # 连接数据库，没有会自动创建文件
    if not os.path.exists("utils/info.db"):
        conn = sqlite3.connect("utils/info.db")
        c = conn.cursor()
        c.execute('CREATE TABLE user(username TEXT PRIMARY KEY NOT NULL, password TEXT)')
        conn.commit()
        conn.close()
        logging.info("Create user database success")

    db = sqlite3.connect('utils/info.db')
    cursor = db.cursor()
    db.commit()

    # 初始化socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # IPv4, TCP
    sock.bind((IP, PORT))
    sock.listen(5)
    logging.info(f"Server connected on {IP}:{PORT}")

    # 所有socket
    connections = [sock]

    # Sockets to which we expect to write
    outputs = []

    users = {}  # 记录在线的客户端的套接字, username: socket
    connects = {}  # 将聊天双方的套接字绑定在一起，可以从user得到socket

    while True:
        # 开始select监听, 对input_list中的服务器端server进行监听
        # select函数阻塞程序运行, 监控inputs中的套接字, 直到inputs中的套接字被触发，一旦调用socket的send, recv函数，将会再次调用此模块
        readable, writable, exceptional = select.select(connections, outputs, [])
        """
        readable: 接收外部发来的数据，监听服务端的套接字
        writable: 处理要发出去的数据，监听可写的套接字
        exceptional: 监听异常
        """
        # 循环判断是否有客户端连接进来, 当有客户端连接进来时select将触发
        for s in readable:
            # 有新用户连接到server
            if s == sock:
                conn, client_address = s.accept()  # 接受TCP连接并返回（conn,address）,其中conn是新的套接字对象，可以用来接收和发送数据
                # print(conn, client_address)
                connections.append(conn)  # 将客户端对象也加入到监听的列表中, 当客户端发送消息时 select 将触发
                users[conn] = None
            # 老用户发来信息，需要处理
            else:  # 客户端对象触发
                data = s.recv(BUFFER_SIZE)
                handle(s, data)

        # 处理异常的情况
        for s in exceptional:
            logging.error('Exception condition on', s.getpeername())
            # Stop listening for input on the connection
            connections.remove(s)
            if s in outputs:
                outputs.remove(s)

        # print(len(connections))
        # print(len(users))
        # if len(connections) == 1 or len(users) < 1:
        #     logging.warning("No client exists, server closed")
        #     sock.close()
        #     sys.exit()
