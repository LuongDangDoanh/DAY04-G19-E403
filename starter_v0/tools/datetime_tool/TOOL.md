---
name: datetime_tool
track: core
kind: utils
requires_env: []
inputs: [format, utc]
outputs: [tool, utc, value, format]
side_effect: false
---
# datetime_tool

Trả về ngày giờ hiện tại với định dạng tuỳ chọn.

- `format`: kiểu hiển thị ngày giờ.
- `utc`: nếu true thì trả về thời gian UTC.

Khi nào dùng:
- Khi cần trả lời câu hỏi về thời gian hiện tại.
- Khi cần chuẩn hóa định dạng thời gian cho báo cáo.

Khi không dùng:
- Không dùng để xử lý múi giờ phức tạp ngoài UTC/local cơ bản.
