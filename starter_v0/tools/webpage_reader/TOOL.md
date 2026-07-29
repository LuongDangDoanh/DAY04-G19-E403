---
name: webpage_reader
track: core
kind: fetch
requires_env: []
inputs: [url, max_chars]
outputs: [tool, url, title, summary]
side_effect: false
---
# webpage_reader

Đọc nội dung văn bản thô từ một trang web và trả về tiêu đề cùng tóm tắt text.

- `url`: địa chỉ trang cần đọc.
- `max_chars`: giới hạn ký tự trả về.

Khi nào dùng:
- Khi cần đọc nhanh nội dung web từ một URL cụ thể.
- Khi muốn trích xuất nội dung thô thay vì chỉ lấy metadata.

Khi không dùng:
- Không dùng khi chỉ cần tìm lướt web; dùng `web_search`.
- Không dùng để gửi yêu cầu web nhạy cảm nếu cần xác nhận dữ liệu.
