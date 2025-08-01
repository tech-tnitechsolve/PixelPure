# -*- coding: utf-8 -*-

"""
download_model.py
Script này dùng để tải về và cache lại model AI (CLIP) từ Hugging Face.
Hãy chạy script này một lần có kết nối mạng để ứng dụng có thể
hoạt động offline sau này.
"""

try:
    from transformers import CLIPProcessor, CLIPModel
    from config import MODEL_NAME
    print(f"Bắt đầu tải model: {MODEL_NAME}")
    print("Quá trình này có thể mất vài phút tùy thuộc vào tốc độ mạng...")

    # Tải và cache processor
    processor = CLIPProcessor.from_pretrained(MODEL_NAME)
    print("Đã tải xong Processor.")

    # Tải và cache model
    model = CLIPModel.from_pretrained(MODEL_NAME)
    print("Đã tải xong Model.")

    print("\n--------------------------------------------------")
    print("TẢI MODEL THÀNH CÔNG!")
    print(f"Model '{MODEL_NAME}' đã được lưu vào cache.")
    print("Bây giờ bạn có thể chạy ứng dụng PixelPure ở chế độ offline.")
    print("--------------------------------------------------")

except ImportError:
    print("Lỗi: Vui lòng cài đặt thư viện 'transformers' và 'torch' trước.")
    print("Chạy lệnh: pip install transformers torch")
except Exception as e:
    print(f"Đã xảy ra lỗi trong quá trình tải model: {e}")
    print("Vui lòng kiểm tra lại kết nối mạng và thử lại.")

