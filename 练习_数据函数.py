# -*- coding: utf-8 -*-
"""
============================================================
✏️ 数据分析函数练习（Copilot 第一次实战）
============================================================

【怎么用这个文件】

1. 打开 VS Code 左下角的「运行」按钮，或按 Cmd+Shift+D 左侧调出运行面板
   最简单的方式：点右上角那个 ▷ 三角形按钮 → 选 "Run Python File"

2. 每道题下面有一个 `pass` 占位符，把光标放在 pass 上面一行，
   **敲两下回车，等一秒** —— Copilot 会灰字弹出建议代码
   → 按 **Tab** 接受建议
   → 按 **Esc** 拒绝，继续自己写

3. 写完一题就运行一次，看输出对不对。三题全绿，说明你掌握了
   数据分析最核心的三个运算：移动平均 / 最大回撤 / 信号检测。

【运行前确认】
   解释器必须是 Anaconda（左下角/右下角状态栏显示 anaconda3）
   如果显示的是别的 Python，按 Cmd+Shift+P → Python: Select Interpreter
   → 选 /Users/liuaowu/anaconda3/bin/python

【卡住了怎么办】
   同目录有 `练习_数据函数_参考答案.py`。
   但请先自己动手写满 10 分钟再看 —— 直接抄的答案记不住。
   看的时候对照自己的思路差异，而不是比谁写得短。

作者：LIU Aowu  |  BNBU 金融数学
============================================================
"""

import pandas as pd


# ============================================================
# 第 1 题：移动平均线（MA）
# ============================================================
# 需求：给 DataFrame 增加一列，列名为 f"MA{window}"，
#       值是收盘价（close 列）的 window 日简单移动平均。
# 返回：增加新列后的 DataFrame（不改原数据，用 .copy()）
#
# 提示：df["新列名"] = df["close"].rolling(window).mean()
# ------------------------------------------------------------
def calc_ma(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    # TODO: 在这里写代码，Copilot 会帮你补全 → 按 Tab 接受建议
    pass


# ============================================================
# 第 2 题：最大回撤（Max Drawdown）
# ============================================================
# 需求：算出一段价格序列的最大回撤，返回一个负数百分比。
#
# 公式：
#   历史最高价 = 价格的累计最大值（cummax）
#   回撤 = (价格 - 历史最高价) / 历史最高价
#   最大回撤 = 所有回撤里最小的那个（因为都是负数，最小 = 亏得最多）
#
# 例子：价格从 100 涨到 120，再跌到 90
#      回撤 = (90 - 120) / 120 = -25%  → 返回 -25.0
#
# 提示：用 .cummax() 和 .min()
# ------------------------------------------------------------
def max_drawdown(close: pd.Series) -> float:
    # TODO: 在这里写代码
    pass


# ============================================================
# 第 3 题：检测均线金叉 / 死叉
# ============================================================
# 需求：给定快线周期和慢线周期，找出所有"金叉"和"死叉"的日期。
#
#   金叉（golden cross）= 快线从下方穿过慢线 → 常被视为买入信号
#   死叉（dead cross）  = 快线从上方跌破慢线 → 常被视为卖出信号
#
# 返回：两个列表 (golden_dates, dead_dates)，元素是日期字符串
#
# 判定技巧：算 diff = MA快 - MA慢
#   金叉 = 今天 diff > 0 且 昨天 diff <= 0
#   死叉 = 今天 diff < 0 且 昨天 diff >= 0
#   （用 .shift(1) 取"前一行"的值）
#
# 提示：可以调用你第 1 题写的 calc_ma() —— 代码复用就是这么来的
# ------------------------------------------------------------
def detect_cross(df: pd.DataFrame, fast: int = 20, slow: int = 60):
    # TODO: 在这里写代码
    pass


# ============================================================
# ✅ 测试区（已写好，不用改。函数写完后直接运行本文件）
# ============================================================
if __name__ == "__main__":

    # 读取海螺水泥的日 K 数据（前复权，来自 akshare）
    CSV = "海螺水泥/海螺水泥_600585_日K.csv"
    df = pd.read_csv(CSV, encoding="utf-8-sig")
    print(f"读取数据：{CSV}")
    print(f"共 {len(df)} 个交易日，区间 {df['date'].iloc[0]} ~ {df['date'].iloc[-1]}\n")

    # ---------- 测试 1 ----------
    print("=" * 55)
    print("测试 1：移动平均线")
    print("=" * 55)
    try:
        result = calc_ma(df, window=20)
        if result is None:
            print("  ⏳ 还没写（返回了 None）")
        elif "MA20" not in result.columns:
            print(f"  ❌ 没生成 MA20 列。当前列：{list(result.columns)}")
        else:
            last = result["MA20"].iloc[-1]
            # 手算验证：最后 20 个收盘价的平均
            manual = df["close"].tail(20).mean()
            match = abs(last - manual) < 0.0001 if pd.notna(last) else False
            print(f"  最后一天 MA20 = {last:.4f}")
            print(f"  手算校验     = {manual:.4f}   {'✅ 一致' if match else '❌ 不一致'}")
    except Exception as e:
        print(f"  ❌ 出错：{type(e).__name__}: {e}")

    # ---------- 测试 2 ----------
    print("\n" + "=" * 55)
    print("测试 2：最大回撤")
    print("=" * 55)
    try:
        mdd = max_drawdown(df["close"])
        if mdd is None:
            print("  ⏳ 还没写（返回了 None）")
        else:
            print(f"  最大回撤 = {mdd:.2f}%")
            pct = mdd * 100 if abs(mdd) < 1 else mdd   # 兼容返回小数或百分比两种写法
            if pct > 0:
                print("  ⚠️ 提示：最大回撤应该是负数，检查一下正负号")
            else:
                # 交叉验证：找出最高点之后的实际跌幅
                cummax = df["close"].cummax()
                idx = (df["close"] - cummax).idxmin()
                peak_date = df.loc[:idx, "close"].idxmax()
                print(f"  最低点出现在 {df['date'].iloc[idx]}（{df['close'].iloc[idx]:.2f} 元）")
                print(f"  此前最高点 {df['date'].iloc[peak_date]}（{df['close'].iloc[peak_date]:.2f} 元）")
    except Exception as e:
        print(f"  ❌ 出错：{type(e).__name__}: {e}")

    # ---------- 测试 3 ----------
    print("\n" + "=" * 55)
    print("测试 3：金叉 / 死叉检测")
    print("=" * 55)
    try:
        outcome = detect_cross(df, fast=20, slow=60)
        if outcome is None:
            print("  ⏳ 还没写（返回了 None）")
        else:
            golden, dead = outcome
            print(f"  近一年金叉 {len(golden)} 次：{golden[-6:] if golden else '无'}")
            print(f"  近一年死叉 {len(dead)} 次：{dead[-6:] if dead else '无'}")
    except Exception as e:
        print(f"  ❌ 出错：{type(e).__name__}: {e}")

    print("\n" + "=" * 55)
    print("三题全绿后，把结果截图发我，我带你上 B 方案（回测）")
    print("=" * 55)
