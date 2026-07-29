# Day 04 Lab v2 Report — Research Agent

## Team

- Team: Bro
- Members: 1
- Provider/model: openrouter / openai/gpt-4o-mini

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent: tìm tin theo từ khóa / theo tài khoản Twitter, đọc URL, tổng hợp thành digest, tra cứu arXiv papers và company policy nội bộ.

**Link dùng thử:** http://localhost:8501 (Streamlit UI)

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | Hỏi lại người dùng khi thiếu thông tin hoặc cần xác nhận | không |
| timeline | Lấy bài đăng gần đây của một tài khoản Twitter | không |
| social_search | Tìm tweet theo chủ đề/từ khóa | không |
| lookup | Tra cứu thông tin trên web (Tavily) | không |
| fetch | Đọc nội dung một URL (Firecrawl) | không |
| format | Trình bày dữ liệu thành markdown digest | không |
| papers | Tìm paper trên arXiv | không |
| paper_text | Đọc nội dung PDF arXiv | không |
| policy | Tra cứu company policy nội bộ | không |
| send | Gửi tin lên Telegram | không |

## A3. Câu hỏi mẫu để thử

1. "Tweet mới nhất của Sam Altman là gì?"
2. "Tin tức AI hôm nay có gì nổi bật?"
3. "Tóm tắt bài này giúp mình: https://openai.com/blog/gpt-5"
4. "Tìm paper arXiv về AI safety và kiểm tra policy công ty về source citation"
5. "Giải giúp mình bài toán tích phân" → agent từ chối đúng cách

## A4. Kịch bản demo đã rehearse

| Scenario | Tool trace cần thấy | Câu chuyện cải thiện version | Fallback run/transcript |
|---|---|---|---|
| Research + digest | lookup → format | v0: agent search nhưng không format. v3: agent search + format đúng | runs/v3_B_base_*.json |
| Missing handle → clarify → timeline | clarify → timeline | v0-v1: agent đoán bừa handle. v2: agent gọi clarify | runs/v2_B_base_*.json |
| Confirm before send | clarify(yes_no) → send | v0: clarify(text) sai response_type. v1-v3: clarify(yes_no) đúng | runs/v3_B_base_*.json |
| Multi-turn switch source | social_search (bỏ lookup) | v2: agent gọi cả 2. v3: chỉ gọi đúng tool mới | runs/v3_B_base_*.json |
| Policy lookup | policy(source_citation) | v0: không biết policy. v3: policy với đúng policy_area | runs/v3_B_group_*.json |

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version evidence

| Version | Prompt/tool change | Hypothesis | Metric name | Before | After | Run File |
|---|---|---|---|---|---|---|
| v0 | Baseline (system prompt + tools.yaml mặc định) | — | case_accuracy | — | 0.95 | runs/v0_B_base_openrouter_20260729T104654822426.json |
| v1 | Thêm clarify(yes_no) trước send + cập nhật tools.yaml clarify description | Agent sẽ dùng response_type=yes_no trước khi send | case_accuracy | 0.95 | 0.85 | runs/v1_B_base_openrouter_20260729T104831674160.json |
| v2 | Thêm CRITICAL section: NEVER guess, always clarify. Cập nhật fetch description. | Agent không đoán bừa khi thiếu thông tin | case_accuracy | 0.85 | 0.95 | runs/v2_B_base_openrouter_20260729T105003548932.json |
| v3 | Thêm multi-turn rule: không gọi tool cũ khi user bỏ nguồn | Agent không gọi tool thừa khi chuyển nguồn | case_accuracy | 0.95 | 1.0 | runs/v3_B_base_openrouter_20260729T105120785220.json |

## B2. Failure analysis

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R12 (v0) | wrong_boundary | clarify(response_type="text") | Agent hỏi nội dung thay vì xác nhận yes/no trước send | Thêm rule: send → clarify(yes_no) trước |
| R10 (v1) | missing_info | timeline(screenname="sama") | Agent đoán handle khi không được cung cấp | Thêm CRITICAL: NEVER guess, always clarify |
| R11 (v1) | missing_info | fetch(url="https://example.com") | Agent đoán URL khi không được cung cấp | Thêm fetch description: không guess URL |
| R12 (v1) | wrong_boundary | clarify(response_type="text") | Vẫn sai response_type mặc dù đã thêm rule | Tăng cường prompt với CRITICAL section |
| M06 (v2) | wrong_tool | lookup + social_search | Agent gọi cả 2 tool khi user bảo bỏ Twitter | Thêm multi-turn rule: không gọi tool cũ |

## B3. Team eval cases

5 single-turn + 5 multi-turn:

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_direct_timeline_routing | Map Joe Biden → handle JoeBiden + limit=3 | timeline(screenname="JoeBiden", limit=3) | PASS |
| G02_arxiv_recent | sort_by=lastUpdatedDate cho paper mới nhất | papers(sort_by="lastUpdatedDate") | PASS |
| G03_name_mapping_unknown | Map Satya Nadella không có trong prompt mẫu | timeline(screenname="satyanadella") | PASS |
| G04_out_of_scope_weather | Thời tiết ngoài phạm vi → từ chối | no_tool, refuse | PASS |
| G05_missing_both_handle_and_content | Thiếu cả handle và query → clarify | clarify(response_type="text") | PASS |
| G06_refine_search | Carry topic=news, timeframe=day, đổi query | lookup(query="GPT-5", topic="news", timeframe="day") | PASS |
| G07_clarify_then_confirm_send | User confirm → send(confirmed=True) | send(text="AI is the future!") | PASS |
| G08_switch_source | Bỏ web → chỉ social_search | social_search(query="Claude 4") | PASS |
| G09_policy_external_publishing | policy với policy_area=external_publishing | policy(policy_area="external_publishing") | PASS |
| G10_parallel_paper_and_policy | Song song papers + policy | papers + policy(source_citation) | PASS |

## B4. Live chat evidence

| Scenario/Turn | Version | Tool Calls + Args | Transcript/Run | Outcome |
|---|---|---|---|---|
| Research bình thường | v3 | lookup(topic=news, timeframe=day) | transcripts/ | Tìm được tin tức AI |
| Thiếu thông tin + bổ sung | v3 | clarify → timeline | transcripts/ | Hỏi handle, sau đó lấy đúng timeline |
| Xác nhận trước gửi | v3 | clarify(yes_no) → send | transcripts/ | Hỏi xác nhận trước, gửi sau khi đồng ý |

## B5. Tool capability evidence

| Category | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Core: clarify | eval_base.json R10-R12 | Hỏi lại khi thiếu thông tin, xác nhận yes_no | Cần prompt rule rõ ràng để không guess |
| Core: timeline | eval_base.json R01, R05 | Lấy tweet đúng handle, đúng limit | Name mapping cần cập nhật thủ công |
| Core: social_search | eval_base.json R02, R07 | Search tweet theo chủ đề, phân biệt Top/Latest | — |
| Core: lookup | eval_base.json R03, R06 | Tra cứu web với topic/timeframe chính xác | — |
| Core: fetch | eval_base.json R04 | Đọc URL | Không guess URL khi thiếu |
| Core: format | eval_group.json G01 | Format dữ liệu thành digest | — |
| Bonus: papers | eval_group.json G02, G10 | Tìm arXiv papers | — |
| Bonus: policy | eval_group.json G09, G10 | Tra cứu company policy | Cần chỉ định đúng policy_area |

## B6. Reflection

- **Which fixes belonged in `system_prompt.md`?**
  - CRITICAL section: NEVER guess missing info, always clarify
  - clarify(response_type="yes_no") before send actions
  - Multi-turn rules: carry over params, drop old sources, no duplicate tool calls
  - Out-of-scope examples: weather, personal advice
  - policy_area guidance for policy tool

- **Which fixes belonged in `tools.yaml`?**
  - clarify description: specify when to use each response_type
  - fetch description: clarify that it needs a valid URL, not to guess

- **Which failure needed manual review instead of automatic grading?**
  - G01 (format tool routing): Single-turn eval expecting format without prior context — the case had to be redesigned because format needs pre-existing data
  - G02 (sort_by choice): "published gần đây" vs "lastUpdatedDate" vs "submittedDate" — semantic ambiguity needs human judgment

- **What would you improve next?**
  - Add more name-to-handle mappings for common Twitter accounts
  - Support multi-turn context across eval cases (not just single-turn per case)
  - Add edge case handling for tool execution errors (rate limits, API failures)
  - Add streaming response in UI for better UX
  - Implement more robust parallel tool call routing for 3+ tools
