---
name: pdf_text_extractor
track: core
kind: extract
requires_env: []
inputs: [pdf_path, max_pages]
outputs: [tool, pdf_path, text, page_count, pages_read]
side_effect: false
---
# pdf_text_extractor

Trích xuất văn bản từ file PDF cục bộ.

- `pdf_path`: đường dẫn tới file PDF.
- `max_pages`: số trang tối đa lấy ra.

Khi nào dùng:
- Khi cần lấy nội dung văn bản từ file PDF để đọc hoặc tóm tắt.
- Khi muốn chuyển PDF thành text cho xử lý tiếp.

Khi không dùng:
- Không dùng nếu file PDF chưa có sẵn hoặc cần tải từ web trước.
