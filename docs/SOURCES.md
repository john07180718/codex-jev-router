# 官方資料來源與核對紀錄

核對日期：**2026-09-22**。來源供核對介面與設計邊界，不代表官方背書此專案。

| 來源 | 用途 |
|---|---|
| https://developers.openai.com/codex/skills/ | Skill 格式、name/description、按需載入與自動選用、使用者／專案位置；頁面目前會轉到官方 ChatGPT Learn |
| https://developers.openai.com/codex/guides/agents-md/ | CODEX_HOME、全域 AGENTS.override.md／AGENTS.md 與指令疊加 |
| https://docs.typesafe.ai/introduction/coding-agents | Jev 是輔助的結構化決策工具，不是 coding-agent 主模型替代品 |
| https://docs.typesafe.ai/api | POST /v1/systemone、Authorization、state/questions/model、answers/usage、錯誤狀態 |
| https://docs.typesafe.ai/introduction/quickstart | 真實 HTTP 請求／回應格式與 API Key 環境變數 |
| https://docs.typesafe.ai/confidence | Choice／Score 的 confidence 與機率分布、Noul 的不同回傳欄位 |
| https://docs.typesafe.ai/models | 版本名稱與別名、記錄實際回覆版本；本版起始 pin 為 jev-1.13.0 |
| https://docs.typesafe.ai/model-jaggedness/jev-1.13 | 計算、日期、多層推理、無關內容與對抗性內容等已知限制 |
| https://docs.github.com/en/actions/reference/security/secure-use | 最小權限、Secrets、SHA pin、不可信 PR 程式的風險 |
| https://docs.github.com/en/get-started/start-your-journey/creating-a-repository-for-your-project-on-github | GitHub 建立與上傳專案 |

## CI 固定版本

- actions/checkout v6.1.0：`d23441a48e516b6c34aea4fa41551a30e30af803`
  https://github.com/actions/checkout/commit/d23441a48e516b6c34aea4fa41551a30e30af803
- actions/setup-python v6.3.0：`ece7cb06caefa5fff74198d8649806c4678c61a1`
  https://github.com/actions/setup-python/commit/ece7cb06caefa5fff74198d8649806c4678c61a1

這是已核對的固定版本，不宣稱為永遠最新。使用 GitHub-hosted runners；老版本自架 runner
可能不符合 Node runtime 要求，需另外核對。Dependabot 會建議更新，但更新仍要檢視與測試。

## 本專案自己的選擇，不是官方保證

每任務3次、每日30次、10秒、零預設重試、16,000 bytes、最多8題／12個選項、
必須包含 NEEDS_REVIEW、只允許字串子集、只作為開發建議，都是此工作流的保守設計。

官方文件中的輸出機率與信心值不構成你的任務成功率、交易勝率或安全保證。
本版沒有抄入第三方社群 CLI，不假設其指令存在，也不下載執行遠端安裝腳本。

API、模型、Codex 載入方式或 Plugin 發佈方式變更時，維護者應重新查證官方資料與測試。
