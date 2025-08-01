# -*- coding: utf-8 -*-

"""
main.py
Đây là file khởi chạy chính cho ứng dụng PixelPure.
Nhiệm vụ của nó là tạo ứng dụng, cửa sổ chính và hiển thị giao diện.
"""

# SỬA LỖI: Thêm đoạn mã để xử lý lỗi xung đột thư viện OpenMP (OMP: Error #15)
# Lỗi này thường xảy ra khi các thư viện như PyTorch, OpenCV, NumPy sử dụng các phiên bản
# OpenMP khác nhau. Đặt biến môi trường này là một giải pháp phổ biến.
import os
os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

# Import các thành phần cần thiết từ các module khác
from ui import MainWindow
from config import STYLESHEET

def main():
    """Hàm chính để chạy ứng dụng."""
    # Tạo đối tượng ứng dụng
    app = QApplication(sys.argv)
    
    # Thiết lập stylesheet (giao diện) cho toàn bộ ứng dụng
    app.setStyleSheet(STYLESHEET)
    
    # (Tùy chọn) Thiết lập icon cho ứng dụng
    # Hãy tạo một file icon.png và đặt cùng thư mục với main.py
    # app.setWindowIcon(QIcon("icon.png"))
    
    # Tạo và hiển thị cửa sổ chính
    main_window = MainWindow()
    main_window.show()
    
    # Bắt đầu vòng lặp sự kiện của ứng dụng
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
