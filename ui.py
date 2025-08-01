# -*- coding: utf-8 -*-

"""
ui.py (v13)
Module này chứa tất cả các thành phần giao diện người dùng (UI) của ứng dụng.
Đã nâng cấp cửa sổ Cài đặt, logic click bảng, tùy chọn hiển thị kết quả,
và cải thiện giao diện hộp thoại tiến trình.
"""

import os
import shutil
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QStackedWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QProgressDialog,
    QGroupBox, QHBoxLayout, QScrollArea, QMessageBox, QRadioButton, QStyle,
    QSlider, QDialog, QDialogButtonBox, QGridLayout, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QPixmap, QIcon, QDragEnterEvent, QDropEvent
from send2trash import send2trash

from config import (
    IMAGE_EXTS, VIDEO_EXTS, OTHER_EXTS, SLOGAN, APP_NAME,
    HIGH_SIMILARITY_SCORE
)
from scanner import ScannerWorker
from settings_manager import load_settings, save_settings, reset_settings


class CustomProgressDialog(QDialog):
    """Hộp thoại tiến trình được tùy chỉnh cho giao diện đẹp hơn."""
    canceled = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Đang Xử Lý")
        # Ẩn nút dấu hỏi và chỉ giữ lại nút đóng
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        self.setFixedSize(450, 180)

        layout = QVBoxLayout(self)
        self.status_label = QLabel("Đang chuẩn bị quét...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px;")

        self.device_label = QLabel("") # Nhãn hiển thị thiết bị
        self.device_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.device_label.setStyleSheet("font-size: 12px; color: #aaa;")

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #4a5060;
                border-radius: 5px;
                text-align: center;
                color: #e0e0e0;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0072ff, stop:1 #00c6ff);
                border-radius: 5px;
            }
        """)
        
        btn_cancel = QPushButton("Hủy")
        btn_cancel.clicked.connect(self.reject)

        layout.addWidget(self.status_label)
        layout.addWidget(self.device_label)
        layout.addWidget(self.progress_bar)
        # SỬA LỖI: Sử dụng cú pháp đúng để căn giữa widget
        layout.addWidget(btn_cancel, alignment=Qt.AlignmentFlag.AlignCenter)

    def setValue(self, value):
        self.progress_bar.setValue(value)

    def setLabelText(self, text):
        self.status_label.setText(text)

    def setDeviceInfo(self, text):
        self.device_label.setText(text)

    def reject(self):
        """Phát tín hiệu khi người dùng hủy."""
        self.canceled.emit()
        super().reject()

class DragDropWidget(QWidget):
    files_dropped = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label = QLabel()
        style = self.style()
        if style:
            icon = style.standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon)
            icon_label.setPixmap(icon.pixmap(128, 128))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_text = QLabel("Kéo và Thả Thư Mục hoặc File vào đây")
        main_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_text.setStyleSheet("font-size: 28px; font-weight: bold; color: #e0e0e0;")
        sub_text = QLabel("PixelPure sẽ thực hiện quét sâu để tìm các file trùng lặp và tương tự")
        sub_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_text.setStyleSheet("font-size: 16px; color: #aaa;")
        layout.addWidget(icon_label)
        layout.addWidget(main_text)
        layout.addWidget(sub_text)

    def dragEnterEvent(self, a0: QDragEnterEvent | None):
        if a0 and (mime_data := a0.mimeData()) and mime_data.hasUrls():
            a0.acceptProposedAction()
        elif a0:
            a0.ignore()

    def dropEvent(self, a0: QDropEvent | None):
        if a0 and (mime_data := a0.mimeData()) and mime_data.hasUrls():
            paths = [url.toLocalFile() for url in mime_data.urls()]
            self.files_dropped.emit(paths)
        elif a0:
            a0.ignore()


class SettingsDialog(QDialog):
    """Cửa sổ dialog để người dùng tùy chỉnh cài đặt."""
    settings_reset = pyqtSignal()

    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cài đặt")
        self.setMinimumWidth(450)
        
        self.settings = current_settings.copy()
        
        layout = QVBoxLayout(self)
        
        group_scan_mode = QGroupBox("Chế độ quét mặc định")
        layout_scan_mode = QVBoxLayout(group_scan_mode)
        self.radio_scan_fast = QRadioButton("Quét nhanh (Trùng lặp cao)")
        self.radio_scan_deep = QRadioButton("Quét sâu (Tương tự - AI)")
        if self.settings.get("scan_mode", "fast") == "fast":
            self.radio_scan_fast.setChecked(True)
        else:
            self.radio_scan_deep.setChecked(True)
        layout_scan_mode.addWidget(self.radio_scan_fast)
        layout_scan_mode.addWidget(self.radio_scan_deep)
        layout.addWidget(group_scan_mode)

        group_threshold = QGroupBox("Ngưỡng tương đồng mặc định (Quét sâu)")
        layout_threshold = QHBoxLayout(group_threshold)
        self.slider_threshold = QSlider(Qt.Orientation.Horizontal)
        self.slider_threshold.setRange(30, 95)
        self.lbl_threshold = QLabel()
        self.slider_threshold.valueChanged.connect(lambda val: self.lbl_threshold.setText(f"{val}%"))
        self.slider_threshold.setValue(self.settings.get("similar_score_threshold", 70))
        layout_threshold.addWidget(self.slider_threshold)
        layout_threshold.addWidget(self.lbl_threshold)
        layout.addWidget(group_threshold)

        group_device = QGroupBox("Thiết bị xử lý AI")
        layout_device = QVBoxLayout(group_device)
        self.radio_device_auto = QRadioButton("Tự động (Khuyên dùng)")
        self.radio_device_cuda = QRadioButton("Ưu tiên GPU (NVIDIA Cuda)")
        self.radio_device_cpu = QRadioButton("Chỉ dùng CPU")
        device_setting = self.settings.get("processing_device", "auto")
        if device_setting == "cuda": self.radio_device_cuda.setChecked(True)
        elif device_setting == "cpu": self.radio_device_cpu.setChecked(True)
        else: self.radio_device_auto.setChecked(True)
        layout_device.addWidget(self.radio_device_auto)
        layout_device.addWidget(self.radio_device_cuda)
        layout_device.addWidget(self.radio_device_cpu)
        layout.addWidget(group_device)

        group_file_op = QGroupBox("Hành động khi Nhóm File")
        layout_file_op = QVBoxLayout(group_file_op)
        self.radio_move = QRadioButton("Di chuyển file (Move)")
        self.radio_copy = QRadioButton("Sao chép file (Copy)")
        if self.settings.get("file_operation", "move") == "move":
            self.radio_move.setChecked(True)
        else:
            self.radio_copy.setChecked(True)
        layout_file_op.addWidget(self.radio_move)
        layout_file_op.addWidget(self.radio_copy)
        layout.addWidget(group_file_op)
        
        group_results_layout = QGroupBox("Hiển thị kết quả")
        layout_results = QVBoxLayout(group_results_layout)
        self.radio_layout_vertical = QRadioButton("Theo hàng dọc (Vertical)")
        self.radio_layout_horizontal = QRadioButton("Theo hàng ngang (Horizontal)")
        if self.settings.get("results_layout", "vertical") == "vertical":
            self.radio_layout_vertical.setChecked(True)
        else:
            self.radio_layout_horizontal.setChecked(True)
        layout_results.addWidget(self.radio_layout_vertical)
        layout_results.addWidget(self.radio_layout_horizontal)
        layout.addWidget(group_results_layout)

        btn_reset = QPushButton("Reset về mặc định")
        btn_reset.clicked.connect(self.reset_to_defaults)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(btn_reset)
        bottom_layout.addStretch()
        bottom_layout.addWidget(button_box)
        layout.addLayout(bottom_layout)

    def reset_to_defaults(self):
        reply = QMessageBox.question(self, "Xác nhận", "Bạn có chắc muốn reset tất cả cài đặt về mặc định không?")
        if reply == QMessageBox.StandardButton.Yes:
            self.settings = reset_settings()
            self.settings_reset.emit()
            self.accept()

    def get_updated_settings(self):
        self.settings["scan_mode"] = "deep" if self.radio_scan_deep.isChecked() else "fast"
        self.settings["similar_score_threshold"] = self.slider_threshold.value()
        if self.radio_device_cuda.isChecked(): self.settings["processing_device"] = "cuda"
        elif self.radio_device_cpu.isChecked(): self.settings["processing_device"] = "cpu"
        else: self.settings["processing_device"] = "auto"
        self.settings["file_operation"] = "copy" if self.radio_copy.isChecked() else "move"
        self.settings["results_layout"] = "horizontal" if self.radio_layout_horizontal.isChecked() else "vertical"
        return self.settings


class FileProcessingWidget(QWidget):
    start_scan_signal = pyqtSignal(list, str, int)
    reset_signal = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.file_list = set()
        self.setAcceptDrops(True)
        main_layout = QHBoxLayout(self)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["", "Tên File", "Kích Thước", "Loại", "Đường Dẫn"])
        header = self.table.horizontalHeader()
        if header:
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 30)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.cellClicked.connect(self.toggle_checkbox_on_row_click)
        
        control_buttons_layout = QHBoxLayout()
        btn_add_file = QPushButton("Thêm File")
        btn_add_folder = QPushButton("Thêm Thư Mục")
        btn_select_all = QPushButton("Chọn Tất Cả")
        btn_deselect_all = QPushButton("Bỏ Chọn Tất Cả")
        
        btn_add_file.clicked.connect(self.add_files)
        btn_add_folder.clicked.connect(self.add_folder)
        btn_select_all.clicked.connect(self.select_all)
        btn_deselect_all.clicked.connect(self.deselect_all)
        
        control_buttons_layout.addWidget(btn_add_file)
        control_buttons_layout.addWidget(btn_add_folder)
        control_buttons_layout.addStretch()
        control_buttons_layout.addWidget(btn_select_all)
        control_buttons_layout.addWidget(btn_deselect_all)
        
        left_layout.addLayout(control_buttons_layout)
        left_layout.addWidget(self.table)
        
        right_panel = QWidget()
        right_panel.setFixedWidth(280)
        right_layout = QVBoxLayout(right_panel)
        
        top_right_layout = QHBoxLayout()
        top_right_layout.addStretch()
        btn_settings = QPushButton("Cài đặt")
        if self.parent_window:
            btn_settings.clicked.connect(self.parent_window.open_settings_dialog)
        top_right_layout.addWidget(btn_settings)
        right_layout.addLayout(top_right_layout)

        stats_group = QGroupBox("Thống Kê")
        stats_layout = QVBoxLayout(stats_group)
        self.lbl_total_files = QLabel("Tổng số file: 0")
        self.lbl_total_size = QLabel("Tổng dung lượng: 0 MB")
        self.lbl_total_images = QLabel("Tổng số ảnh: 0")
        self.lbl_total_videos = QLabel("Tổng số video: 0")
        self.lbl_total_others = QLabel("Tổng số file khác: 0")
        stats_layout.addWidget(self.lbl_total_files)
        stats_layout.addWidget(self.lbl_total_size)
        stats_layout.addWidget(self.lbl_total_images)
        stats_layout.addWidget(self.lbl_total_videos)
        stats_layout.addWidget(self.lbl_total_others)
        
        scan_group = QGroupBox("Chế Độ Quét")
        scan_layout = QVBoxLayout(scan_group)
        self.radio_fast = QRadioButton("Quét nhanh (Trùng lặp cao)")
        self.radio_deep = QRadioButton("Quét sâu (Tương tự - AI)")
        scan_layout.addWidget(self.radio_fast)
        scan_layout.addWidget(self.radio_deep)

        self.threshold_widget = QWidget()
        threshold_layout = QHBoxLayout(self.threshold_widget)
        threshold_layout.setContentsMargins(0, 5, 0, 0)
        self.slider_threshold = QSlider(Qt.Orientation.Horizontal)
        self.slider_threshold.setRange(30, 95)
        self.lbl_threshold_value = QLabel()
        threshold_layout.addWidget(QLabel("Ngưỡng:"))
        threshold_layout.addWidget(self.slider_threshold)
        threshold_layout.addWidget(self.lbl_threshold_value)
        scan_layout.addWidget(self.threshold_widget)
        
        self.slider_threshold.valueChanged.connect(self.update_threshold_label)
        self.radio_deep.toggled.connect(self.toggle_threshold_slider)
        
        btn_start = QPushButton("Bắt Đầu Quét")
        btn_start.setObjectName("StartButton")
        btn_start.clicked.connect(self.start_scan)
        
        btn_reset = QPushButton("Reset")
        btn_reset.clicked.connect(self.reset_signal.emit)
        
        right_layout.addWidget(stats_group)
        right_layout.addWidget(scan_group)
        right_layout.addStretch()
        right_layout.addWidget(btn_start)
        right_layout.addWidget(btn_reset)
        
        main_layout.addWidget(left_panel, 3)
        main_layout.addWidget(right_panel, 1)

        self.update_ui_from_settings()

    def update_ui_from_settings(self):
        if self.parent_window and hasattr(self.parent_window, 'settings'):
            settings = self.parent_window.settings
            threshold = settings.get("similar_score_threshold", 70)
            self.slider_threshold.setValue(threshold)
            self.update_threshold_label(threshold)
            
            scan_mode = settings.get("scan_mode", "fast")
            if scan_mode == "deep":
                self.radio_deep.setChecked(True)
            else:
                self.radio_fast.setChecked(True)
            
            self.toggle_threshold_slider(self.radio_deep.isChecked())

    def toggle_threshold_slider(self, checked):
        self.threshold_widget.setVisible(checked)

    def update_threshold_label(self, value):
        self.lbl_threshold_value.setText(f"{value}%")

    def add_paths(self, paths):
        all_files_in_drop = set()
        supported_exts = IMAGE_EXTS + VIDEO_EXTS + OTHER_EXTS
        for path in paths:
            path_str = str(path)
            if os.path.isdir(path_str):
                for root, _, files in os.walk(path_str):
                    for name in files:
                        if Path(name).suffix.lower() in supported_exts:
                            all_files_in_drop.add(os.path.join(root, name))
            elif os.path.isfile(path_str) and Path(path_str).suffix.lower() in supported_exts:
                all_files_in_drop.add(path_str)
        
        if new_files := all_files_in_drop - self.file_list:
            self.file_list.update(new_files)
            self.update_table()

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Chọn file", "", "All Files (*)")
        if files: self.add_paths(files)
            
    def add_folder(self):
        if folder := QFileDialog.getExistingDirectory(self, "Chọn thư mục"):
            self.add_paths([folder])

    def update_table(self):
        self.table.setRowCount(0)
        total_size, image_count, video_count, other_count = 0, 0, 0, 0
        sorted_list = sorted(list(self.file_list))
        self.table.setRowCount(len(sorted_list))

        for row, file_path in enumerate(sorted_list):
            chk_box_item = QTableWidgetItem()
            chk_box_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            chk_box_item.setCheckState(Qt.CheckState.Checked)
            self.table.setItem(row, 0, chk_box_item)

            p = Path(file_path)
            try:
                size = os.path.getsize(file_path)
                total_size += size
                ext = p.suffix.lower()
                if ext in IMAGE_EXTS: file_type, image_count = "Ảnh", image_count + 1
                elif ext in VIDEO_EXTS: file_type, video_count = "Video", video_count + 1
                else: file_type, other_count = "Khác", other_count + 1

                self.table.setItem(row, 1, QTableWidgetItem(p.name))
                self.table.setItem(row, 2, QTableWidgetItem(f"{size / 1024 / 1024:.2f} MB"))
                self.table.setItem(row, 3, QTableWidgetItem(file_type))
                self.table.setItem(row, 4, QTableWidgetItem(file_path))
            except FileNotFoundError: continue
        
        self.lbl_total_files.setText(f"Tổng số file: {self.table.rowCount()}")
        self.lbl_total_size.setText(f"Tổng dung lượng: {total_size / 1024 / 1024:.2f} MB")
        self.lbl_total_images.setText(f"Tổng số ảnh: {image_count}")
        self.lbl_total_videos.setText(f"Tổng số video: {video_count}")
        self.lbl_total_others.setText(f"Tổng số file khác: {other_count}")

    def toggle_checkbox_on_row_click(self, row, column):
        if item := self.table.item(row, 0):
            current_state = item.checkState()
            item.setCheckState(Qt.CheckState.Unchecked if current_state == Qt.CheckState.Checked else Qt.CheckState.Checked)

    def select_all(self):
        for i in range(self.table.rowCount()):
            if item := self.table.item(i, 0): item.setCheckState(Qt.CheckState.Checked)

    def deselect_all(self):
        for i in range(self.table.rowCount()):
            if item := self.table.item(i, 0): item.setCheckState(Qt.CheckState.Unchecked)

    def get_selected_files(self):
        selected = []
        for i in range(self.table.rowCount()):
            if (item := self.table.item(i, 0)) and item.checkState() == Qt.CheckState.Checked:
                if path_item := self.table.item(i, 4):
                    selected.append(path_item.text())
        return selected

    def start_scan(self):
        if not (selected_files := self.get_selected_files()):
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn ít nhất một file để quét.")
            return
        scan_mode = 'deep' if self.radio_deep.isChecked() else 'fast'
        threshold = self.slider_threshold.value()
        if self.parent_window and hasattr(self.parent_window, 'settings'):
            self.parent_window.settings["similar_score_threshold"] = threshold
            self.parent_window.settings["scan_mode"] = scan_mode
            save_settings(self.parent_window.settings)
        self.start_scan_signal.emit(selected_files, scan_mode, threshold)

    def reset(self):
        self.file_list.clear()
        self.update_table()


class ResultsWidget(QWidget):
    back_signal = pyqtSignal()
    rescan_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.groups = {}
        main_layout = QVBoxLayout(self)
        
        top_bar_layout = QHBoxLayout()
        btn_back = QPushButton("Quay Lại")
        btn_back.clicked.connect(self.back_signal.emit)
        self.lbl_results_summary = QLabel("Kết quả quét:")
        self.lbl_results_summary.setStyleSheet("font-weight: bold; font-size: 16px;")
        
        layout_options_group = QGroupBox("Hiển thị")
        layout_options_layout = QHBoxLayout(layout_options_group)
        self.radio_vertical = QRadioButton("Dọc")
        self.radio_horizontal = QRadioButton("Ngang")
        self.radio_vertical.toggled.connect(self.redraw_results)
        layout_options_layout.addWidget(self.radio_vertical)
        layout_options_layout.addWidget(self.radio_horizontal)

        top_bar_layout.addWidget(btn_back)
        top_bar_layout.addWidget(self.lbl_results_summary)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(layout_options_group)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.results_layout = QVBoxLayout(self.scroll_content)
        self.results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.scroll_content)
        
        bottom_bar_layout = QHBoxLayout()
        self.btn_delete = QPushButton("Xóa File Đã Chọn")
        self.btn_delete.setObjectName("DeleteButton")
        self.btn_group_op = QPushButton()
        self.btn_group_op.setObjectName("GroupButton")
        
        self.btn_delete.clicked.connect(self.delete_selected)
        self.btn_group_op.clicked.connect(self.group_op_selected)
        
        bottom_bar_layout.addStretch()
        bottom_bar_layout.addWidget(self.btn_group_op)
        bottom_bar_layout.addWidget(self.btn_delete)
        
        main_layout.addLayout(top_bar_layout)
        main_layout.addWidget(self.scroll_area)
        main_layout.addLayout(bottom_bar_layout)
        
        self.update_ui_from_settings()

    def redraw_results(self):
        if not self.radio_vertical.isChecked() and not self.radio_horizontal.isChecked():
            return
            
        stored_groups = list(self.groups.items())
        
        self.clear_results()
        
        # Vẽ lại
        for group_id, file_widgets in stored_groups:
            score = float(group_id.split('_')[0])
            files = [path for cb, path in file_widgets]
            self.add_group(score, files, is_redraw=True)

    def update_ui_from_settings(self):
        if self.parent_window and hasattr(self.parent_window, 'settings'):
            settings = self.parent_window.settings
            op = settings.get("file_operation", "move")
            op_text = "Di chuyển" if op == "move" else "Sao chép"
            self.btn_group_op.setText(f"Nhóm và {op_text}")

            layout_mode = settings.get("results_layout", "vertical")
            if layout_mode == "horizontal":
                self.radio_horizontal.setChecked(True)
            else:
                self.radio_vertical.setChecked(True)
            
            self.redraw_results()

    def clear_results(self):
        while self.results_layout.count():
            if (child := self.results_layout.takeAt(0)) and (widget := child.widget()):
                widget.deleteLater()
        self.groups.clear()

    def add_group(self, score, files, is_redraw=False):
        group_id = f"{score}_{len(self.groups)}"
        group_type = "Tương tự"
        if score == 100.0: group_type = "Trùng lặp tuyệt đối"
        elif score >= HIGH_SIMILARITY_SCORE: group_type = "Trùng lặp cao"

        title = f"Nhóm {len(self.groups) + 1}: {group_type} ({score:.1f}%)"
        group_box = QGroupBox(title)
        
        layout_mode = "horizontal" if self.radio_horizontal.isChecked() else "vertical"
        
        # SỬA LỖI: Khởi tạo max_cols
        max_cols = 5
        if layout_mode == "horizontal":
            group_layout = QGridLayout(group_box)
            group_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        else:
            group_layout = QVBoxLayout(group_box)

        file_widgets = []
        try:
            sorted_files = sorted(files, key=lambda x: os.path.getsize(x) if os.path.exists(x) else -1, reverse=True)
        except FileNotFoundError: sorted_files = files

        for idx, file_path in enumerate(sorted_files):
            if not os.path.exists(file_path): continue
            p = Path(file_path)
            file_widget = QWidget()
            file_layout = QVBoxLayout(file_widget)
            
            cb = QRadioButton(p.name)
            thumb_label = QLabel()
            thumb_label.setFixedSize(120, 120)
            thumb_label.setStyleSheet("border: 1px solid #4a5060; background-color: #23272e; border-radius: 5px;")
            thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            ext = p.suffix.lower()
            if ext in IMAGE_EXTS:
                pixmap = QPixmap(file_path)
                thumb_label.setPixmap(pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                thumb_label.setText(ext.upper()[1:])
            
            size_label = QLabel(f"{os.path.getsize(file_path) / 1024 / 1024:.2f} MB")
            
            file_layout.addWidget(cb)
            file_layout.addWidget(thumb_label)
            file_layout.addWidget(size_label)
            file_widget.setToolTip(file_path)
            
            # Nếu là QGridLayout, dùng addWidget(widget, row, col). Nếu là QVBoxLayout, chỉ dùng addWidget(widget)
            if layout_mode == "horizontal":
                # type: ignore[arg-type]  # Đảm bảo IDE không cảnh báo nhầm alignment
                group_layout.addWidget(file_widget, idx // max_cols, idx % max_cols)  # type: ignore
            else:
                group_layout.addWidget(file_widget)

            file_widgets.append((cb, file_path))
        
        if file_widgets:
            file_widgets[0][0].setChecked(True)
            self.results_layout.addWidget(group_box)
            if not is_redraw:
                self.groups[group_id] = file_widgets

    def get_files_for_delete(self):
        to_delete = []
        for group_widgets in self.groups.values():
            kept_file = next((path for cb, path in group_widgets if cb.isChecked()), None)
            for _, path in group_widgets:
                if path != kept_file:
                    to_delete.append(path)
        return to_delete

    def delete_selected(self):
        if not (files_to_delete := self.get_files_for_delete()):
            QMessageBox.information(self, "Thông báo", "Không có file nào được chọn để xóa.")
            return

        reply = QMessageBox.question(self, "Xác nhận Xóa", f"Bạn có chắc muốn chuyển {len(files_to_delete)} file vào thùng rác không?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            success_count, errors = 0, []
            for f in files_to_delete:
                try: send2trash(f); success_count += 1
                except Exception as e: errors.append(f"{Path(f).name}: {e}")
            
            msg = f"Đã chuyển {success_count} file vào thùng rác thành công."
            if errors: msg += f"\n\nLỗi trên các file sau:\n" + "\n".join(errors)
            QMessageBox.information(self, "Hoàn tất", msg)
            self.rescan_signal.emit()

    def group_op_selected(self):
        dest_folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục đích")
        if not dest_folder: return

        total_files = sum(len(widgets) for widgets in self.groups.values())
        if not total_files:
            QMessageBox.information(self, "Thông báo", "Không có file nào để xử lý.")
            return

        op = "move"
        if self.parent_window and hasattr(self.parent_window, 'settings'):
            op = self.parent_window.settings.get("file_operation", "move")
        op_text_vn = "di chuyển" if op == "move" else "sao chép"
        
        reply = QMessageBox.question(self, f"Xác nhận {op_text_vn.capitalize()}", f"Bạn có chắc muốn {op_text_vn} và đổi tên TOÀN BỘ {total_files} file trong các nhóm không?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes: return

        file_op_func = shutil.move if op == "move" else shutil.copy2
        success_count, errors = 0, []
        
        for group_idx, (_, file_widgets) in enumerate(self.groups.items()):
            file_counter = 1
            for _, path in file_widgets:
                original_path = Path(path)
                try:
                    new_name = f"nhom_{group_idx + 1}({file_counter}){original_path.suffix}"
                    destination_path = os.path.join(dest_folder, new_name)
                    
                    while os.path.exists(destination_path):
                        file_counter += 1
                        new_name = f"nhom_{group_idx + 1}({file_counter}){original_path.suffix}"
                        destination_path = os.path.join(dest_folder, new_name)

                    file_op_func(path, destination_path)
                    success_count += 1
                    file_counter += 1
                except Exception as e: errors.append(f"{original_path.name}: {e}")

        msg = f"Đã {op_text_vn} và đổi tên thành công {success_count} file."
        if errors: msg += f"\n\nLỗi trên các file sau:\n" + "\n".join(errors)
        QMessageBox.information(self, "Hoàn tất", msg)
        self.rescan_signal.emit()


class MainWindow(QMainWindow):
    """Cửa sổ chính của ứng dụng."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} - {SLOGAN}")
        self.setGeometry(100, 100, 1200, 800)
        
        self.settings = load_settings()
        
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        self.drag_drop_widget = DragDropWidget(self)
        self.processing_widget = FileProcessingWidget(self)
        self.results_widget = ResultsWidget(self)
        
        self.stacked_widget.addWidget(self.drag_drop_widget)
        self.stacked_widget.addWidget(self.processing_widget)
        self.stacked_widget.addWidget(self.results_widget)
        
        self.drag_drop_widget.files_dropped.connect(self.handle_files_dropped)
        self.processing_widget.start_scan_signal.connect(self.start_scan)
        self.processing_widget.reset_signal.connect(self.reset_to_start)
        self.results_widget.back_signal.connect(self.show_processing_screen)
        self.results_widget.rescan_signal.connect(self.refresh_processing_screen)

        self.worker: ScannerWorker | None = None
        self.worker_thread: QThread | None = None
        self.is_scanning = False
        self.progress_dialog: CustomProgressDialog | None = None

    def open_settings_dialog(self):
        dialog = SettingsDialog(self.settings, self)
        dialog.settings_reset.connect(self.apply_and_save_settings)
        if dialog.exec():
            self.apply_and_save_settings(dialog.get_updated_settings())
            QMessageBox.information(self, "Thành công", "Đã lưu cài đặt.")

    def apply_and_save_settings(self, new_settings=None):
        if new_settings:
            self.settings = new_settings
        else:
            self.settings = load_settings()
        
        save_settings(self.settings)
        self.processing_widget.update_ui_from_settings()
        self.results_widget.update_ui_from_settings()

    def handle_files_dropped(self, paths):
        self.processing_widget.add_paths(paths)
        self.stacked_widget.setCurrentWidget(self.processing_widget)

    def start_scan(self, file_list, scan_mode, threshold):
        if self.is_scanning:
            QMessageBox.information(self, "Đang xử lý", "Một tiến trình quét đang chạy. Vui lòng đợi hoàn tất.")
            return
            
        self.is_scanning = True
        if self.results_widget:
            self.results_widget.clear_results()
        
        self.progress_dialog = CustomProgressDialog(self)
        self.progress_dialog.canceled.connect(self.cancel_scan)
        
        self.worker_thread = QThread()
        processing_device = self.settings.get("processing_device", "auto")
        self.worker = ScannerWorker(file_list, scan_mode, threshold, processing_device)
        self.worker.moveToThread(self.worker_thread)
        
        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.scan_finished)
        self.worker.error_occurred.connect(self.scan_error)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.group_found.connect(self.results_widget.add_group)
        if self.worker:
            self.worker.device_info.connect(self.progress_dialog.setDeviceInfo)
        
        self.worker_thread.start()
        self.progress_dialog.exec()

    def update_progress(self, value, text):
        if self.progress_dialog:
            self.progress_dialog.setValue(value)
            self.progress_dialog.setLabelText(text)

    def scan_finished(self):
        if self.progress_dialog and self.progress_dialog.isVisible():
            self.progress_dialog.accept()
            if self.results_widget and self.results_widget.groups:
                self.stacked_widget.setCurrentWidget(self.results_widget)
            else:
                QMessageBox.information(self, "Hoàn tất", "Không tìm thấy file trùng lặp hoặc tương tự nào.")
                self.stacked_widget.setCurrentWidget(self.processing_widget)
        
        if self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait()
        
        self.worker_thread = None
        self.worker = None
        self.is_scanning = False

    def scan_error(self, message):
        if self.progress_dialog:
            self.progress_dialog.accept()
        QMessageBox.critical(self, "Lỗi Quét", message)
        self.stacked_widget.setCurrentWidget(self.processing_widget)
        self.is_scanning = False

    def cancel_scan(self):
        if self.worker:
            self.worker.stop()

    def reset_to_start(self):
        self.processing_widget.reset()
        self.stacked_widget.setCurrentWidget(self.drag_drop_widget)
        
    def show_processing_screen(self):
        self.stacked_widget.setCurrentWidget(self.processing_widget)

    def refresh_processing_screen(self):
        all_files = list(self.processing_widget.file_list)
        remaining_files = [f for f in all_files if os.path.exists(f)]
        
        self.processing_widget.file_list = set(remaining_files)
        self.processing_widget.update_table()
        self.stacked_widget.setCurrentWidget(self.processing_widget)
