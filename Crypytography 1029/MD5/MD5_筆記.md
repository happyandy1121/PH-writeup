# MD5 解題程式使用筆記

這份筆記說明如何使用同資料夾的 [solve_md5.py](solve_md5.py)。程式知道原文的固定開頭、結尾和總長度後，逐一組合中間的字元，計算 MD5 並與目標雜湊比較。它使用 Python 標準函式庫，不需額外安裝套件。

## 填入已知條件

打開 `solve_md5.py`，修改檔案最上方的設定：

```python
TARGET_HASH = "dfb3d86e2f71fc381012b1beeba20937"
LENGTH = 8
PREFIX = "PH{"
SUFFIX = "}"
CHARSET = string.ascii_letters + string.digits + string.punctuation + " "
```

- `TARGET_HASH`：題目給的 32 位十六進位 MD5 值。
- `LENGTH`：**完整原文**的字元數，包含 `PREFIX` 和 `SUFFIX`。範例 `PH{5yee}` 是 8 個字元。
- `PREFIX`、`SUFFIX`：已知的開頭和結尾。如果沒有固定部分，可填空字串 `""`。
- `CHARSET`：每個未知位置可能使用的字元。若確定只有數字，可改成 `string.digits`；只有小寫英文字母可改成 `string.ascii_lowercase`。不要把實際答案排除在字元範圍外。

程式會算出未知位置數量：`LENGTH - len(PREFIX) - len(SUFFIX)`。目前設定是 `8 - 3 - 1 = 4` 個位置、每個位置 95 種字元，所以最多需要檢查 `95^4 = 81,450,625` 個候選。條件越準確，搜尋越快。`LENGTH` 以 Python 的字元數計算；雜湊前則會把候選文字編成 UTF-8 bytes，因此若題目包含非 ASCII 字元，需特別確認題目說的長度與編碼。

## 執行程式

在 `PH-writeup` 倉庫根目錄開啟終端機，執行：

```powershell
python "Crypytography 1029/MD5/solve_md5.py"
```

若你的環境用 `py` 啟動 Python，也可以把指令開頭的 `python` 換成 `py`。程式會先印出總長度、未知字元數和候選數；搜尋期間每 100 萬個候選會顯示一次進度。要中止可按 `Ctrl+C`。

用原檔設定實際執行後，得到：

```text
找到原文：'PH{5yee}'
驗證 MD5：dfb3d86e2f71fc381012b1beeba20937
```

第二行是把找到的文字重新做 MD5，結果與 `TARGET_HASH` 相同。換題時請重新填入雜湊與已知格式，不要直接沿用範例答案。

## 沒找到時檢查什麼

如果程式跑完顯示「目前的長度、開頭、結尾與字元範圍內沒有找到結果」，依序核對 `TARGET_HASH` 是否抄對、`LENGTH` 是否包含括號與固定文字、`PREFIX`／`SUFFIX` 是否正確、`CHARSET` 是否漏掉可能的字元。只要其中一項限制錯誤，即使搜尋完全部候選也找不到原文。

## 解題重點

MD5 是單向雜湊，這支程式不是直接把雜湊「解密」。它利用題目提供的格式與長度縮小候選範圍，對每個候選算 `MD5(候選字串的 UTF-8 bytes)`，直到與目標值相同。未知字元每增加一個位置，搜尋量就會再乘上 `CHARSET` 的字元種類數，所以先確認題目條件再執行最有效率。
