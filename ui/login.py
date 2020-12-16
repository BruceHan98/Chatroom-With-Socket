import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from utils.header import *

sock = None


def login_get_sock(s):
    global sock
    sock = s


class LoginWindow(QMainWindow):
    """
    聊天室的登录窗口：
    """
    # 外部调用状态
    CLOSE = pyqtSignal()
    LOGIN_REPEAT = pyqtSignal()
    PASSWORD_WRONG = pyqtSignal()
    REGISTER_SUCCESS = pyqtSignal()
    REGISTER_REPEAT = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sock = sock
        # 为了能在外部调用
        self.CLOSE.connect(self.close)
        self.LOGIN_REPEAT.connect(self.login_repeat)
        self.PASSWORD_WRONG.connect(self.password_wrong)
        self.REGISTER_REPEAT.connect(self.register_repeat)
        self.REGISTER_SUCCESS.connect(self.register_success)

        self.label = QLabel("<h4 style='text-align:center'>登录</h3>")
        self.label.setDisabled(True)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.username = QLineEdit()
        self.username.setPlaceholderText("用户名")
        self.password = QLineEdit()
        self.password.setPlaceholderText("密码")
        self.password.setEchoMode(2)
        layout = QGridLayout()
        self.btnSend = QPushButton("登录")
        self.btnRegister = QPushButton("注册")
        self.btnQuit = QPushButton("退出")
        self.btnSend.pressed.connect(self.login)
        self.btnRegister.pressed.connect(self.register)
        self.btnQuit.pressed.connect(self.close)

        layout.addWidget(self.label, 0, 0, 1, 3)
        layout.addWidget(self.username, 1, 0, 2, 3)
        layout.addWidget(self.password, 3, 0, 2, 3)
        layout.addWidget(self.btnSend, 5, 0)
        layout.addWidget(self.btnRegister, 5, 1)
        layout.addWidget(self.btnQuit, 5, 2)
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        self.setFixedSize(320, 150)
        self.center()
        self.setWindowOpacity(0.95)

    def mousePressEvent(self, event):
        print(event.globalPos())
        self.windowPos = self.pos()
        self.mousePos = event.globalPos()
        self.dPos = self.mousePos - self.windowPos

    def mouseMoveEvent(self, event):
        print(event.globalPos())
        self.move(event.globalPos() - self.dPos)

    def center(self):
        """
        center the window
        """
        qr_ = self.frameGeometry()
        cp_ = QDesktopWidget().availableGeometry().center()
        qr_.moveCenter(cp_)
        self.move(qr_.topLeft())

    def password_wrong(self):
        QMessageBox.warning(self, "Warning", "\n用户名或密码错误", QMessageBox.Cancel)

    def login_repeat(self):
        QMessageBox.warning(self, "Warning", "\n用户已经在线", QMessageBox.Cancel)

    def register_success(self):
        QMessageBox.information(self, "Info", "\n注册成功", QMessageBox.Yes)

    def register_repeat(self):
        QMessageBox.warning(self, "Warning", "\n请不要重复注册", QMessageBox.Cancel)

    def login(self):
        username = self.username.text()
        password = self.password.text()
        self.sock.sendall((str(c_login) + '\r\r' + username + '\r\r' + password).encode('utf-8'))

    def register(self):
        username = self.username.text()
        password = self.password.text()
        QMessageBox.question(self, "CONFIRM", "\n确定要注册吗?", QMessageBox.Yes | QMessageBox.No,
                             QMessageBox.No)
        self.sock.sendall((str(c_register) + '\r\r' + username + '\r\r' + password).encode('utf-8'))

    def keyPressEvent(self, QKeyEvent):
        """
        登录对话框的按键处理函数：按下回车键或者小键盘的enter键触发点击login按钮。
        """
        if QKeyEvent.key() == Qt.Key_Return or QKeyEvent.key() == Qt.Key_Enter:
            self.btnSend.animateClick()
        if QKeyEvent.key() == Qt.Key_Escape:
            self.btnQuit.animateClick()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    loginWindow = LoginWindow()

    loginWindow.btnSend.clicked.connect(loginWindow.close)

    loginWindow.show()
    app.exec_()
