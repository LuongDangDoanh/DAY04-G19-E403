---
name: calculator
track: core
kind: utils
requires_env: []
inputs: [expression]
outputs: [tool, expression, result]
side_effect: false
---
# calculator

Tính toán các biểu thức số học đơn giản.

- `expression`: biểu thức toán học nhập vào.

Khi nào dùng:
- Khi cần tính nhanh các phép cộng, trừ, nhân, chia, lũy thừa, modulo.
- Khi cần trả lời câu hỏi dạng tính toán chính xác.

Khi không dùng:
- Không dùng cho các phép toán đại số phức tạp hoặc ký hiệu toán học không chuẩn.
