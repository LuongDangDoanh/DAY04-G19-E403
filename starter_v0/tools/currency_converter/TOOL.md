---
name: currency_converter
track: core
kind: finance
requires_env: []
inputs: [amount, from_currency, to_currency]
outputs: [tool, amount, from_currency, to_currency, result, rate]
side_effect: false
---
# currency_converter

Chuyển đổi tiền tệ theo tỷ giá hiện tại từ exchangerate.host.

- `amount`: số tiền cần đổi.
- `from_currency`: mã tiền tệ gốc (ví dụ `USD`).
- `to_currency`: mã tiền tệ đích (ví dụ `EUR`).

Khi nào dùng:
- Khi cần đổi nhanh giá trị tiền tệ chính xác.
- Khi muốn trả lời câu hỏi về tỷ giá hiện tại.

Khi không dùng:
- Không dùng cho mục đích giao dịch tài chính nhạy cảm nếu cần xác nhận thêm.
