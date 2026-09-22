# 安全與資料處理

## 範圍

這是正常合作代理的開發輔助工具，不是安全沙箱、完整 DLP、秘密管理系統或交易風控產品。
JEV 與 Codex 都可能判斷錯誤。任何高信心、PASS 或單次測試成功都不會賦予新的操作權限。

## 送出的內容

Live 模式只向固定 `https://api.typesafe.ai/v1/systemone` 傳送已驗證的 model、state、questions。
認證用標準 Authorization header；不轉址、不提供任意主機配置、不將 key 放在 prompt。
使用者必須取得供應商使用資格並同意相關條款與資料政策。

個別 API 使用者的資料保留條款可能不同，這份專案不替供應商保證一律零保留。
本工具自己的紀錄不存原始輸入或輸出；Codex/IDE 對話紀錄則可能仍包含工具輸入與輸出。
使用者若手動把 request 放到檔案，該檔案仍存在，應自行清理；正式操作優先 stdin。

## 授權

啟用 Live、授權一個專案與提供 Key 是三件不同事。
只安裝 Skill 不視為資料外傳授權，專案內的檔案不能替自己增加使用者層級的授權。
`data_reviewed`、風險等級與預期收益是呼叫者的聲明，程式只能驗證欄位，不能證明聲明正確。
公司與工作區禁止外傳的規則優先，即使本機誤設 live 也不能使用。

## 已做的防護

固定目的與型別、未知欄位拒絕、數值合理性、概率分布、對應題目及模型版本檢查。
命令不經 shell 拼接，provider error body 不回傳，API Key 不寫入 argv 或普通 log。
常見敏感模式（部分 token、私鑰、Bearer、JWT、email 等）會阻擋整筆請求，
不會默默改寫關鍵證據再送。

敏感模式檢查可能誤擋，也可能漏掉姓名、電話、地址、自訂 token、編碼秘密或未列的資訊。
不得宣稱「100%防外洩」。遇到誤擋請用合成資料重現，再由維護者判斷，不增加繞過旗標。

輸入中夾帶的指令只能當資料；附加 guard 語句不是 prompt injection 的完整防線。
程式不執行模型答案，Skill 也不得要求高風險自動動作。

## 預算與故障

所有經此 wrapper 的 Live 嘗試先在 SQLite 交易預留。重試也占額度。
超時會終止本機 worker，但 provider 仍可能完成或計費；未知用量保持未知。
同一任務重複請求不重送，包含先前失敗的請求；不允許反覆改題只為取得想要的結論。
若 DB 不可寫或有錯，不能發請求繞過 ledger。Live 階段與其他工具故障不得解除既有保護。

這不是對抗同權限程式的強制閘道。新 task、新 --home、改程式、改 DB、直接 API 請求
或另一台電腦不受原本額度統一控制。要真正跨機器強制管控需獨立權限邊界與服務端設計。

## 儲存與清理

`~/.codex-jev-workflow/config.json`：模式、限制、授權的本機專案路徑，沒有 Key。
`usage.sqlite3`：task id、HMAC 指紋、狀態、版本、計數與用量，沒有原始 prompt/response。
`install-backups/`：以前的全域指令與 Skill 備份，**可能包含使用者原本的私人內容**。

本機資料不自動上傳，不要把狀態目錄、備份、request.local.json 或 benchmark.local.json 提交 Git。
HMAC key 與指紋在同一本機 DB；不能把持有 DB 後的指紋視為強匿名化。

套件移除保留紀錄。需完全移除時：停用、等待沒有任務運作、檢查及備份需要的用量，
再由使用者選擇刪除本機狀態。刪除會一併重置本機呼叫預算。

## GitHub 與漏洞回報

普通 CI 不需要 TYPESAFE_API_KEY 或 OPENAI_API_KEY。不要在不受信任 PR 的 workflow
注入付費憑證；不採用 pull_request_target 配合 checkout 不可信程式。
CI 用只讀權限與固定 SHA 的官方 Actions。不要把自架含私人密鑰的 runner 接到公開 PR。

發佈前維護者應在 GitHub 啟用 Private vulnerability reporting。
敏感漏洞請走儲存庫私人回報；如果未提供私人管道，只在公開 Issue 留下不含細節的聯絡請求。
不在公開 Issue 上傳可用密鑰、私人程式碼、個資或可造成傷害的完整利用資料。
本起始專案沒有提供虛構的安全聯絡信箱。
