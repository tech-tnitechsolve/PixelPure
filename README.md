# PixelPure

PixelPure là một dự án Python dùng để xử lý hình ảnh, quét và phân tích các file ảnh.

## Mục đích

## Cấu trúc dự án

# PixelPure



## Tính năng nổi bật
- Quét và phát hiện ảnh trùng lặp hoặc tương tự trong thư mục.
- Hỗ trợ nhiều định dạng ảnh phổ biến (PNG, JPG, JPEG, BMP, ...).
- Giao diện người dùng hiện đại, dễ sử dụng với PyQt6.
- Tùy chọn chế độ quét nhanh hoặc sâu, tối ưu cho từng nhu cầu.
- Hỗ trợ chọn thiết bị xử lý (CPU, CUDA nếu có).
- Xem trước ảnh, chọn ảnh giữ lại/xóa, thao tác hàng loạt.

## Cấu trúc dự án
```
PixelPure/
├── main.py              # Điểm khởi động ứng dụng
├── ui.py                # Giao diện người dùng
├── scanner.py           # Logic quét và phân tích ảnh
├── config.py            # Cấu hình chung
├── download_model.py    # Tải mô hình AI (nếu cần)
├── requirements.txt     # Thư viện phụ thuộc
├── oke/                 # Thư mục chứa ảnh mẫu
└── ...
```

## Hướng dẫn cài đặt & sử dụng
1. **Cài đặt Python >= 3.10**
2. **Cài đặt thư viện:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Chạy ứng dụng:**
   ```bash
   python main.py
   ```
4. Làm theo hướng dẫn trên giao diện.

## Đóng góp & liên hệ
- Đóng góp qua Pull Request hoặc Issue trên GitHub.
- Liên hệ: [TNI Tech Solutions](mailto:info@tnitechsolutions.com)

## License
MIT License. Xem chi tiết trong file LICENSE nếu có.

---
© 2025 TNI Tech Solutions. Dành cho mục đích học tập, nghiên cứu và phát triển cộng đồng.
