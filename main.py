from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QTextEdit
from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from ui_mainwindow import Ui_MainWindow
import sys
import socket

class ClientNode(QtCore.QThread):
    received = QtCore.pyqtSignal(str)

    def __init__(self, host, port, name, parent=None):
        super().__init__(parent)
        self.host = host
        self.port = port
        self.name = name
        self.running = True
        self.node = None

    def run(self):
        try:
            self.node = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.node.connect((self.host, int(self.port)))
            self.node.settimeout(1)
            while self.running:
                try:
                    data = self.node.recv(1024).decode()
                    if data:
                        self.received.emit(data)
                except socket.timeout:
                    continue
        except Exception as e:
            print("Lỗi kết nối:", e)
            self.received.emit("Lỗi kết nối: " + str(e))

    def send_sms(self, message):
        try:
            if self.node:
                full_message = f"{self.name}: {message}"
                self.node.send(full_message.encode())
        except Exception as e:
            print("Lỗi gửi tin nhắn:", e)
            self.received.emit("Lỗi gửi tin nhắn: " + str(e))

    def stop(self):
        self.running = False
        if self.node:
            self.node.close()

class ChatTextEdit(QTextEdit):
    enter_pressed = QtCore.pyqtSignal()  # Tín hiệu để báo phím Enter đã được nhấn

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.enter_pressed.emit()  # Phát tín hiệu khi nhấn Enter
        else:
            super().keyPressEvent(event)  # Xử lý các phím khác như bình thường

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.uic = Ui_MainWindow()
        self.uic.setupUi(self)

        # Tạo một đối tượng ChatTextEdit để thay thế cho self.uic.Chat
        self.uic.Chat = ChatTextEdit(self)
        self.uic.Chat.setGeometry(190, 110, 541, 161)  # Điều chỉnh kích thước và vị trí theo giao diện của bạn
        self.uic.Chat.enter_pressed.connect(self.send_message)  # Kết nối sự kiện Enter với hàm send_message

        # Khởi tạo biến cho client
        self.client_thread = None

        # Kết nối các nút với các phương thức
        self.uic.english.clicked.connect(self.english)
        self.uic.vietnam.clicked.connect(self.vietnam)
        self.uic.start.clicked.connect(self.start)
        self.uic.stop.clicked.connect(self.stop)

    def english(self):
        self.uic.label_1.setText('Your ID')
        self.uic.label_2.setText('Your Port')
        self.uic.label_3.setText('Your Name')
        self.uic.label_6.setText('Notice')
        self.uic.label_4.setText('Chat Middle')
        self.uic.Chat.setText('Convert language to English successfully!')

    def vietnam(self):
        self.uic.label_1.setText('ID riêng của bạn')
        self.uic.label_2.setText('Port riêng của bạn')
        self.uic.label_3.setText('Tên của bạn')
        self.uic.label_6.setText('Bảng thông báo')
        self.uic.label_4.setText('Bảng nhắn tin trung tâm')
        self.uic.Chat.setText('Đã chuyển qua ngôn ngữ tiếng Việt')

    def start(self):
        host = self.uic.ID.toPlainText()
        port = self.uic.Pot.toPlainText()
        name = self.uic.Name.toPlainText()

        QMessageBox.information(self, "Thông Báo", "Cài đặt thành công!")

        # Bắt đầu luồng client
        self.client_thread = ClientNode(host, port, name)
        self.client_thread.received.connect(self.update_chat)
        self.client_thread.start()

    def send_message(self):
        message = self.uic.Chat.toPlainText()
        if self.client_thread and message.strip():
            self.client_thread.send_sms(message)
            self.uic.Chat.clear()  # Xóa nội dung sau khi gửi

    def update_chat(self, message):
        self.uic.Chat.append(message)

    def stop(self):
        QMessageBox.warning(self, "Thông báo", "Công cụ đã dừng!")
        if self.client_thread:
            self.client_thread.stop()
            self.client_thread = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())
