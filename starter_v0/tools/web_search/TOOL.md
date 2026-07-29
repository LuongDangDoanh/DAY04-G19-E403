---
name: web_search
track: core
kind: search
requires_env: []
inputs: [query, max_results, region]
outputs: [tool, query, items]
side_effect: false
---
# web_search

Tìm thông tin nhanh trên web bằng DuckDuckGo Instant Answer API.

- `query`: nội dung cần tìm.
- `max_results`: số kết quả tối đa.
- `region`: chỉ định vùng tìm kiếm, dùng để giúp agent lựa chọn công cụ.

Khi nào dùng:
- Khi cần một tìm kiếm web nhanh, tổng hợp kết quả sơ bộ.
- Khi cần lấy tiêu đề, URL và đoạn tóm tắt cho các nguồn phù hợp.

Khi không dùng:
- Không dùng để đọc nội dung chi tiết của một trang; dùng `webpage_reader` hoặc `fetch`.
