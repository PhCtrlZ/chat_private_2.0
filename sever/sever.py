from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QTextEdit, QLineEdit, QPushButton, QLabel, QVBoxLayout, QWidget
from PyQt5 import QtCore
import sys
import socket
import threading
from ui_server import Ui_ServerWindow  # Import giao diện sau khi biên dịch từ .ui

class ServerNode(QtCore.QThread):
    new_message = QtCore.pyqtSignal(str)

    def __init__(self, host, port, parent=None):
        super().__init__(parent)
        self.host = host
        self.port = port
        self.running = True
        self.node = None
        self.clients = []

    def broadcast(self, message, client_socket=None):
        # Gửi tin nhắn đến tất cả client, bỏ qua client_socket nếu nó là người gửi
        for client in self.clients:
            if client != client_socket:
                try:
                    client.send(message.encode())
                except:
                    self.clients.remove(client)

    def handle_client(self, client_socket):
        while self.running:
            try:
                data = client_socket.recv(1024).decode()
                if data:
                    self.new_message.emit(data)
                    self.broadcast(data, client_socket)
            except:
                self.clients.remove(client_socket)
                client_socket.close()
                break

    def run(self):
        try:
            self.node = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.node.bind((self.host, int(self.port)))
            self.node.listen(5)
            self.new_message.emit("Server đang lắng nghe...")

            while self.running:
                client_socket, addr = self.node.accept()
                self.clients.append(client_socket)
                self.new_message.emit(f"Kết nối từ {addr}")

                client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
                client_thread.daemon = True
                client_thread.start()
        except Exception as e:
            self.new_message.emit("Lỗi khởi động server: " + str(e))

    def stop(self):
        self.running = False
        for client in self.clients:
            client.close()
        if self.node:
            self.node.close()
        self.new_message.emit("Server đã dừng.")

class ServerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_ServerWindow()
        self.ui.setupUi(self)

        # Khởi tạo các biến server
        self.server_thread = None

        # Kết nối nút và sự kiện
        self.ui.start_button.clicked.connect(self.start_server)
        self.ui.stop_button.clicked.connect(self.stop_server)
        self.ui.send_button.clicked.connect(self.send_message)

    def start_server(self):
        host = self.ui.host_input.text()
        port = self.ui.port_input.text()

        if not host or not port.isdigit():
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đúng IP và cổng.")
            return

        self.server_thread = ServerNode(host, int(port))
        self.server_thread.new_message.connect(self.ui.log_display.append)
        self.server_thread.start()

        self.ui.start_button.setEnabled(False)
        self.ui.stop_button.setEnabled(True)
        self.ui.log_display.append("Server đã bắt đầu.")

    def stop_server(self):
        if self.server_thread:
            self.server_thread.stop()
            self.server_thread = None

        self.ui.start_button.setEnabled(True)
        self.ui.stop_button.setEnabled(False)
        self.ui.log_display.append("Server đã dừng.")

    def send_message(self):
        message = self.ui.message_input.toPlainText().strip()
        if message and self.server_thread:
            formatted_message = f"Server: {message}"
            self.server_thread.broadcast(formatted_message)
            self.ui.log_display.append(f"Bạn: {message}")
            self.ui.message_input.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    server_win = ServerWindow()
    server_win.show()
    sys.exit(app.exec())
