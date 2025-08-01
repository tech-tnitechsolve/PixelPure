# -*- coding: utf-8 -*-

"""
ui.py (v5)
Module này chứa tất cả các thành phần giao diện người dùng (UI) của ứng dụng.
Đã sửa các lỗi Pylance liên quan đến ghi đè phương thức và kiểm tra None.
"""

import os
import shutil
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QStackedWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QProgressDialog,
    QGroupBox, QHBoxLayout, QScrollArea, QMessageBox, QRadioButton, QStyle,
    QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QPixmap, QIcon, QDragEnterEvent, QDropEvent
from send2trash import send2trash

from config import (
    IMAGE_EXTS, VIDEO_EXTS, OTHER_EXTS, SLOGAN, APP_NAME,
    HIGH_SIMILARITY_SCORE
)
from scanner import ScannerWorker


class DragDropWidget(QWidget):
    """Widget cho phép kéo thả file và thư mục vào."""
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
        """SỬA LỖI: Đổi tên tham số thành 'a0' để tương thích và kiểm tra None."""
        if a0:
            mime_data = a0.mimeData()
            if mime_data and mime_data.hasUrls():
                a0.acceptProposedAction()
            else:
                a0.ignore()

    def dropEvent(self, a0: QDropEvent | None):
        """SỬA LỖI: Đổi tên tham số thành 'a0' để tương thích và kiểm tra None."""
        if a0:
            mime_data = a0.mimeData()
            if mime_data and mime_data.hasUrls():
                urls = mime_data.urls()
                paths = [url.toLocalFile() for url in urls]
                self.files_dropped.emit(paths)
            else:
                a0.ignore()


class FileProcessingWidget(QWidget):
    """Widget hiển thị danh sách file và các tùy chọn quét."""
    start_scan_signal = pyqtSignal(list)
    reset_signal = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
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
        self.table.cellClicked.connect(self.toggle_checkbox)
        
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
        
        scan_group = QGroupBox("Tùy Chọn")
        scan_layout = QVBoxLayout(scan_group)
        scan_layout.addWidget(QLabel("Chế độ quét sâu sẽ được thực hiện."))
        
        btn_start = QPushButton("Bắt Đầu Quét Sâu")
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

    def dragEnterEvent(self, a0: QDragEnterEvent | None):
        """SỬA LỖI: Đổi tên tham số thành 'a0' để tương thích và kiểm tra None."""
        if a0:
            mime_data = a0.mimeData()
            if mime_data and mime_data.hasUrls():
                a0.acceptProposedAction()
            else:
                a0.ignore()

    def dropEvent(self, a0: QDropEvent | None):
        """SỬA LỖI: Đổi tên tham số thành 'a0' để tương thích và kiểm tra None."""
        if a0:
            mime_data = a0.mimeData()
            if mime_data and mime_data.hasUrls():
                urls = mime_data.urls()
                paths = [url.toLocalFile() for url in urls]
                self.add_paths(paths)
            else:
                a0.ignore()

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
            elif os.path.isfile(path_str):
                 if Path(path_str).suffix.lower() in supported_exts:
                    all_files_in_drop.add(path_str)
        
        new_files = all_files_in_drop - self.file_list
        if new_files:
            self.file_list.update(new_files)
            self.update_table()

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Chọn file", "", "All Files (*)")
        if files: self.add_paths(files)
            
    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục")
        if folder: self.add_paths([folder])

    def update_table(self):
        self.table.setRowCount(0)
        total_size, image_count, video_count, other_count = 0, 0, 0, 0
        sorted_list = sorted(list(self.file_list))
        self.table.setRowCount(len(sorted_list))

        for row_position, file_path in enumerate(sorted_list):
            chk_box_item = QTableWidgetItem()
            chk_box_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            chk_box_item.setCheckState(Qt.CheckState.Checked)
            self.table.setItem(row_position, 0, chk_box_item)

            p = Path(file_path)
            try:
                size = os.path.getsize(file_path)
            except FileNotFoundError:
                continue
            total_size += size
            ext = p.suffix.lower()
            file_type = "Khác"
            if ext in IMAGE_EXTS: file_type, image_count = "Ảnh", image_count + 1
            elif ext in VIDEO_EXTS: file_type, video_count = "Video", video_count + 1
            else: other_count += 1

            self.table.setItem(row_position, 1, QTableWidgetItem(p.name))
            self.table.setItem(row_position, 2, QTableWidgetItem(f"{size / 1024 / 1024:.2f} MB"))
            self.table.setItem(row_position, 3, QTableWidgetItem(file_type))
            self.table.setItem(row_position, 4, QTableWidgetItem(file_path))
        
        self.lbl_total_files.setText(f"Tổng số file: {self.table.rowCount()}")
        self.lbl_total_size.setText(f"Tổng dung lượng: {total_size / 1024 / 1024:.2f} MB")
        self.lbl_total_images.setText(f"Tổng số ảnh: {image_count}")
        self.lbl_total_videos.setText(f"Tổng số video: {video_count}")
        self.lbl_total_others.setText(f"Tổng số file khác: {other_count}")

    def toggle_checkbox(self, row, column):
        if column == 0:
            if item := self.table.item(row, 0):
                item.setCheckState(Qt.CheckState.Unchecked if item.checkState() == Qt.CheckState.Checked else Qt.CheckState.Checked)

    def select_all(self):
        for i in range(self.table.rowCount()):
            if item := self.table.item(i, 0):
                item.setCheckState(Qt.CheckState.Checked)

    def deselect_all(self):
        for i in range(self.table.rowCount()):
            if item := self.table.item(i, 0):
                item.setCheckState(Qt.CheckState.Unchecked)

    def get_selected_files(self):
        selected = []
        for i in range(self.table.rowCount()):
            if (check_item := self.table.item(i, 0)) and \
               (path_item := self.table.item(i, 4)) and \
               check_item.checkState() == Qt.CheckState.Checked:
                selected.append(path_item.text())
        return selected

    def start_scan(self):
        selected_files = self.get_selected_files()
        if not selected_files:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn ít nhất một file để quét.")
            return
        self.start_scan_signal.emit(selected_files)

    def reset(self):
        self.file_list.clear()
        self.update_table()


class ResultsWidget(QWidget):
    """Widget hiển thị kết quả quét và các tùy chọn xử lý."""
    back_signal = pyqtSignal()
    rescan_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.groups = {}
        main_layout = QVBoxLayout(self)
        top_bar_layout = QHBoxLayout()
        btn_back = QPushButton("Quay Lại")
        btn_back.clicked.connect(self.back_signal.emit)
        self.lbl_results_summary = QLabel("Kết quả quét:")
        self.lbl_results_summary.setStyleSheet("font-weight: bold; font-size: 16px;")
        top_bar_layout.addWidget(btn_back)
        top_bar_layout.addWidget(self.lbl_results_summary)
        top_bar_layout.addStretch()
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.results_layout = QVBoxLayout(self.scroll_content)
        self.results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.scroll_content)
        
        bottom_bar_layout = QHBoxLayout()
        btn_delete = QPushButton("Xóa File Đã Chọn")
        btn_delete.setObjectName("DeleteButton")
        btn_group_move = QPushButton("Nhóm và Di Chuyển")
        btn_group_move.setObjectName("GroupButton")
        
        btn_delete.clicked.connect(self.delete_selected)
        btn_group_move.clicked.connect(self.group_and_move_selected)
        
        bottom_bar_layout.addStretch()
        bottom_bar_layout.addWidget(btn_group_move)
        bottom_bar_layout.addWidget(btn_delete)
        
        main_layout.addLayout(top_bar_layout)
        main_layout.addWidget(self.scroll_area)
        main_layout.addLayout(bottom_bar_layout)

    def clear_results(self):
        while self.results_layout.count():
            child = self.results_layout.takeAt(0)
            if child and (widget := child.widget()):
                widget.deleteLater()
        self.groups.clear()

    def add_group(self, score, files):
        group_id = f"group_{len(self.groups)}"
        
        if score == 100.0:
            group_type = "Trùng lặp tuyệt đối"
        elif score >= HIGH_SIMILARITY_SCORE:
            group_type = "Trùng lặp cao"
        else:
            group_type = "Tương tự"

        title = f"Nhóm {len(self.groups) + 1}: {group_type} ({score:.1f}%)"
        group_box = QGroupBox(title)
        group_layout = QVBoxLayout(group_box)
        
        file_widgets = []
        try:
            sorted_files = sorted(files, key=lambda x: os.path.getsize(x) if os.path.exists(x) else -1, reverse=True)
        except FileNotFoundError:
            sorted_files = files

        for file_path in sorted_files:
            if not os.path.exists(file_path): continue
            p = Path(file_path)
            file_widget = QWidget()
            file_layout = QHBoxLayout(file_widget)
            cb = QRadioButton(f"Giữ lại file này")
            thumb_label = QLabel()
            thumb_label.setFixedSize(80, 80)
            thumb_label.setStyleSheet("border: 1px solid #4a5060; background-color: #23272e; border-radius: 5px;")
            thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            ext = p.suffix.lower()
            if ext in IMAGE_EXTS:
                pixmap = QPixmap(file_path)
                thumb_label.setPixmap(pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                thumb_label.setText(ext.upper()[1:])

            info_layout = QVBoxLayout()
            info_layout.addWidget(QLabel(f"<b>{p.name}</b>"))
            info_layout.addWidget(QLabel(f"{os.path.getsize(file_path) / 1024 / 1024:.2f} MB"))
            info_layout.addWidget(QLabel(f"<i>{p.parent}</i>"))

            file_layout.addWidget(cb)
            file_layout.addWidget(thumb_label)
            file_layout.addLayout(info_layout)
            group_layout.addWidget(file_widget)
            file_widgets.append((cb, file_path))
        
        if file_widgets:
            file_widgets[0][0].setChecked(True)
            self.results_layout.addWidget(group_box)
            self.groups[group_id] = file_widgets

    def get_files_for_action(self):
        to_action = []
        for group_id, file_widgets in self.groups.items():
            kept_file = next((path for cb, path in file_widgets if cb.isChecked()), None)
            for cb, path in file_widgets:
                if path != kept_file:
                    to_action.append(path)
        return to_action

    def delete_selected(self):
        files_to_delete = self.get_files_for_action()
        if not files_to_delete:
            QMessageBox.information(self, "Thông báo", "Không có file nào được chọn để xóa.")
            return

        reply = QMessageBox.question(self, "Xác nhận Xóa",
                                     f"Bạn có chắc muốn chuyển {len(files_to_delete)} file vào thùng rác không?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            success_count, errors = 0, []
            for f in files_to_delete:
                try:
                    send2trash(f)
                    success_count += 1
                except Exception as e:
                    errors.append(f"{Path(f).name}: {e}")
            
            msg = f"Đã chuyển {success_count} file vào thùng rác thành công."
            if errors:
                msg += f"\n\nLỗi trên các file sau:\n" + "\n".join(errors)
                QMessageBox.warning(self, "Hoàn tất với lỗi", msg)
            else:
                QMessageBox.information(self, "Thành công", msg)
            self.rescan_signal.emit()

    def group_and_move_selected(self):
        dest_folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục đích để nhóm và di chuyển file")
        if not dest_folder: return

        files_to_move = self.get_files_for_action()
        if not files_to_move:
            QMessageBox.information(self, "Thông báo", "Không có file nào được chọn để di chuyển.")
            return
        
        reply = QMessageBox.question(self, "Xác nhận Di Chuyển",
                                     f"Bạn có chắc muốn di chuyển và đổi tên {len(files_to_move)} file không?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes: return

        success_count, errors = 0, []
        for group_idx, (group_id, file_widgets) in enumerate(self.groups.items()):
            kept_file = next((path for cb, path in file_widgets if cb.isChecked()), None)
            
            file_counter = 1
            for cb, path in file_widgets:
                if path == kept_file: continue
                
                original_path = Path(path)
                try:
                    new_name = f"nhom_{group_idx + 1}({file_counter}){original_path.suffix}"
                    destination_path = os.path.join(dest_folder, new_name)
                    
                    while os.path.exists(destination_path):
                        file_counter += 1
                        new_name = f"nhom_{group_idx + 1}({file_counter}){original_path.suffix}"
                        destination_path = os.path.join(dest_folder, new_name)

                    shutil.move(path, destination_path)
                    success_count += 1
                    file_counter += 1
                except Exception as e:
                    errors.append(f"{original_path.name}: {e}")

        msg = f"Đã di chuyển và đổi tên thành công {success_count} file."
        if errors:
            msg += f"\n\nLỗi trên các file sau:\n" + "\n".join(errors)
            QMessageBox.warning(self, "Hoàn tất với lỗi", msg)
        else:
            QMessageBox.information(self, "Thành công", msg)
        self.rescan_signal.emit()


class MainWindow(QMainWindow):
    """Cửa sổ chính của ứng dụng."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} - {SLOGAN}")
        self.setGeometry(100, 100, 1200, 800)
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        self.drag_drop_widget = DragDropWidget()
        self.processing_widget = FileProcessingWidget()
        self.results_widget = ResultsWidget()
        
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

    def handle_files_dropped(self, paths):
        self.processing_widget.add_paths(paths)
        self.stacked_widget.setCurrentWidget(self.processing_widget)

    def start_scan(self, file_list):
        if self.is_scanning:
            QMessageBox.information(self, "Đang xử lý", "Một tiến trình quét đang chạy. Vui lòng đợi hoàn tất.")
            return
            
        self.is_scanning = True
        self.results_widget.clear_results()
        
        self.progress_dialog = QProgressDialog("Đang chuẩn bị quét...", "Hủy", 0, 100, self)
        self.progress_dialog.setWindowTitle("Đang Xử Lý")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        
        self.worker_thread = QThread()
        self.worker = ScannerWorker(file_list)
        self.worker.moveToThread(self.worker_thread)
        
        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.scan_finished)
        self.worker.error_occurred.connect(self.scan_error)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.group_found.connect(self.results_widget.add_group)
        self.progress_dialog.canceled.connect(self.cancel_scan)
        
        self.worker_thread.start()
        self.progress_dialog.show()

    def update_progress(self, value, text):
        if self.progress_dialog:
            self.progress_dialog.setValue(value)
            self.progress_dialog.setLabelText(text)

    def scan_finished(self):
        if self.progress_dialog and not self.progress_dialog.wasCanceled():
            self.progress_dialog.setValue(100)
            self.progress_dialog.close()
            if self.results_widget.groups:
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
            self.progress_dialog.close()
        QMessageBox.critical(self, "Lỗi Quét", message)
        self.stacked_widget.setCurrentWidget(self.processing_widget)
        self.is_scanning = False

    def cancel_scan(self):
        if self.worker: self.worker.stop()

    def reset_to_start(self):
        self.processing_widget.reset()
        self.stacked_widget.setCurrentWidget(self.drag_drop_widget)
        
    def show_processing_screen(self):
        self.stacked_widget.setCurrentWidget(self.processing_widget)

    def refresh_processing_screen(self):
        """Cập nhật lại danh sách file sau khi thực hiện hành động."""
        all_files = list(self.processing_widget.file_list)
        remaining_files = [f for f in all_files if os.path.exists(f)]
        
        self.processing_widget.file_list = set(remaining_files)
        self.processing_widget.update_table()
        self.stacked_widget.setCurrentWidget(self.processing_widget)
