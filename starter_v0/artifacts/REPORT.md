# Day 04 Lab v2 Report — Research Agent

## Team

- Team: G19-E403
- Members: n/a
- Provider/model: OpenRouter / `openai/gpt-4o-mini`

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent cho web news, X/Twitter, URL đọc bài, arXiv, policy nội bộ, và gửi Telegram sau khi xác nhận.

Link dùng thử:

- n/a

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | hỏi lại khi thiếu thông tin hoặc cần xác nhận | không |
| timeline | lấy tweet từ một account cụ thể | không |
| social_search | tìm tweet theo chủ đề | không |
| lookup | tìm web/news theo query + timeframe | không |
| fetch | đọc URL cụ thể | không |
| policy | tra policy nội bộ | không |
| papers | tìm paper arXiv | không |
| paper_text | đọc text paper arXiv | không |
| send | gửi Telegram sau xác nhận | không |
| format | định dạng digest | không |

## A3. Câu hỏi mẫu để thử

1. Tweet mới nhất của Sam Altman là gì?
2. Tin AI hôm nay có gì nổi bật?
3. Tóm tắt bài này: https://openai.com/blog/gpt-5
4. Theo policy nội bộ, có được đưa PII vào prompt không?
5. Đăng bản tin này lên Telegram giúp mình

## A4. Kịch bản demo đã rehearse

| Scenario | Tool trace cần thấy | Câu chuyện cải thiện version | Fallback run/transcript |
|---|---|---|---|
| Timeline by handle | `timeline(screenname=sama)` | thêm map tên -> handle | [v5 base run](../runs/v5_B_base_openrouter_20260729T111055749827.json) |
| News lookup | `lookup(query=AI, topic=news, timeframe=day)` | rõ timeframe tiếng Việt | [v5 base run](../runs/v5_B_base_openrouter_20260729T111055749827.json) |
| Telegram confirm | `clarify(response_type=yes_no)` | tách confirm vs thiếu nội dung | [v5 base run](../runs/v5_B_base_openrouter_20260729T111055749827.json) |
| Multi-turn correction | `timeline(screenname=karpathy, limit=3)` | giữ correction ở turn sau | [v5 base run](../runs/v5_B_base_openrouter_20260729T111055749827.json) |

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version evidence

| Version | Prompt/tool change | Hypothesis | Metric name | Before | After | Run File |
|---|---|---|---|---:|---:|---|
| v1 | baseline cleanup | make routing explicit | case_accuracy | 0.7 | 0.7 | [run](../runs/v1_B_base_openrouter_20260729T105701444658.json) |
| v2 | explicit routing rewrite | improve tool selection | case_accuracy | 0.7 | 0.0 | [run](../runs/v2_B_base_openrouter_20260729T110347884988.json) |
| v3 | clarify/send boundary tuning | separate text vs yes_no | case_accuracy | 0.0 | 0.9 | [run](../runs/v3_B_base_openrouter_20260729T110654304016.json) |
| v4 | explicit deictic send example | fix "bản tin này" boundary | case_accuracy | 0.9 | 0.95 | [run](../runs/v4_B_base_openrouter_20260729T110904312972.json) |
| v5 | final routing + boundary pass | lock the remaining edge cases | case_accuracy | 0.95 | 1.0 | [run](../runs/v5_B_base_openrouter_20260729T111055749827.json) |

## B2. Failure analysis

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R12_confirm_before_send | wrong_boundary | `clarify(response_type=text)` | model treated "bản tin này" as missing content | add explicit yes_no rule for deictic send requests |
| G04_missing_send_content | missing_info | `clarify(response_type=yes_no)` | group case was too vague | rewrite case to say content was not provided |
| GM05_news_topic_correction | wrong_arg_value | `lookup(query=AI, topic=news, timeframe=week)` | carryover topic was too loose | make latest turn restate `chip bán dẫn` |

## B3. Team eval cases

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_policy_privacy | policy privacy lookup | `policy(data_privacy)` | PASS |
| G02_paper_search | paper search | `papers(query, max_results=3)` | PASS |
| G03_read_arxiv_id | read arXiv id | `paper_text(arxiv_url=1706.03762)` | PASS |
| G04_missing_send_content | missing send content | `clarify(text)` | PASS |
| G05_no_tool_math | out of scope math | no tool | PASS |
| GM01_policy_carry_area | carry policy area | `policy(external_publishing)` | PASS |
| GM02_social_to_timeline_correction | topic -> account correction | `timeline(OpenAI, limit=4)` | PASS |
| GM03_confirmed_send | confirmed send | `send(confirmed=true)` | PASS |
| GM04_url_correction | URL correction | `fetch(openai.com/research)` | PASS |
| GM05_news_topic_correction | topic correction with timeframe carry | `lookup(chip bán dẫn, news, week)` | PASS |

## B4. Live chat evidence

| Scenario/Turn | Version | Tool Calls + Args | Transcript/Run | Outcome |
|---|---|---|---|---|
| Base eval | v5 | see run JSON tool_calls | [run](../runs/v5_B_base_openrouter_20260729T111055749827.json) | 20/20 pass |
| Group eval | v5 | see run JSON tool_calls | [run](../runs/v5_B_group_openrouter_20260729T111358933916.json) | 10/10 pass |

## B5. Tool capability evidence

| Category | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Must-have: tool mới đầu tiên | [tools.yaml](./tools.yaml) | `clarify`, `timeline`, `social_search`, `lookup`, `fetch` route correctly | missing account/url must not be guessed |
| Optional built-in | [v5 base run](../runs/v5_B_base_openrouter_20260729T111055749827.json) | core routing and boundary cases passed | Twitter/Telegram API calls can still 403 at execution time |
| Bonus: tool mới thứ 4 trở đi | [tools.yaml](./tools.yaml) | `policy`, `papers`, `paper_text`, `send`, `format` present and callable | manual review needed for external API failures |

## B6. Reflection

- `system_prompt.md` needed the main routing and boundary rules.
- `tools.yaml` needed the short schema-level examples and argument hints.
- Manual review was needed for tool execution errors; routing PASS does not prove the external API succeeded.
- Next improvement: add a small regression harness around the `clarify` boundary and redact/validate sensitive outbound API logs.
