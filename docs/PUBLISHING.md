# 放上 GitHub

目標儲存庫：<https://github.com/john07180718/codex-jev-router>。

2026-09-22 封裝時，公開空白儲存庫已由擁有者建立；本次整合上傳回傳 HTTP 403，沒有成功提交程式碼。下列為由擁有者上傳的步驟，不代表已完成發佈。

## 建議發佈流程

先在本機完成測試。把**解壓後的專案檔案**放到 repo 根目錄，
不要只上傳一個 ZIP 而讓 README、Skill、測試與 CI 都藏在裡面。
使用 Git 或 GitHub Desktop 上傳時確認 `.github` 等點開頭資料夾也被包含。

本專案名稱為 `codex-jev-router`。
Description 可用：

> 讓 Codex 按需使用 JEV 的開發輔助工作流：語意分類、候選篩選、有限預算、安全退回與用量驗證。

可選 topics：`codex`、`agent-skills`、`jev`、`developer-tools`、`workflow`、`python`。
請自行確認 MIT 授權與作者署名是否符合你的發佈意圖。

## 目前空白儲存庫：網頁上傳

1. 解壓 `codex-jev-router-v0.1.0.zip`，進入內層 `codex-jev-router`，確認能直接看到 `README.md`、`LICENSE`、`.github`、`jev_workflow` 等項目。
2. 在空白儲存庫首頁按 `uploading an existing file`。
3. 將上述資料夾**裡面的全部檔案及子資料夾**拖進上傳區；包含 `.github`、`.gitignore`、`.env.example`。不要只上傳 ZIP，也不要再多包一層 `codex-jev-router`。
4. 提交說明填 `Initial commit: Codex JEV Router v0.1.0`，確認提交至 `main`，按 `Commit changes`。
5. 檢查首頁能顯示 README、MIT License，並在 Actions 查看實際測試結果。不要把尚未執行的檢查寫成已通過。

只上傳封裝中這些專案檔案；不要加入個人 `.env`、API Key、客戶或其他私有專案資料。

## 上傳前檢查

1. 全部離線測試與 demo 通過；docs/VALIDATION.md 與實際狀態一致。
2. 不包含真實 Key、.env、私有專案、客戶資料、聊天紀錄、狀態 DB 或安裝備份。
3. 確認 `.gitignore` 只是防誤加，不會移除已經 commit 的秘密；有外洩就撤銷/換 Key，不能只刪畫面。
4. README 不放未實測的節省比例、不放假的 badge、stars、使用者數或跨平台保證。
5. 確認 CI 僅需只讀權限，沒有付費 API Secrets、部署或產品操作。
6. 將 CI 在 GitHub 的實際結果與本機離線結果分開記錄。
7. 若準備公開，確認 repo visibility、開源授權、私人漏洞回報與維護責任。

## 上傳後

GitHub Actions 執行本 repo 的離線測試矩陣。CI 不是啟用 JEV 的開關，
也不是替每個下載者提供免費 API。每位使用者自行安裝、授權、提供 Key 與承擔服務費。
GitHub 的執行資源費用則依你的帳戶與方案，不因沒有模型呼叫就保證 CI 永遠免費。

檢查綠燈後再考慮標記第一個 pre-release `v0.1.0`，註明 Live 與 Codex E2E 驗證情況。
不要將起始模板直接宣稱穩定 production release。

更廣泛的安裝分發可在後續評估打包成 Codex/ChatGPT Plugin；官方目前推薦以 Plugin
分發可重用 Skills。本版先交付 GitHub 原始碼與本機 Skill 安裝器，沒有替你提交插件商店。

## 官方操作來源

- https://docs.github.com/en/get-started/start-your-journey/creating-a-repository-for-your-project-on-github
- https://docs.github.com/en/actions/reference/security/secure-use
- https://developers.openai.com/codex/skills/

- https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository
