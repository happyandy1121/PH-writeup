# Padding Oracle 題目筆記（40004）

## 題目流程

伺服器把 FLAG 加上 PKCS#7 padding，用 AES-CBC 加密，先印出：

```text
flag = hex(IV || C1 || C2 || ...)
```

之後可以反覆輸入十六進位密文。伺服器解密並檢查 padding，回覆 `PADDING CORRECT!!!` 或 `PADDING ERROR!!!`。它沒有直接顯示明文，但這個**正確／錯誤的差別**就是會洩漏資訊的 padding oracle。

## CBC 解密與可控制的部分

對任一密文區塊 `Ci`，它的原始明文是：

```text
Pi = 解密(Ci) XOR X
```

`X` 是它前一個密文區塊；若 `Ci` 是第一塊，`X` 就是 IV。我們可以單獨提交 `X' || Ci`，讓自訂的 `X'` 當作 IV。`解密(Ci)` 不變，但 `X'` 會改變這一塊的明文。服務對修改後明文的 padding 回覆正確或錯誤，便能用來猜原始的 `Pi`。

## 怎麼從最後一個 byte 開始猜？

先只改 `X` 的最後一個 byte，目標是讓解密後的最後一個 byte 變成 `01`。對每個候選明文字元 `g`，設定：

```text
X'[15] = X[15] XOR g XOR 01
```

若 oracle 回覆 `PADDING CORRECT!!!`，表示猜測可能正確。接著要**再改倒數第二個 byte 測一次**：真正的 `01` padding 仍會有效；若剛才只是碰巧保留原本較長的 padding，就會失效。這能排除常見的第一步誤判。

得到最後一個明文 byte 後，目標改為讓尾端兩個 bytes 都是 `02 02`。已知最後一個明文 byte 是 `P[15]`，就設定：

```text
X'[15] = X[15] XOR P[15] XOR 02
X'[14] = X[14] XOR 猜測的 P[14] XOR 02
```

oracle 回覆正確時，就找到 `P[14]`。接著讓尾端三個 bytes 都變成 `03`，依序往左推，直到整個 16-byte 區塊還原。對每一個密文區塊都重複這個流程，最後去掉 PKCS#7 padding。

## 終端機互動範例

下面是同一次連線的實際數值。服務先印出 `IV || C1 || C2`。我們只取 `C1 || C2` 提交，讓原本的 `C1` 當成新的 IV；它會解出原本的最後一個明文區塊，因此 padding 正確。

```text
$ nc 10.99.70.3 40004
flag = 621d1f2ceaf7e7a9efd799309c7567dd843a0f11cd69c61d3e4ade043c91921695c0e27d2ed4e418de541bf34d3799e8
cipher = 843a0f11cd69c61d3e4ade043c91921695c0e27d2ed4e418de541bf34d3799e8
PADDING CORRECT!!!
cipher = 843a0f11cd69c61d3e4ade043c91921795c0e27d2ed4e418de541bf34d3799e8
PADDING ERROR!!!
cipher = 843a0f11cd69c61d3e4ade043c91921595c0e27d2ed4e418de541bf34d3799e8
PADDING CORRECT!!!
```

三次輸入只差在「當作 IV 的 `C1`」最後一個 byte：原值 `16` 得到正確；XOR `01` 後變 `17`，得到錯誤；XOR `03` 後變 `15`，又得到正確。原本的最後兩個明文 bytes 是 `02 02`，所以 XOR `03` 會把最後一個 `02` 改成 `01`，形成有效的單 byte padding。**這些密文只能搭配此範例的同一次連線使用**；新連線要重新讀取當次的 `flag =`。

## 提示檔的空格

`40004_hint.py` 使用 `find` 保存目前已找到的原始明文後綴。各空格依序可填：

```python
IV[:index]
bytes([exhaustive])
find
IV[index + 1:]
bytes([exhaustive ^ padding ^ IV[index]]) + find
```

其中後綴的新 IV 值是 `padding XOR 已知明文 XOR 原 IV`。提示檔用「略過未修改的最後一個 byte」處理第一步可能遇到的舊 padding；[solve_padding_oracle.js](solve_padding_oracle.js) 另外做一次驗證查詢，排除較長 padding 造成的誤判。

## 結果與核心觀念

實測還原的兩個明文區塊最後以 `02 02` 結尾。去掉 padding 後得到：

```text
PH{RU_p4dD1NG_BY73_genER@T0R?}
```

問題不在於 AES 金鑰被破解，而是服務對修改後密文給出了**可區分的 padding 檢查結果**。反覆查詢這個結果，便能逐 byte 還原原始明文。執行 `node "Crypytography 1029/solve_padding_oracle.js" --demo` 可看到三次示範查詢；不加 `--demo` 則會跑完整還原。
