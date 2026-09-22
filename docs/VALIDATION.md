# 驗證紀錄

核對日期：2026-09-22。這份紀錄描述交付原始碼時實際執行的驗證，不是使用者電腦或 GitHub 的執行結果。

## 實際通過

執行環境：Linux x86_64，Python 3.13.5。全部使用合成資料、暫存目錄或模擬傳輸；未提供真實服務憑證。

| 項目 | 實際結果 |
|---|---|
| `python -m unittest discover -s tests -v` | 61 個測試通過 |
| `python -m compileall -q jev_workflow tools tests` | 通過 |
| `python -m jev_workflow demo` | `MOCK`、`live_attempts: 0`、不授予操作權限 |
| JSON／YAML／TOML 與本機 Markdown 連結 | 語法與連結路徑檢查通過；不代表 GitHub CI 已執行 |
| 空白 A/B 模板 | 0 組完整對照、1 組資料不完整；節省率為 `null`，沒有補造數據 |
| 以臨時 HOME／CODEX_HOME 預覽安裝 | 未建立 Skill、未改動規則 |
| 套用使用者層級安裝 | 成功複製 Skill 與執行程式 |
| 從原始碼目錄以外執行已安裝啟動器 | `demo` 成功，沒有依賴原始碼工作目錄 |
| 重複套用安裝 | 沒有重複加入全域規則區塊 |
| 移除安裝 | 移除管理中的 Skill／規則區塊，保留其他使用者規則 |

測試涵蓋：呼叫預算與併發預留、相同任務去重、授權與專案拒用、資料與回應格式、常見敏感字串、HTTP 與超時的模擬處理、用量未知值、安裝衝突與 A/B 配對。

詳細測試輸出見 [offline-test-results.txt](offline-test-results.txt)。測試數量不是可靠性百分比，也不代表完整覆蓋所有情境。

## 尚未驗證

| 項目 | 限制 |
|---|---|
| 真實 TypeSafe API | 未提供 Key，未發出真實 API 請求。文件相符、模擬成功不等於服務已接通。 |
| Codex 讀取與自動選用 Skill | 未啟動使用者的 Codex；須在實際環境確認 Skill 出現、適當任務才呼叫。 |
| Windows／macOS／WSL 實機 | 尚未執行。CI 已配置多平台，但配置不等於執行通過。 |
| Python 3.10／3.12 實際執行 | 尚未執行；本次只驗證 Python 3.13.5。 |
| GitHub Actions | 目標公開儲存庫已建立，但整合上傳被 HTTP 403 拒絕，尚無本專案遠端 CI 執行紀錄。 |
| Codex Token／帳號額度／費用節省 | 沒有前後測量資料，未知。 |
| 對抗性安全審計 | 未完成。正規表示式與提示詞不是隔離機制，也不保證阻擋所有資料外洩。 |
| GitHub 發佈 | 擁有者已建立公開空白 repository；本包尚未成功提交或推送，沒有 GitHub release。 |

## 發佈前的下一輪驗證

先在自己的環境執行離線測試與 Mock，再確認 Codex 可以載入 Skill。由使用者明確開啟 Live 並授權專案後，用合成資料做一次真實請求；分開記錄回應、API 用量與錯誤。最後再做配對 A/B 任務量測，不能拿測試輸出當作效益證明。

## GitHub 命名整理

2026-09-22：專案名稱與中英文標題整理為 `codex-jev-router` / Codex JEV Router；MIT 署名為公開帳號 `john07180718 and contributors`，補上正確 repository 連結與網頁上傳步驟。Python 匯入名稱 `jev_workflow`、CLI `jev-workflow`、本機狀態目錄與管理標記保持相容，不需要使用者更換既有配置。

命名整理後重新執行：Linux x86_64 / Python 3.13.5；61 個離線測試通過、Mock 回傳 `MOCK`、Python compileall 通過。未發出真實 JEV 請求。
