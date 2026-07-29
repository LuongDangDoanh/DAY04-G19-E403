# Day 04 Lab v2 Report — G19 Research Agent

Provider: OpenRouter (`openai/gpt-4o-mini`)  
UI: Streamlit (`app.py`) + static claymorphism demo (`index.html`)  
Local URL: `http://localhost:8501`  
Public URL: chưa tạo tunnel; dùng `cloudflared tunnel --url http://localhost:8501` khi cần demo máy khác.

## PHẦN A — Giới thiệu agent

### A1. Agent này làm được gì

Agent nhận yêu cầu research, chọn đúng tool, truyền arguments, chạy tool thật và lưu trace JSON. Agent hỗ trợ tìm web/news, tìm bài đăng theo account hoặc topic, đọc URL, hỏi lại khi thiếu thông tin, xác nhận trước action có side effect và định dạng digest.

UI cho phép chạy cùng một scenario qua v0–v3, xem request/response, từng round, tool name, args, status, result/error, transcript và artifact hashes.

Chạy UI:

```powershell
cd starter_v0
python -m pip install -r requirements.txt
streamlit run app.py
```

### A2. Tool agent có

| Tên tool | Làm được gì | Phân loại |
|---|---|---|
| `clarify` | Hỏi lại thông tin thiếu hoặc xin yes/no confirmation | core |
| `timeline` | Lấy bài đăng gần đây của một account | core |
| `social_search` | Tìm bài đăng theo topic, Latest hoặc Top | core |
| `lookup` | Tìm web/news theo query, topic, timeframe | core |
| `fetch` | Đọc đúng URL user cung cấp | core |
| `format` | Định dạng các items đã có thành digest | core |
| `source_quality` | Team tool mới: xếp hạng metadata của URL, không fact-check | team-added |
| `web_search`, `webpage_reader`, `calculator`, `unit_converter`, `datetime_tool`, `weather_lookup`, `currency_converter`, `pdf_text_extractor`, `csv_summary`, `markdown_summarizer` | Capability bổ sung có implementation và declaration | built-in extension |
| `send`, `policy`, `papers`, `paper_text` | Telegram, policy, arXiv/PDF | optional |

### A3. Câu hỏi mẫu

1. `Tin tức AI hôm nay có gì nổi bật?`
2. `Tweet mới nhất của Sam Altman là gì?`
3. `Tóm tắt bài này giúp mình: https://openai.com/blog/gpt-5`
4. `Tóm tắt 5 tweet mới nhất giúp mình` — agent phải hỏi account, không đoán.
5. `Đăng bản tin này lên Telegram giúp mình` — agent phải hỏi yes/no trước khi gửi.

### A4. Kịch bản demo đã rehearse

| Scenario | Tool trace cần thấy | Câu chuyện cải thiện version | Fallback |
|---|---|---|---|
| Research request | `lookup(query=AI, topic=news, timeframe=day)` | v0 routing/args 70%; v2/v3 100% | `v3_B_base...json` |
| Missing account | `clarify(response_type=text)` và không có timeline thừa | v3 chặn regression đoán nhiều account | `v3_openrouter_20260729T112447983907.transcript.json` |
| Sensitive action | `clarify(response_type=yes_no)`, không gọi `send` | boundary được mô tả rõ trong prompt + declaration | transcript live |
| Same scenario comparison | v0, v1, v2, v3 artifact/hash | 0.70 → 0.90 → 1.00 → 1.00 | `analysis/clean_base_runs.csv` |

---

## PHẦN B — Chi tiết / Bằng chứng

Điều kiện metric hợp lệ đều đạt cho các run được chọn: `provider_error_cases=0` và `measured_cases=total_cases=20`. Run v0 đầu tiên `v0_B_base_openrouter_20260729T095147124145.json` có 20 provider errors do chạy trước khi env được nạp; run đó được giữ làm evidence retry nhưng không dùng để báo metric. Metric v0 dưới đây dùng run sạch `20260729T100032268561`.

### B1. Version evidence

| Version | Thay đổi | Hypothesis | Case accuracy | Routing | Args | Multiturn | Run |
|---|---|---|---:|---:|---:|---:|---|
| v0 | Baseline prompt/declarations mơ hồ | Đo failure pattern ban đầu | 0.70 | 0.70 | 0.70 | 1.00 | `runs/v0_B_base_openrouter_20260729T100032268561.json` |
| v1 | Prompt rõ routing/boundary + `source_quality` | Policy rõ giúp chọn tool và carry context tốt hơn | 0.90 | 1.00 | 0.90 | 1.00 | `runs/v1_B_base_openrouter_20260729T111051328405.json` |
| v2 | Declaration rõ, required args, `additionalProperties=false` | Tách JSON fields và bắt buộc `response_type` sẽ hết malformed args | 1.00 | 1.00 | 1.00 | 1.00 | `runs/v2_B_base_openrouter_20260729T111457043069.json` |
| v3 | Prompt thêm argument audit và cấm đoán account | Giữ v2 accuracy và chặn unnecessary timeline calls | 1.00 | 1.00 | 1.00 | 1.00 | `runs/v3_B_base_openrouter_20260729T111923409150.json` |

Hash và hypothesis đầy đủ nằm trong `artifacts/version_log.csv`.

### B2. Failure analysis dựa trên trace thật

| Run/case | Actual call | What failed | Fix |
|---|---|---|---|
| v1 / `R11_missing_url` | `clarify(question=...)` | Model bỏ `response_type=text`; implementation default nên tool result vẫn có text nhưng argument grader fail | v2 làm `response_type` required và mô tả rõ text/yes_no |
| v1 / `R13_parallel_web_and_tweets` | lookup có key malformed `topic=news','timeframe`; social call thiếu explicit `search_type` nhưng routing đúng | Args JSON không ổn định, lookup tool result nhận `TypeError` | v2 tách field, `additionalProperties=false`, required query/topic/timeframe |
| v3 first attempt / `R10_missing_handle` | 3 timeline calls: `elonmusk`, `sama`, `karpathy` | Model đoán nhiều account khi user không nêu account; RapidAPI trả 403/429 cho các call thừa | v3 final ghi rõ exactly one `clarify(text)` và cấm đoán/multiple timelines; rerun pass 20/20 |
| live / Karpathy | `timeline(screenname=karpathy, limit=5)` | Routing đúng nhưng RapidAPI response thật là HTTP 403 | Không che lỗi; UI/transcript hiển thị result/error và report ghi rõ credential/plan blocker |

### B3. Team eval cases

`data/eval_group.json` có đúng 10 case: 5 single-turn (`G01–G05`) và 5 multi-turn (`G06–G10`). Run v3 group đạt 10/10, provider errors 0, routing/args/multiturn 1.0.

| Case | What it tests | Expected | Result |
|---|---|---|---|
| G01 | URL cụ thể thắng lookup | `fetch` exact URL | PASS |
| G02 | Thiếu account | `clarify(text)` | PASS |
| G03 | Send cần confirmation | `clarify(yes_no)` | PASS |
| G04 | Top vs Latest và limit | `social_search(query, Top, 4)` | PASS |
| G05 | Coding ngoài scope | no tool | PASS |
| G06 | Carry account + latest limit | `timeline(karpathy, 3)` | PASS |
| G07 | Clarify URL rồi fetch | `fetch` exact arXiv URL | PASS |
| G08 | Đổi social sang web news | `lookup(OpenAI, news, week)` | PASS |
| G09 | Sửa search type và limit | `social_search(AI safety, Top, 6)` | PASS |
| G10 | Hủy send, chỉ draft | no tool | PASS |

Evidence: `runs/v3_B_group_openrouter_20260729T112047597434.json`, `analysis/group_runs.csv`.

### B4. Live chat evidence

| Scenario | Version | Trace | Outcome |
|---|---|---|---|
| News research | v3 | `lookup({query: AI, topic: news, timeframe: day})` | 5 live results returned; response cites sources |
| Missing information | v3 | `clarify({response_type: text})`, then `timeline({screenname: karpathy, limit: 5})` | Clarification boundary pass; timeline API error shown honestly |
| Sensitive action | v3 | `clarify({response_type: yes_no})`; no `send` | Confirmation boundary pass |

Transcript: `transcripts/v3_openrouter_20260729T112447983907.transcript.json`.

### B5. Tool capability evidence

| Category | Evidence | What worked | Risk / guardrail |
|---|---|---|---|
| Team tool mới: `source_quality` | `tools/source_quality/TOOL.md`, `tool.py`, registry, YAML; direct smoke | URL metadata returns primary/secondary/unclassified score, no env/network | Not a fact-check; prompt says use only after URL exists |
| Core `lookup` | escalated smoke + live transcript | `error=None`, one result returned | API quota/provider dependency |
| Core `fetch` | escalated smoke on `https://example.com` | `error=None`, Example Domain returned | Firecrawl quota/provider dependency |
| Core `timeline`, `social_search` | smoke + live transcript | Routing works; implementation is called | RapidAPI returns HTTP 403 with current set credentials; needs plan/key remediation before claiming full core smoke PASS |
| Optional `send` | dry-run smoke | `status=needs_confirmation`, no message sent | Telegram credentials remain outside eval; never live-sent |

### B6. UI evidence

`app.py` reuses `run_model_tool_loop` from `chat.py`; it does not implement a second agent loop. It renders:

- request and final response;
- each round and tool event with name, args, status, result/error;
- transcript id/path, run count, artifact version, prompt hash and tools hash;
- three demo scenarios and version selector v0–v3;
- transcript persistence in `transcripts/*.transcript.json`.

UI validation:

- `python scripts/preflight_provider.py --provider openrouter` passed with model `openai/gpt-4o-mini`;
- `python -m streamlit run app.py --server.headless true --server.port 8501` started successfully;
- `GET http://localhost:8501` returned HTTP 200;
- `index.html` inline JavaScript syntax check passed;
- `requirements.txt` contains `streamlit>=1.30.0`.

### B7. Submission and security checks

`python scripts/check_submission.py` output:

```text
SUBMISSION CHECK: PASS
tools=21 group_cases=10 base_versions=4 transcripts=1
```

`python -m py_compile app.py scripts/check_submission.py tools/source_quality/tool.py` passed. A secret scan over submitted source/artifact files found zero key/token matches. `.env`, `.venv/`, `__pycache__/`, and arXiv cache are ignored and must not be submitted.

Deterministic edge-case suite: `python -m unittest discover -s scripts -p 'test_tools.py' -v` — 8/8 passed, covering clarify boundaries, calculator unsafe input, unit conversion invalid input, source-quality URL validation, empty format/input contracts, and datetime output.

### B8. Reflection

- Prompt fixes: scope/no-tool behavior, exact routing map, multi-turn latest-turn rule, clarification and side-effect boundary, and the final argument audit.
- Declaration fixes: descriptions now say when to use/not use each tool; `clarify.response_type` and `lookup.query/topic/timeframe` are required; lookup fields cannot be silently merged.
- Manual review mattered for tool execution: routing PASS did not mean RapidAPI succeeded. The 403/429/HTTP errors are preserved in run/transcript evidence.
- Next improvement: renew or correct the RapidAPI Twitter API45 subscription/key, rerun both timeline/social smoke tests, then rerun v3 base/group and update this report without changing eval cases.

### B9. Optional scope

The extension suite was not run because it is optional. Telegram live-send was not run by design; only dry-run confirmation was tested. No public Cloudflare tunnel was opened from this workspace.
