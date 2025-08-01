# -*- coding: utf-8 -*-

"""
config.py (v3)
Tệp này chứa tất cả các cấu hình và hằng số cho ứng dụng PixelPure.
Cập nhật để sử dụng ngưỡng mặc định cho thanh trượt.
"""

# --- Thông tin ứng dụng ---
APP_NAME = "PixelPure"
APP_VERSION = "2.1.0"
SLOGAN = "Quét sâu, dọn gọn, hiệu quả cao"

# --- Cấu hình Model AI ---
MODEL_NAME = "openai/clip-vit-base-patch32"

# --- Ngưỡng điểm tương đồng (%) ---
# Các file có điểm từ HIGH_SIMILARITY_SCORE trở lên sẽ được coi là trùng lặp cao.
HIGH_SIMILARITY_SCORE = 95.0
# Ngưỡng mặc định cho chế độ quét sâu, có thể được người dùng thay đổi.
DEFAULT_SIMILAR_SCORE_THRESHOLD = 70.0

# --- Cấu hình cho việc chuyển đổi các giá trị thành điểm ---
MAX_L2_DISTANCE = 40.0
PHASH_HAMMING_DISTANCE_THRESHOLD = 5

# --- Các định dạng file được hỗ trợ ---
IMAGE_EXTS = [
    '.jpg', '.jpeg', '.jpe', '.jif', '.jfif', '.jfi',
    '.png', '.gif', '.webp', '.tiff', '.tif', '.bmp', '.dib',
    '.heic', '.heif', '.ico', '.raw', '.cr2', '.nef', '.orf', '.sr2'
]
VIDEO_EXTS = [
    '.mp4', '.m4p', '.m4v', '.avi', '.mov', '.qt', '.mkv',
    '.flv', '.swf', '.wmv', '.mpg', '.mp2', '.mpeg', '.mpe', '.mpv', '.webm'
]
OTHER_EXTS = [
    '.doc', '.docx', '.odt', '.pdf', '.txt', '.rtf', '.md',
    '.xls', '.xlsx', '.ods', '.ppt', '.pptx', '.odp',
    '.zip', '.rar', '.7z', '.tar', '.gz',
    '.mp3', '.wav', '.ogg', '.flac', '.m4a'
]

# --- CSS (QSS) cho Giao Diện ---
STYLESHEET = """
QWidget {
    font-family: "Segoe UI", "Arial", "Helvetica", sans-serif;
    font-size: 14px;
    color: #e0e0e0;
    background-color: #2c313c;
}
QMainWindow {
    background-color: #23272e;
}
QGroupBox {
    font-weight: bold;
    font-size: 16px;
    border: 1px solid #4a5060;
    border-radius: 8px;
    margin-top: 10px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 10px;
}
QLabel {
    background-color: transparent;
}
QPushButton {
    background-color: #4a5060;
    border: 1px solid #5a6070;
    padding: 8px 16px;
    border-radius: 5px;
    min-width: 100px;
}
QPushButton:hover {
    background-color: #5a6070;
    border: 1px solid #6a7080;
}
QPushButton:pressed {
    background-color: #3a4050;
}
QPushButton#StartButton {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0072ff, stop:1 #00c6ff);
    color: white;
    font-weight: bold;
    font-size: 16px;
    padding: 12px;
}
QPushButton#StartButton:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0082ff, stop:1 #00d6ff);
}
QPushButton#DeleteButton {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #c31432, stop:1 #240b36);
    color: white;
    font-weight: bold;
}
QPushButton#DeleteButton:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #d32442, stop:1 #341b46);
}
QPushButton#GroupButton {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #11998e, stop:1 #38ef7d);
    color: white;
    font-weight: bold;
}
QPushButton#GroupButton:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #21a99e, stop:1 #48ff8d);
}
QTableWidget {
    background-color: #3a4050;
    border: 1px solid #4a5060;
    gridline-color: #4a5060;
}
QHeaderView::section {
    background-color: #4a5060;
    padding: 4px;
    border: 1px solid #2c313c;
    font-weight: bold;
}
QRadioButton, QCheckBox {
    background-color: transparent;
}
QProgressDialog {
    background-color: #3a4050;
}
QScrollArea {
    border: none;
}
QSlider::groove:horizontal {
    border: 1px solid #4a5060;
    height: 8px;
    background: #3a4050;
    margin: 2px 0;
    border-radius: 4px;
}
QSlider::handle:horizontal {
    background: #e0e0e0;
    border: 1px solid #e0e0e0;
    width: 18px;
    margin: -5px 0;
    border-radius: 9px;
}
"""
