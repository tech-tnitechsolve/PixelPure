# -*- coding: utf-8 -*-

"""
scanner.py (v7)
Module này chứa logic quét file đa tầng.
Đã sửa lỗi import sai tên biến.
"""

import os
import hashlib
import traceback
from pathlib import Path
from collections import defaultdict

import cv2
import faiss
import numpy as np
import torch
from PIL import Image
import imagehash
from PyQt6.QtCore import QObject, pyqtSignal
from transformers import CLIPProcessor, CLIPModel

from config import (
    MODEL_NAME, MAX_L2_DISTANCE,
    IMAGE_EXTS, VIDEO_EXTS, PHASH_HAMMING_DISTANCE_THRESHOLD
)

class ScannerWorker(QObject):
    """
    Worker thực hiện các tác vụ quét nặng trong một luồng riêng.
    """
    progress_updated = pyqtSignal(int, str)
    group_found = pyqtSignal(float, list)
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    device_info = pyqtSignal(str)

    def __init__(self, file_list, scan_mode, similarity_threshold, processing_device):
        super().__init__()
        self.file_list = file_list
        self.scan_mode = scan_mode
        self.similarity_threshold = similarity_threshold
        self.processing_device_setting = processing_device
        self.device = self._determine_device()
        self.is_running = True
        self.model: CLIPModel | None = None
        self.processor: CLIPProcessor | None = None
        self.processed_files = set()

    def _determine_device(self):
        """Xác định thiết bị xử lý dựa trên cài đặt và phần cứng có sẵn."""
        if self.processing_device_setting == 'cuda':
            if torch.cuda.is_available():
                return 'cuda'
            else:
                return 'cpu'
        elif self.processing_device_setting == 'cpu':
            return 'cpu'
        else:
            return "cuda" if torch.cuda.is_available() else "cpu"

    def _load_model(self):
        """Tải model và processor của CLIP."""
        if self.model and self.processor:
            return True
        try:
            self.device_info.emit(f"Đang tải mô hình lên: {self.device.upper()}...")
            self.progress_updated.emit(0, "Đang tải mô hình AI...")
            model_obj = CLIPModel.from_pretrained(MODEL_NAME)
            self.model = model_obj.to(self.device) # type: ignore
            self.processor = CLIPProcessor.from_pretrained(MODEL_NAME)
            self.progress_updated.emit(5, f"Tải mô hình AI thành công trên {self.device.upper()}.")
            return True
        except Exception as e:
            error_msg = (f"Không thể tải mô hình AI: {e}\n\n"
                         "Vui lòng kiểm tra kết nối mạng cho lần chạy đầu tiên, "
                         "hoặc chạy file 'download_model.py' để tải model về trước.")
            self.error_occurred.emit(error_msg)
            return False
    
    def stop(self):
        self.is_running = False

    def run(self):
        try:
            if not self.is_running: return
            self.scan_absolute_duplicates()
            if not self.is_running: return
            self.scan_perceptual_hashes()
            if not self.is_running: return
            if self.scan_mode == 'deep':
                if self._load_model():
                    self.scan_ai_similarity()
        except Exception as e:
            error_msg = (f"Đã xảy ra lỗi không mong muốn trong quá trình quét:\n\n{str(e)}\n\n"
                         f"Chi tiết:\n{traceback.format_exc()}")
            self.error_occurred.emit(error_msg)
        finally:
            self.finished.emit()

    def _get_file_hash(self, filepath, block_size=65536):
        hasher = hashlib.sha256()
        try:
            with open(filepath, 'rb') as f:
                buf = f.read(block_size)
                while len(buf) > 0 and self.is_running:
                    hasher.update(buf)
                    buf = f.read(block_size)
            return hasher.hexdigest() if self.is_running else None
        except (IOError, PermissionError):
            return None

    def scan_absolute_duplicates(self):
        self.progress_updated.emit(10, "Tầng 1: Tìm file trùng lặp tuyệt đối...")
        hashes_by_size = defaultdict(list)
        for file_path in self.file_list:
            if not self.is_running: return
            try:
                if os.path.getsize(file_path) > 0:
                    hashes_by_size[os.path.getsize(file_path)].append(file_path)
            except OSError:
                continue

        final_hashes = defaultdict(list)
        for size, files in hashes_by_size.items():
            if not self.is_running or len(files) < 2: continue
            for file_path in files:
                if file_hash := self._get_file_hash(file_path):
                    final_hashes[file_hash].append(file_path)

        for files in final_hashes.values():
            if not self.is_running: return
            if len(files) > 1:
                self.group_found.emit(100.0, files)
                self.processed_files.update(files)

    def scan_perceptual_hashes(self):
        self.progress_updated.emit(25, "Tầng 2: Phân tích ảnh bằng pHash...")
        image_files = [f for f in self.file_list if f not in self.processed_files and Path(f).suffix.lower() in IMAGE_EXTS]
        if len(image_files) < 2: return

        hashes = []
        for file_path in image_files:
            if not self.is_running: return
            try:
                with Image.open(file_path) as img:
                    hashes.append((file_path, imagehash.phash(img)))
            except Exception:
                continue
        
        local_processed = set()
        for i in range(len(hashes)):
            if not self.is_running or i in local_processed: continue
            path1, hash1 = hashes[i]
            group, distances = [path1], []

            for j in range(i + 1, len(hashes)):
                if j in local_processed: continue
                path2, hash2 = hashes[j]
                if (dist := hash1 - hash2) <= PHASH_HAMMING_DISTANCE_THRESHOLD:
                    group.append(path2)
                    distances.append(dist)
                    local_processed.add(j)

            if len(group) > 1:
                avg_dist = sum(distances) / len(distances)
                score = max(0, 100 * (1 - avg_dist / 64.0))
                self.group_found.emit(score, group)
                self.processed_files.update(group)
                local_processed.add(i)

    def _get_features_from_image(self, image: Image.Image):
        if not self.model or not self.processor:
            return None
        try:
            inputs = self.processor(images=image, return_tensors="pt")
            pixel_values = inputs.pixel_values.to(self.device, dtype=torch.float32)
            with torch.no_grad():
                features = self.model.get_image_features(pixel_values=pixel_values)
            return features.cpu().numpy().flatten()
        except Exception:
            return None

    def _extract_image_features(self, image_path: str):
        try:
            with Image.open(image_path).convert("RGB") as image:
                return self._get_features_from_image(image)
        except Exception:
            return None

    def _extract_video_features(self, video_path: str):
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened(): return None
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_indices = np.linspace(0, total_frames - 1, min(5, total_frames), dtype=int)
            
            video_features = []
            for idx in frame_indices:
                if not self.is_running: break
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                if ret:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(frame_rgb)
                    if (features := self._get_features_from_image(pil_img)) is not None:
                        video_features.append(features)
            
            cap.release()
            if video_features and self.is_running:
                return np.mean(video_features, axis=0).flatten()
            return None
        except Exception:
            return None

    def _extract_features(self, file_path):
        ext = Path(file_path).suffix.lower()
        if ext in IMAGE_EXTS:
            return self._extract_image_features(file_path)
        elif ext in VIDEO_EXTS:
            return self._extract_video_features(file_path)
        return None

    def scan_ai_similarity(self):
        self.progress_updated.emit(50, "Tầng 3: Phân tích sâu bằng AI...")
        media_files = [f for f in self.file_list if f not in self.processed_files and Path(f).suffix.lower() in IMAGE_EXTS + VIDEO_EXTS]
        if len(media_files) < 2: return

        features_list, path_list = [], []
        for i, file_path in enumerate(media_files):
            if not self.is_running: return
            self.progress_updated.emit(50 + int((i / len(media_files)) * 45), f"Phân tích AI: {Path(file_path).name}")
            if (features := self._extract_features(file_path)) is not None:
                features_list.append(features)
                path_list.append(file_path)

        if not self.is_running or not features_list: return

        self.progress_updated.emit(95, "Xây dựng chỉ mục và tìm kiếm AI...")
        features_matrix = np.array(features_list).astype('float32')
        if features_matrix.ndim != 2: return

        dimension = features_matrix.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(features_matrix) # type: ignore

        local_processed = set()
        num_paths = len(path_list)
        for i in range(num_paths):
            if not self.is_running or i in local_processed: continue
            
            query = np.array([features_matrix[i]])
            distances, indices = index.search(query, k=min(10, num_paths)) # type: ignore
            
            group, scores = [path_list[i]], []
            for j, dist in zip(indices[0], distances[0]):
                if i == j or j in local_processed: continue
                if (score := max(0, 100 * (1 - dist / MAX_L2_DISTANCE))) >= self.similarity_threshold:
                    group.append(path_list[j])
                    scores.append(score)
                    local_processed.add(j)
            
            if len(group) > 1:
                self.group_found.emit(sum(scores) / len(scores), group)
                self.processed_files.update(group)
                local_processed.add(i)
