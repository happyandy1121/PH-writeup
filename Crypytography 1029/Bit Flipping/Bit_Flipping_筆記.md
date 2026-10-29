# Bit Flipping 題目筆記（40003）

## 題目流程

伺服器先用 AES-CBC 加密已知明文 `b'A' * 32`，並印出：

```text
Base64(IV || 密文)
```

接著它讀入我們送回的 Base64，解碼、解密後檢查明文是否包含 `CTFGOGOGO`。包含就印出 FLAG。每次加密會產生新的 16-byte IV，但同一次連線內我們可以使用服務剛印出的 IV 來修改密文。

## 為什麼修改 IV 可以改變明文？

CBC 第一區塊的解密關係是：

```text
P1 = 解密(C1) XOR IV
```

原本 `P1` 的前 9 bytes 都是 `A`。若希望它們變成 `CTFGOGOGO`，只要對 IV 的前 9 bytes 做以下運算：

```text
新 IV[i] = 原 IV[i] XOR 'A'[i] XOR 'CTFGOGOGO'[i]
```

代回公式後，原本的 `A` 會被抵消，解密結果便成為想要的字元。例如第一個字元要從 `A`（`0x41`）變成 `C`（`0x43`），只需把 IV 第一個 byte XOR `0x02`，因為 `0x41 XOR 0x43 = 0x02`。

這個攻擊不需要知道金鑰。只改 IV，後面的密文區塊保持原樣，因此最後一區塊的 padding 也不受影響。

## 提示檔怎麼填

`40003_hint.py` 的三個空格可以填：

```python
plain_text = b'A' * 9
goal = b'CTFGOGOGO'

for i in range(9):
    cipher_text[i] = cipher_text[i] ^ plain_text[i] ^ goal[i]
```

`cipher_text` 是 Base64 解碼後的 `bytearray`，所以它的前 16 bytes 是 IV。改完後再 Base64 編碼並送回服務。

## 終端機互動範例

下面是一次實際連線的範例。第一行 Base64 是**服務輸出**；第二行 Base64 是我們修改 IV 後**輸入**的內容。這兩行看起來只改了開頭，因為只動到 IV 的前 9 bytes。

```text
$ nc 10.99.70.3 40003
rIO40Kej8Zq43H2aP5a0A8yVtUjjAIiidXqnmfQXUpvsyWMx5kccpmccxUcRKHX51NdYbttVqUonJzuVLl0swA==
rpa/1qml/5y23H2aP5a0A8yVtUjjAIiidXqnmfQXUpvsyWMx5kccpmccxUcRKHX51NdYbttVqUonJzuVLl0swA==
PH{X0R_pOw3r!}
```

**每次連線的 IV 都不同。** 第二行只能搭配本範例第一行使用；自己操作時，要解碼當次服務印出的 Base64、修改 IV，再送回重新編碼的結果。可執行 `node "Crypytography 1029/solve_bit_flipping.js" --demo`，讓腳本印出當次收到、送出的是哪兩行 Base64。

## 核心觀念

CBC 加密能隱藏明文，但如果接收方沒有驗證資料是否被修改，攻擊者可以透過改動 IV，精確控制**第一個明文區塊**的對應 bytes。這題只需改出 9-byte 的關鍵字，就能通過檢查並得到 `PH{X0R_pOw3r!}`。

可重跑的程式：[solve_bit_flipping.js](solve_bit_flipping.js)。
