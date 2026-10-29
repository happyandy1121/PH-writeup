"""MD5 候選比對：固定開頭、結尾與總長度，枚舉中間的字元。"""

import hashlib
import itertools
import string
import time


# ===== 之後修改這裡 =====
TARGET_HASH = "dfb3d86e2f71fc381012b1beeba20937"
LENGTH = 8  # 完整原文的總字元數，包含 PREFIX 與 SUFFIX
PREFIX = "PH{"
SUFFIX = "}"
CHARSET = string.ascii_letters + string.digits + string.punctuation + " "
# 只猜數字：CHARSET = string.digits
# 只猜小寫英文：CHARSET = string.ascii_lowercase
# ========================


def crack_md5(target_hash, length, prefix, suffix, charset, show_progress=False):
    """回傳符合 MD5 的字串；完整搜尋後無解則回傳 None。採 UTF-8 編碼。"""
    target_hash = target_hash.strip().lower()
    if len(target_hash) != 32 or any(c not in string.hexdigits for c in target_hash):
        raise ValueError("TARGET_HASH 必須是 32 位十六進位 MD5。")
    if type(length) is not int or length < len(prefix) + len(suffix):
        raise ValueError("LENGTH 必須是整數，且不能小於開頭加結尾的長度。")
    unknown_length = length - len(prefix) - len(suffix)
    charset = "".join(dict.fromkeys(charset))
    if unknown_length > 0 and not charset:
        raise ValueError("還有未知字元時，CHARSET 不能留空。")

    target = bytes.fromhex(target_hash)
    prefix_bytes = prefix.encode("utf-8")
    suffix_bytes = suffix.encode("utf-8")
    symbols = [char.encode("utf-8") for char in charset]
    total = len(symbols) ** unknown_length
    start = time.monotonic()
    if show_progress:
        print(f"總長度 = {length}；未知字元數 = {unknown_length}")
        print(f"字元種類 = {len(symbols)}；候選數 = {total:,}", flush=True)

    for tried, middle in enumerate(itertools.product(symbols, repeat=unknown_length), 1):
        candidate = prefix_bytes + b"".join(middle) + suffix_bytes
        if hashlib.md5(candidate).digest() == target:
            return candidate.decode("utf-8")
        if show_progress and tried % 1_000_000 == 0:
            elapsed = time.monotonic() - start
            print(f"已搜尋 {tried:,}/{total:,}，經過 {elapsed:.1f} 秒", flush=True)
    return None


def main():
    try:
        plaintext = crack_md5(TARGET_HASH, LENGTH, PREFIX, SUFFIX, CHARSET, True)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    except KeyboardInterrupt:
        raise SystemExit("\n已停止搜尋。") from None

    if plaintext is None:
        print("目前的長度、開頭、結尾與字元範圍內沒有找到結果。")
        return
    print(f"找到原文：{plaintext!r}")
    print(f"驗證 MD5：{hashlib.md5(plaintext.encode('utf-8')).hexdigest()}")


if __name__ == "__main__":
    main()
