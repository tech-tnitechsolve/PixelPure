# -*- coding: utf-8 -*-

"""
settings_manager.py
Module này quản lý việc đọc và ghi cài đặt của người dùng vào file JSON.
"""

import json
import os

SETTINGS_FILE = "settings.json"
DEFAULT_SETTINGS = {
    "similar_score_threshold": 70,
    "file_operation": "move",
    "scan_mode": "fast",
    "results_layout": "vertical",
    "processing_device": "auto"  # Thêm cài đặt mới: 'auto', 'cuda', 'cpu'
}

def load_settings():
    """
    Tải cài đặt từ file JSON. Nếu file không tồn tại hoặc lỗi,
    tạo mới với các giá trị mặc định.
    """
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                # Đảm bảo tất cả các key mặc định đều tồn tại
                for key, value in DEFAULT_SETTINGS.items():
                    if key not in settings:
                        settings[key] = value
                return settings
        except (json.JSONDecodeError, IOError):
            return DEFAULT_SETTINGS.copy()
    else:
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    """Lưu từ điển cài đặt vào file JSON."""
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4)
        return True
    except IOError:
        return False

def reset_settings():
    """Xóa file cài đặt và lưu lại cài đặt mặc định."""
    if os.path.exists(SETTINGS_FILE):
        try:
            os.remove(SETTINGS_FILE)
        except OSError:
            pass # Bỏ qua nếu không xóa được
    save_settings(DEFAULT_SETTINGS)
    return DEFAULT_SETTINGS.copy()
