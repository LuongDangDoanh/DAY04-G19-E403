---
name: source_quality
track: team
kind: research_quality
requires_env: []
inputs: [url, title, source]
outputs: [tool, url, tier, score, reasons]
side_effect: false
---
# source_quality

Đánh giá nhanh chất lượng và độ ưu tiên của một nguồn đã có metadata.

- `url`: URL của nguồn; bắt buộc.
- `title`: tiêu đề nguồn nếu đã có.
- `source`: tên domain hoặc nguồn hiển thị nếu đã có.

Khi dùng:
- Dùng sau `lookup` hoặc `fetch` khi cần giải thích vì sao một nguồn được ưu tiên.
- Dùng để sắp xếp nguồn, không dùng để khẳng định nội dung bài viết là đúng.

Khi không dùng:
- Không dùng thay cho `lookup`, `fetch`, hoặc kiểm chứng nội dung.
- Không truy cập mạng và không làm thay đổi dữ liệu.
