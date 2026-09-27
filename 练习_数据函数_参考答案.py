# -*- coding: utf-8 -*-
"""
============================================================
参考答案 —— 请先自己写！卡壳超过 10 分钟再看这里 🙈
============================================================

对照要点：不是看你写的和这里"长得像不像"，而是看：
  1. 能不能跑通（测试区全绿）
  2. 你能不能用自己的话说出每一行在干嘛

自己写完再看答案，收获是抄答案的 10 倍。
============================================================
"""

import pandas as pd


# ---------------- 第 1 题 ----------------
def calc_ma(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    # 关键点 1：.copy() —— 不修改传入的原表，避免"副作用"
    #         （这是函数式编程的基本礼貌，也是 pandas 最常见的坑）
    out = df.copy()

    # 关键点 2：rolling 是"滑动窗口"，mean() 求窗口内平均
    #         前 window-1 个位置数据不够，会自动是 NaN
    out[f"MA{window}"] = out["close"].rolling(window).mean()

    return out


# ---------------- 第 2 题 ----------------
def max_drawdown(close: pd.Series) -> float:
    # 第 1 步：算出"到目前为止的历史最高价"
    #         cummax = cumulative maximum，逐行往后取最大值
    running_max = close.cummax()

    # 第 2 步：算每一天相对历史最高价跌了多少（都是 ≤0 的数）
    drawdown = (close - running_max) / running_max

    # 第 3 步：最小（最负）的那个就是最大回撤
    mdd = drawdown.min()

    # 转成百分比
    return float(mdd * 100)


# ---------------- 第 3 题 ----------------
def detect_cross(df: pd.DataFrame, fast: int = 20, slow: int = 60):
    # 复用第 1 题的函数 —— 这就是为什么要写成函数，而不是复制粘贴代码
    d = calc_ma(df, window=fast)
    d = calc_ma(d, window=slow)

    fast_col, slow_col = f"MA{fast}", f"MA{slow}"
    diff = d[fast_col] - d[slow_col]

    # 昨天的差值：用 shift(1) 把整列往下挪一行
    prev = diff.shift(1)

    # 金叉：今天快线在上（diff>0），昨天还在下（prev<=0）→ 刚穿上去
    golden_mask = (diff > 0) & (prev <= 0)

    # 死叉：正好反过来
    dead_mask = (diff < 0) & (prev >= 0)

    # 取出对应的日期（NaN 行天然不满足条件，不用额外处理）
    golden_dates = d.loc[golden_mask, "date"].tolist()
    dead_dates = d.loc[dead_mask, "date"].tolist()

    return golden_dates, dead_dates


# ============================================================
# 直接运行本文件 = 跑练习文件里那套测试，看是否全绿
# ============================================================
if __name__ == "__main__":
    import runpy
    import sys

    print("用参考答案验证测试区：\n")
    # 把本文件的函数"注入"到练习文件的命名空间里跑测试
    src = open("练习_数据函数.py", encoding="utf-8").read()
    # 去掉练习文件里那三个空函数定义，用答案版本替换
    ns = {
        "__name__": "__main__",
        "calc_ma": calc_ma,
        "max_drawdown": max_drawdown,
        "detect_cross": detect_cross,
        "pd": pd,
    }
    body = src.split("if __name__")[0]
    # 只执行 import 部分，函数定义用答案覆盖
    exec("import pandas as pd\n", ns)
    test_part = "if __name__" + src.split("if __name__", 1)[1]
    exec(test_part, ns)
