---
name: markdown_summarizer
track: core
kind: summarize
requires_env: []
inputs: [markdown_text, max_sentences]
outputs: [tool, summary, sentence_count]
side_effect: false
---
# markdown_summarizer

Tóm tắt nội dung Markdown bằng cách lấy các câu đề mục đầu.

- `markdown_text`: văn bản Markdown cần tóm tắt.
- `max_sentences`: số câu tóm tắt tối đa.

Khi nào dùng:
- Khi cần trích xuất ý chính nhanh từ Markdown.
- Khi muốn có phiên bản ngắn gọn của tài liệu hoặc ghi chú.

Khi không dùng:
- Không dùng khi cần phân tích ngữ nghĩa sâu hoặc tóm tắt nhiều đoạn phức tạp.
