# 安裝、啟用與移除

## 前置條件

Python 3.10+、一個可以執行本機指令並載入 Skills 的 Codex 環境。
CLI 在執行時只用 Python 標準函式庫；源碼直接執行不用 pip。
`pyproject.toml` 只提供可選的本機打包資訊；這份專案尚未替你發佈到 PyPI。

目前只在驗證紀錄列出的環境實際測過。CI 提供 Windows/macOS/Linux 與多版 Python
的測試矩陣，不等於這些工作已經在 GitHub 跑過。

## 1. 解壓並開啟專案根目錄

Windows 終端可能是 `python` 或 `py -3`，macOS/Linux 可能是 `python3`。
下面以 `python` 示範，請使用可用的 3.10+ interpreter。

```text
python --version
python -m unittest discover -s tests -v
python -m jev_workflow demo
```

`demo` 用臨時資料夾執行 Mock，不讀取你的 Key、不啟用 Live、不變更個人授權。
若使用者已設定全域停用環境變數 `JEV_WORKFLOW_DISABLED=1`，demo 也會尊重停用。

## 2. 安裝

```text
python tools/install.py --scope user --global-rule
python tools/install.py --scope user --global-rule --apply
```

第一行是預覽。第二行會複製 Skill 與 Python package，並將短區塊合併到
`CODEX_HOME`（預設 `~/.codex`）的第一個非空 `AGENTS.override.md` 或 `AGENTS.md`。
其他指令內容保留。備份在 `~/.codex-jev-workflow/install-backups/<id>/`。

只裝某專案：

```text
python tools/install.py --scope project --project "C:\Projects\demo" --apply
```

不要同時裝使用者層與同專案同名技能，除非你已確認 Codex 選用的是哪一份。
安裝器不掃描、合併所有深層的 AGENTS.md。較靠近工作的專案規則或公司政策仍可能
限制 Skill 的使用。重新開一個 Codex 工作階段，請它列出本次載入的指令來源與可用 Skill。
驗證這一步會使用 Codex；請由使用者自行啟動，不把它當作免費離線測試。

已安裝啟動器位於：

```text
<HOME>/.agents/skills/jev-assist/scripts/jev.py
```

可直接以完整路徑執行，不需把整個工具庫加入每一個產品 repo。

## 3. 明確授權資料與啟用 Live

由使用者操作，不讓 Codex 為了完成一般任務自行打開：

```text
python -m jev_workflow init
python -m jev_workflow authorize --project "C:\Projects\demo" --allow-external-data
python -m jev_workflow configure --mode live
```

授權對象是正規化後的**單一專案根目錄**，不會自動包含每個子專案或另一份 worktree。
這代表允許傳送符合政策、已檢視的最小開發片段，不是授權外傳整個 repo 或任何個資。
資料庫與配置預設在 `~/.codex-jev-workflow`；正常使用不要更換 `--home` 以免形成獨立預算。

憑證用環境變數 `TYPESAFE_API_KEY` 提供。CLI 不會自動讀 `.env`。
已安裝 Codex CLI 的使用者可在自己的互動終端執行：

```text
python tools/with_key.py codex
```

這是便利的隱藏輸入方式，不是防止同帳戶程序讀取秘密的安全容器。
不要把 Key 直接貼入 shell history、聊天或任何公開資料。
使用 IDE/App 時，需依該環境的安全設定方式讓其執行程序取得憑證；本工具不猜測你的 IDE 設定。

## 4. 本機檢查不等於 API 成功

```text
python -m jev_workflow doctor --project "C:\Projects\demo"
```

`local_prerequisites_met=true` 只代表本機條件具備。
`live_api_verified=false` 是刻意保留，doctor 沒有偷偷發請求。

首次真實測試應先用獨立合成測試專案。授權該測試資料夾後：

```text
python -m jev_workflow begin --project "C:\Projects\jev-synthetic-test"
```

記下回傳的 task_id，在已取得環境憑證的同一程序環境執行：

```text
python -m jev_workflow ask --project "C:\Projects\jev-synthetic-test" --task "<task_id>" --request examples/test-failures.json
python -m jev_workflow end --project "C:\Projects\jev-synthetic-test" --task "<task_id>"
```

也可用 `tools/with_key.py` 只對 ask 指令提供 Key：

```text
python tools/with_key.py python -m jev_workflow ask --project "C:\Projects\jev-synthetic-test" --task "<task_id>" --request examples/test-failures.json
```

這才可能發送一筆真實且可能計費的 JEV 請求。
必須看到 `ADVISORY` 與真實 usage 才能說本次 API 呼叫成功；不能用 Mock、doctor 或程式退出碼0替代。
測試後可撤銷測試專案授權。

## 5. 關閉與移除

```text
python -m jev_workflow configure --mode off
python -m jev_workflow revoke --project "C:\Projects\demo"
python tools/install.py --uninstall
python tools/install.py --uninstall --apply
```

安裝器依 manifest 移除自己管理的檔案與區塊，保留其他規則。
如果 installed Skill 被手動改過，為了不刪除修改內容會停止，請先檢視與另存。
全域檔在多檔安裝過程中不是資料庫式原子交易；若中途中斷，請檢查備份與輸出路徑，
不要反覆盲目覆蓋。需要回復時以備份為參照，只合併受影響的部分，避免蓋掉之後的新規則。

移除 Skill 不會自動撤銷供應商 Key 或刪除 usage.sqlite3、config.json、備份。
停用後確認沒有工作在執行，再由使用者選擇保留、封存或刪除本機資料。
刪除資料庫也會清掉目前預算紀錄；不要在執行中的任務用此方式重置。
