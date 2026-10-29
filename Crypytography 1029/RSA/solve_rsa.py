"""RSA 解題：填入 n、e、C，再依已知資訊選擇方式。

有質因數：填 p、q，可選填 r 與各自的 power，用私鑰解密。
沒有質因數：p、q、r 都留 None，嘗試低指數攻擊。
質因數模式的底數必須是不同質數；一般 RSA 的次方都填 1。
請自行確認填入的因數是質數；程式不做質因數分解或質數檢測。
低指數模式搜尋 m**e = C + k*n；不保證所有小 e 的題目都能解開。
無須安裝額外套件。
"""

from itertools import count
from math import gcd, prod


# ===== 在這裡填入資料 =====
n = 1637398304753367121187260747056122259393942398399761387242025733392993548960861835474754194034919024431979533556739
e = 3
C = 1043833875788103294251922712228155602305707907222550685595732076887614134057517287824824043020048575641617885067077
# 有質因數時填入底數；沒有時全部保留 None。
p = None
p_power = 1
q = None
q_power = 1
r = None  # 第三個質數可選填
r_power = 1

# 沒有重複質因數的一般 RSA，將各個 power 設成 1。
MAX_K = None  # 低指數模式：None 表示不設搜尋上限；也可填 50_000_000 等整數

# =================================


def decrypt(n, p, q, e, c, r=None, p_power=1, q_power=1, r_power=1):
    """使用自行提供的質數與次方計算私鑰 d 與明文整數 m。"""
    if p is None or q is None:
        raise ValueError("請先將 p、q 的 None 換成題目提供的質數。")
    factors = [p, q] if r is None else [p, q, r]
    powers = [p_power, q_power] if r is None else [p_power, q_power, r_power]
    if any(type(value) is not int for value in (n, e, c, *factors)):
        raise ValueError("n、p、q、e、C 與選填的 r 都必須是整數。")
    if any(value < 2 for value in factors) or len(set(factors)) != len(factors):
        raise ValueError("填入的質數必須互不相同，且都大於等於 2。")
    if any(type(power) is not int or power < 1 for power in powers):
        raise ValueError("各質數的 power 必須是大於等於 1 的整數。")
    if prod(base ** power for base, power in zip(factors, powers)) != n:
        raise ValueError("各質數的次方乘積不等於 n，請檢查質數與 power。")
    if n < 6 or e <= 1 or not 0 <= c < n:
        raise ValueError("請確認 n >= 6、e > 1，且 0 <= c < n。")

    # phi(p**k) = p**(k-1) * (p-1)，不同質數的結果可相乘。
    phi = prod(
        base ** (power - 1) * (base - 1)
        for base, power in zip(factors, powers)
    )
    if gcd(e, phi) != 1:
        raise ValueError("e 與 phi(n) 不互質，無法計算私鑰 d。")

    d = pow(e, -1, phi)
    m = pow(c, d, n)
    if pow(m, e, n) != c:
        raise ValueError(
            "重新加密驗證失敗，請確認填入的底數都是質數，並核對題目條件。"
        )
    return p, q, phi, d, m


def integer_root(value, degree):
    """用整數運算求 floor(value**(1/degree))，避免浮點誤差。"""
    if value < 2:
        return value
    x = 1 << ((value.bit_length() + degree - 1) // degree)
    while True:
        y = ((degree - 1) * x + value // x ** (degree - 1)) // degree
        if y >= x:
            return x
        x = y


def solve_low_e(n, e, c, max_k):
    """搜尋完全 e 次方數，回傳 (m, k)；max_k=None 時不設搜尋上限。"""
    if any(type(value) is not int for value in (n, e, c)):
        raise ValueError("n、e、C 都必須是整數。")
    if max_k is not None and (type(max_k) is not int or max_k < 0):
        raise ValueError("MAX_K 必須是 None 或大於等於 0 的整數。")
    if n <= 1 or not 0 <= c < n:
        raise ValueError("請確認 n > 1、0 <= C < n。")
    if not 2 <= e <= 17:
        raise ValueError("此程式的低指數模式支援 2 <= e <= 17；若有質因數請填入 p、q。")

    m = integer_root(c, e)
    if m ** e == c:
        return m, 0

    # 小模數篩選只排除不可能的 k，不分解 n，也不會漏掉範圍內的解。
    residues, modulus = [0], 1
    for small_modulus in (9, 7, 13, 19, 31):
        possible = {pow(x, e, small_modulus) for x in range(small_modulus)}
        residues = [
            residue + j * modulus
            for residue in residues
            for j in range(small_modulus)
            if (c + (residue + j * modulus) * n) % small_modulus in possible
        ]
        modulus *= small_modulus
    residues.sort()
    if not residues:
        return None

    offsets = count(0, modulus) if max_k is None else range(0, max_k + 1, modulus)
    for offset in offsets:
        for residue in residues:
            k = offset + residue
            if max_k is not None and k > max_k:
                break
            if k == 0:
                continue
            value = c + k * n
            m = integer_root(value, e)
            if m ** e == value and m < n:
                return m, k
    return None


def main():
    print(f"n = {n}, e = {e}, c = {C}")
    try:
        if p is None and q is None and r is None:
            print("模式：低指數攻擊")
            if MAX_K is None:
                print("搜尋不設上限，可按 Ctrl+C 停止。", flush=True)
            result = solve_low_e(n, e, C, MAX_K)
            if result is None:
                if MAX_K is None:
                    print("小模數檢查已排除所有 k，這組數字不適用此方法。")
                else:
                    print(f"在 0 <= k <= {MAX_K} 內沒有找到結果。")
                    print("可增加 MAX_K、改成 None，或檢查題目是否需要其他攻擊條件。")
                return
            m, k = result
            print(f"k = {k}")
        else:
            print("模式：已知質因數解密")
            _, _, phi, d, m = decrypt(
                n, p, q, e, C, r=r,
                p_power=p_power, q_power=q_power, r_power=r_power,
            )
            print(f"p = {p}, p_power = {p_power}")
            print(f"q = {q}, q_power = {q_power}")
            if r is not None:
                print(f"r = {r}, r_power = {r_power}")
            print(f"phi(n) = {phi}")
            print(f"d = {d}")
    except ValueError as error:
        raise SystemExit(str(error)) from error
    except KeyboardInterrupt:
        raise SystemExit("\n已停止搜尋。") from None

    if pow(m, e, n) != C:
        raise SystemExit("重新加密驗證失敗，請核對輸入。")
    print(f"m = {m}")
    print("重新加密驗證：通過")

    # 假設題目將文字編成大端序整數；原題若採用其他編碼，需另行解讀。
    raw = m.to_bytes(max(1, (m.bit_length() + 7) // 8), "big")
    print(f"明文 bytes = {raw!r}")
    try:
        print(f"明文文字（UTF-8）= {raw.decode('utf-8')!r}")
    except UnicodeDecodeError:
        print("明文無法直接以 UTF-8 解碼，請依題目的編碼解讀 m。")


if __name__ == "__main__":
    main()
