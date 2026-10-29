# Cut and Paste 題目筆記

## 題目在做什麼

伺服器先讀入 `user`，組成以下明文，再用 AES-ECB 加密並給我們十六進位的 token：

```text
user:<輸入的 user>;money:10;
```

接著伺服器讓我們提交一個 token，解密後執行：

```python
user, money, _ = token.split(b';')
if int(money.split(b':')[1]) > 666666:
    print(FLAG)
```

因此，解密結果必須**恰好有兩個分號，切出三段**；第二段要是大於 `666666` 的 `money` 欄位。

## 漏洞重點

- AES 的區塊長度是 **16 bytes**。ECB 模式逐塊獨立加密及解密。
- 伺服器只用 `aes.decrypt(token)`，沒有檢查 token 是否完整、是否仍為原本產生的內容。
- 所以我們可以只提交加密結果的前兩個區塊，讓原本尾端的 `;money:10;` 消失。
- `if ':;' in user` 只禁止相鄰的 `:;`。我們的輸入包含 `:666667;`，不會被攔下。

## 解法：讓想要的內容落在前 32 bytes

輸入以下 **user 值**（不要自行加上開頭的 `user:`）：

```text
AAAAAAAAAAA;money:666667;BB
```

伺服器加上固定前綴、後綴後，明文的區塊如下：

```text
區塊 1（16 bytes）：user:AAAAAAAAAAA
區塊 2（16 bytes）：;money:666667;BB
區塊 3（16 bytes）：;money:10; + 6 個補零 bytes
```

`user:` 是 5 bytes，11 個 `A` 讓第一塊剛好填滿。第二塊的長度是 `7（;money:）+ 6（666667）+ 1（;）+ 2（BB）= 16`。

拿到加密 token 後，只保留前 **32 bytes**，也就是十六進位字串的前 **64 個字元**，提交給 `token =`。伺服器解密後得到：

```text
user:AAAAAAAAAAA;money:666667;BB
```

這會被切成三段：

```text
user  = user:AAAAAAAAAAA
money = money:666667
_     = BB
```

`666667 > 666666`，因此取得 flag：`PH{y0u_AR3_sO_rICH!}`。

## 終端機互動範例

下面是一次實際連線的紀錄；`user =` 和第二個 `token =` 後面的內容是我們輸入的。服務每次會產生新金鑰，因此**下方 token 只能用於這一次連線**。

```text
$ nc 10.99.70.3 40001
user = AAAAAAAAAAA;money:666667;BB
token = b76db925c3fea141c39d327e68383c4193c955fd21fda51bf65de3219c2cef893917e2fe46d51b3c75d1dfc8028b259d
token = b76db925c3fea141c39d327e68383c4193c955fd21fda51bf65de3219c2cef89
PH{y0u_AR3_sO_rICH!}
```

第一個 `token =` 是服務印出的 **96 個 hex 字元**（3 個區塊）；第二個 `token =` 要輸入它的**前 64 個 hex 字元**（2 個區塊）。新的連線要重新取當次輸出的前 64 個字元，不能照抄上面的舊 token。

## 變化與容易犯的錯

**`money` 不一定要從區塊開頭開始。** 我們保留的是連續的前兩塊，所以只要目標明文在前 32 bytes 內，且切成三段即可。例如輸入：

```text
AAAAAAAA;money:666666666;BB
```

前 32 bytes 會是 `user:AAAAAAAA;money:666666666;BB`，同樣有效。使用者名稱少 3 個 `A`，金額便能多 3 位數。

但 `user:AAAAAAAAAAA;money:666666666` **不能直接作為截斷後的 token 明文**：它只有一個分號，`split(b';')` 只會得到兩段；若把原本的 `;money:10;` 也保留下來，又會切出多於三段。另要記得，`user =` 提示只要輸入使用者欄位的內容，程式會自動加上 `user:`。

## 核心觀念

加密只能隱藏內容，不能保證內容沒有被截取或修改。這題用 ECB 加密 token，卻沒有驗證其完整性；攻擊者便能藉由保留部分密文，讓伺服器解析出自己指定的金額。

本題的連線腳本：[solve.js](solve.js)。在此資料夾的上一層執行 `node "Crypytography 1029/solve.js"` 即可重現。
