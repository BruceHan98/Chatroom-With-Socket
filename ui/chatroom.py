# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'chatroom.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!
import socket
import os

from utils.header import *
from PyQt5 import QtCore, QtGui, QtWidgets
import ctypes
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("myappid")


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(828, 600)
        self.setWindowIcon(QtGui.QIcon('ui/logo.png'))
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        self.listWidget = QtWidgets.QListWidget(self.centralwidget)
        self.listWidget.setGeometry(QtCore.QRect(50, 70, 171, 471))
        self.listWidget.setObjectName("listWidget")
        self.listWidget.addItem(" --- 在线用户 --- ")
        self.listWidget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.textEdit = QtWidgets.QTextEdit(self.centralwidget)
        self.textEdit.setGeometry(QtCore.QRect(250, 460, 431, 81))
        self.textEdit.setObjectName("textEdit")

        self.textBrowser = QtWidgets.QTextBrowser(self.centralwidget)
        self.textBrowser.setGeometry(QtCore.QRect(250, 70, 531, 371))
        self.textBrowser.setObjectName("textBrowser")

        self.sendmsg = QtWidgets.QPushButton(self.centralwidget)
        self.sendmsg.setGeometry(QtCore.QRect(690, 460, 91, 34))
        self.sendmsg.setObjectName("sendmsg")

        self.sendfile = QtWidgets.QPushButton(self.centralwidget)
        self.sendfile.setGeometry(QtCore.QRect(690, 510, 91, 34))
        self.sendfile.setObjectName("sendfile")

        self.logout = QtWidgets.QPushButton(self.centralwidget)
        self.logout.setGeometry(QtCore.QRect(701, 30, 81, 34))
        self.logout.setObjectName("logout")

        self.welcome_label = QtWidgets.QLabel(self.centralwidget)
        self.welcome_label.setGeometry(QtCore.QRect(50, 25, 120, 40))
        self.welcome_label.setObjectName("welcome_label")

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "ChatRoom"))
        self.sendmsg.setText(_translate("MainWindow", "发送"))
        self.sendfile.setText(_translate("MainWindow", "发送文件"))
        self.logout.setText(_translate("MainWindow", "登出"))
        self.welcome_label.setText(_translate("MainWindow", "欢迎你"))


class ChatRoom(QtWidgets.QMainWindow, Ui_MainWindow):
    ADD_BOX = QtCore.pyqtSignal(str)
    DEL_BOX = QtCore.pyqtSignal(str)
    WELCOME = QtCore.pyqtSignal(str)
    REVMSG = QtCore.pyqtSignal(str)
    APPEND = QtCore.pyqtSignal(str)
    REV_FILE = QtCore.pyqtSignal(str, bytes)
    SHOW = QtCore.pyqtSignal()

    def __init__(self, sock, parent=None):
        super(ChatRoom, self).__init__(parent)
        self.setupUi(self)
        self.sock = sock

        self.WELCOME.connect(self.welcome)
        self.REVMSG.connect(self.rev_msg)
        self.SHOW.connect(self.show)
        self.APPEND.connect(self.append)
        self.REV_FILE.connect(self.rev_file)
        self.ADD_BOX.connect(self.new_login)
        self.DEL_BOX.connect(self.new_logout)

        self.logout.pressed.connect(self.log_out)
        self.sendmsg.pressed.connect(self.send_msg)
        self.sendfile.pressed.connect(self.send_file)

        self.listWidget.clicked.connect(self.clicked)
        self.listWidget.doubleClicked.connect(self.double_clicked)
        self.selected_users = []
        self.is_double_clicked = False

        self.textEdit.textChanged.connect(self.text_changed)

    # 欢迎登录
    def welcome(self, username):
        _translate = QtCore.QCoreApplication.translate
        self.welcome_label.setText(_translate("MainWindow", str("你好," + username)))
        self.setWindowTitle(_translate("MainWindow", str(username)))

    # 好友上线
    def new_login(self, username):
        self.listWidget.addItem(username)

    # 好友下线
    def new_logout(self, username):
        print("处理好友下线")
        item = self.listWidget.findItems(username, QtCore.Qt.MatchExactly)
        if len(item) > 0:
            # print(item[0].text())
            self.listWidget.removeItemWidget(item[0])
            row = item[0].listWidget().row(item[0])
            # print(row)
            self.listWidget.takeItem(row)

    def clicked(self):
        if not self.is_double_clicked:
            QtCore.QTimer.singleShot(300, self.item_clicked_timeout)

    def item_clicked_timeout(self):
        if not self.is_double_clicked:
            for item in self.listWidget.selectedItems():
                self.selected_users.append(item.text())
                item.setBackground(QtGui.QColor(135, 206, 250, 255))
            pass
        else:
            self.is_double_clicked = False

    def double_clicked(self):
        self.is_double_clicked = True
        for item in self.listWidget.selectedItems():
            item.setBackground(QtGui.QColor('white'))
            if item.text() in self.selected_users:
                self.selected_users.remove(item.text())

    # 发送文件
    def send_file(self):
        file_path = QtWidgets.QFileDialog.getOpenFileName(self, '选择文件', '')
        file_name = os.path.basename(file_path[0])
        print(file_path)
        header = str(c_send_file)

        usernames = ''
        for user in self.selected_users:
            usernames = usernames + user + '\t'

        f = open(file_path[0], "rb")
        data = f.read()

        raw_data = file_name + '\t' + data.decode('utf-8', "ignore")
        send_data = header + '\r\r' + usernames + '\r\r' + raw_data
        self.sock.sendall(bytes(send_data, encoding='utf-8'))  # 发送给服务端处理 .encode('utf-8')
        self.APPEND.emit(f"<font color='orange'> 文件已发送:\n {file_name}")
        self.textEdit.clear()

    # 接收文件
    def rev_file(self, filename, file):
        reply = QtWidgets.QMessageBox.question(self, "文件", "\n是否要接收文件？", QtWidgets.QMessageBox.No |
                                               QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            f = open(filename, "wb+")
            f.write(file)
            f.close()
            QtWidgets.QMessageBox.information(self, "成功", "\n已存储为{}".format(filename), QtWidgets.QMessageBox.Ok)
            self.APPEND.emit(f"<font color='orange'> 接收到文件:\n {filename}")

    # 登出
    def log_out(self):
        self.sock.sendall(str(c_logout).encode('utf-8'))
        self.close()

    # 显示消息
    def append(self, msg):
        self.textBrowser.append(msg)

    def text_changed(self):
        msg = self.textEdit.toPlainText()
        if '\n' in msg:
            msg = msg.replace('\n', '')  # 将文本框的\n清除掉
            self.textEdit.setText(msg)  # 将处理后的内容重新放入文本框
            self.send_msg()

    # 发送消息
    def send_msg(self):
        send_data = str(c_send_msg)
        msg = self.textEdit.toPlainText()
        if msg == '':  # 避免发送空消息
            msg = ' '
        usernames = ''
        if len(self.selected_users) == 0:
            error_dialog = QtWidgets.QMessageBox.warning(self, '确认', '你还没有选择好友！')
            return
        for user in self.selected_users:
            usernames = usernames + user + '\t'
        send_data = send_data + '\r\r' + usernames + '\r\r' + msg
        self.sock.sendall(send_data.encode('utf-8'))
        self.textBrowser.append("<font color='green'>" + "我: " + "<font>" + msg)
        self.textBrowser.moveCursor(self.textBrowser.textCursor().End)  # 文本框显示到底部
        self.textEdit.clear()

    # 接受消息
    def rev_msg(self, msg):
        sender, mg = msg.split('\r\r')
        self.textBrowser.append(f"<font color='blue'> {sender}" + ": <font>" + mg)
        self.textBrowser.moveCursor(self.textBrowser.textCursor().End)  # 文本框显示到底部


if __name__ == "__main__":
    import sys

    sock = socket.socket()
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QMainWindow()
    ui = ChatRoom(sock)
    ui.setupUi(Form)
    Form.show()

    sys.exit(app.exec_())

