---
name: csv_summary
track: core
kind: extract
requires_env: []
inputs: [csv_path, max_rows]
outputs: [tool, csv_path, headers, row_count, sample_rows]
side_effect: false
---
# csv_summary

Đọc file CSV cục bộ và trả về tiêu đề, số dòng và mẫu dữ liệu.

- `csv_path`: đường dẫn đến file CSV.
- `max_rows`: số dòng mẫu trả về.

Khi nào dùng:
- Khi cần hiểu nhanh cấu trúc dữ liệu trong file CSV.
- Khi muốn xem ví dụ vài dòng đầu cùng phần header.

Khi không dùng:
- Không dùng nếu CSV cần phân tích sâu hơn hoặc xử lý dữ liệu phức tạp.
