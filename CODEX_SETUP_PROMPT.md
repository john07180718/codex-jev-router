# 貼給 Codex 的安裝與驗收指令

請在目前 `codex-jev-router` 資料夾協助我完成本機工作流設定。

先讀 README.md、docs/INSTALL.md、SECURITY.md 與 docs/VALIDATION.md。
這個專案是開發輔助工具，不是任何產品、交易機器人或自動化系統的執行依賴。

## 執行範圍

1. 確認 Python 3.10+、作業系統、目前使用者目錄、實際 CODEX_HOME 與既有同名 Skill。
   不印出任何密鑰、環境秘密或客戶內容。
2. 在目前原始碼執行全部離線測試與 `python -m jev_workflow demo`。
   不把 Mock 成功寫成真實 JEV 成功，不因測試失敗就刪除測試或降低安全規則。
3. 執行安裝預覽：`python tools/install.py --scope user --global-rule`。
   我授權在此執行環境將這套 Skill 安裝到使用者層級，並在保留原內容與備份後新增它自己的全域區塊。
   確認無衝突後執行同一指令加上 `--apply`。
   遇到非本專案管理的同名 Skill、手動修改或不完整標記時，停止該覆寫，列出處理方式。
4. 執行本機 doctor，確認安裝路徑與 Python 啟動器可用。
   請明確區分：規則檔已建立、Skill 啟動器能執行、Codex 已載入、真實 API 已成功。
   不為了取得證據而自動花費 Codex/JEV 額度或啟動新的付費代理。
5. 保持 Mock 預設。不要替我啟用 Live、授權所有專案、提高預算、建立背景任務或找我的 API Key。
   真實啟用步驟列給我，我在自己的終端處理憑證。
6. 使用合成資料示範一般任務跳過、適合任務 Mock、服務失敗退回、高風險不授權等行為。
   程式層的測試不代表 Codex 模型已按預期自動觸發 Skill，兩者分開回報。
7. GitHub 先只做準備：檢查 .gitignore、沒有秘密資料，並列出將上傳的檔案。
   不自動建立公開 repo、不 push、不放 API Key 到 GitHub Secrets。
   真正上傳需要我另行指定 repository、分支與公開/私人選擇。

## 最後交付

列出實際變更位置、備份位置、測試結果、啟動器驗證、尚未完成的真實整合驗證。
附上停用與移除指令。不承諾節省比例，也不把未知項目寫成已驗證。
