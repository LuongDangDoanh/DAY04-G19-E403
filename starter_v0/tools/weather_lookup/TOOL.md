---
name: weather_lookup
track: core
kind: info
requires_env: []
inputs: [location, units]
outputs: [tool, location, weather]
side_effect: false
---
# weather_lookup

Lấy thời tiết hiện tại cho một địa điểm cụ thể.

- `location`: tên thành phố hoặc địa điểm.
- `units`: `metric` hoặc `imperial`.

Khi nào dùng:
- Khi cần trả lời câu hỏi về điều kiện thời tiết hiện tại.
- Khi cần dữ liệu nhiệt độ/độ ẩm/gió ngay lập tức.

Khi không dùng:
- Không dùng cho dự báo dài hạn hoặc phân tích khí tượng chuyên sâu.
