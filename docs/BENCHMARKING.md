# 如何驗證是否真的省 Token

目前沒有你的專案的比較數據，不提供節省百分比。

## 先把指標分開

Codex input / cached input / output：由可驗證的 Codex/API 使用量來源取得。
JEV input / output：來自有效的 JEV API 回應。沒有回應的請求可能用量未知。
Codex 訂閱額度：另一種產品計量，這個工具不冒充能讀取或換算。
任務品質、實際花費、耗時：各自量，不能只比較一個 token 總數。

本專案不讀取未公開格式的 Codex session 檔、不擷取登入憑證、不抓私人聊天紀錄。
`stats` 的 codex_tokens 與 codex_quota_savings 刻意是 null。

## 配對實驗

同一組任務與同一起始 commit，使用相同 Codex 模型與 reasoning effort、權限、
測試和驗收標準；一組關掉此工作流，一組開啟。使用獨立的新工作階段，記錄所有額外成本，
並交錯執行順序，避免暖快取或先做過一次造成假優勢。

不要拿簡單改字當 baseline，拿大範圍重構當 treatment，也不要把失敗的 JEV 任務刪掉。
先試多個代表性任務，再決定哪些場景停用或保留。沒有樣本量分析時不宣稱統計顯著。

## 輸入檔

複製 `examples/benchmark.template.json` 為 `benchmark.local.json`。
每個 pair 要有 baseline / jev 各一筆：

- pair_id / task_ref / starting_commit：同一任務的識別與起始狀態。
- codex_model / reasoning_effort：實際設定，不能只填「最新」。
- codex_input_tokens：完整 input，含其中的 cached 部分。
- codex_cached_input_tokens：input 的子集，**不再加一次**。
- codex_output_tokens：來源提供的完整 output；不要重複加已包含的 reasoning。
- jev_input_tokens / jev_attempts：此任務的實際資料；若有無法結算請求，token 填 null。
- elapsed_seconds：整個任務的可比較耗時，不只 JEV API latency。
- quality_pass：是否通過預先訂好的相同驗收條件。

未知值保持 null。不要將 null 當零。不可比較的 model/effort/commit 或不完整 pair
不納入 token 差異計算；報表會列出排除的數量。

```text
python tools/compare_usage.py benchmark.local.json
```

報表包含完整組數、配置不符與不完整組數、兩組總用量與品質通過數、觀察到的
Codex token 差異。品質失敗的完整樣本不被偷偷剔除。
即使 token 降低，品質變差也不能說整體更有效率。

計算：`(baseline_input + baseline_output - jev組的Codex_input - jev組的Codex_output) / baseline的Codex總量`。
這只是該批輸入資料的觀察值，不代表穩定因果效果或訂閱額度節省。

## 發佈 benchmark 的規範

公開任務規格、起始版本、模型、推理設定、樣本數、失敗案例、驗收方式、原始已去識別用量。
樣本不足時寫試驗紀錄，不寫「保證省50%」。不同廠商的 tokens 不直接當同價單位相減。
要比較美元需當時定價、cached 計價與完整計費紀錄，這個工具目前不自動換算。
不得將使用者的真實專案、客戶資料或 API Key 放入公開 benchmark。
