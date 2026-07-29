---
name: unit_converter
track: core
kind: utils
requires_env: []
inputs: [value, from_unit, to_unit, category]
outputs: [tool, value, from_unit, to_unit, category, result]
side_effect: false
---
# unit_converter

Chuyển đổi giữa các đơn vị phổ biến.

- `value`: giá trị số ban đầu.
- `from_unit`: đơn vị gốc.
- `to_unit`: đơn vị cần chuyển.
- `category`: tùy chọn, ví dụ `length`, `weight`, `temperature`.

Khi nào dùng:
- Khi cần chuyển đổi đơn vị nhanh và chính xác.
- Khi câu hỏi có kiểu "bao nhiêu km trong 5 dặm" hoặc "37°C bằng bao nhiêu °F".

Khi không dùng:
- Không dùng cho chuyển đổi đơn vị đặc thù nếu không xác định được category rõ ràng.
