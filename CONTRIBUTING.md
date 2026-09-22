# 參與維護

先閱讀 README、SECURITY、ARCHITECTURE 與 AGENTS.md。
修改要聚焦單一問題，附合成資料的最小重現與對應離線測試。

```text
python -m unittest discover -s tests -v
python -m compileall -q jev_workflow tools tests
python -m jev_workflow demo
```

普通 CI 不使用任何真實 API Key。網路、超時、重試與真實回應形狀用 stub／mock 驗證；
這不是模型能力評測，更不是 Live 驗證。真實測試請維護者明確授權後在獨立測試環境進行。

任何改動不可自動增加產品依賴、授權或資料外傳範圍，也不可刪測試只為取得綠燈。
API 格式變動先核對官方文件，再更新 schema、模型 pin、參考文件與回歸測試。

效能宣稱要附完整比較資料與失敗案例；不能把模擬 token 當實測。
私人程式、客戶資料、Key、安裝備份與原始 session 記錄不得出現在 Issue 或 PR。

開新功能前寫明目的、非目標、資安影響、費用影響、驗收條件與移除方式。
發布前更新 CHANGELOG、VALIDATION、README 狀態與版本號，不放尚未證實的支援徽章。
