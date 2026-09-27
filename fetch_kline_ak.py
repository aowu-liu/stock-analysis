# -*- coding: utf-8 -*-
"""
fetch_kline_ak.py —— 用 akshare 拉取 A 股日 K 线 + 基本面数据（通用版）

对比旧版 fetch_kline.py（腾讯接口）的升级点：
  1. 数据源换成 akshare（社区维护，非野接口），字段多了成交额/振幅/涨跌幅/换手率
  2. 顺便拉取基本面：总市值、流通市值、行业分类
  3. 顺便拉取财务摘要（80 个指标 × 100+ 期）

用法：
    python fetch_kline_ak.py 600585 海螺水泥              # 默认 490 个交易日
    python fetch_kline_ak.py 600900 长江电力 750          # 自定义天数

输出（存到当前目录）：
    <名称>_<代码>_日K.csv        —— 日 K 线数据（列名与旧版兼容，可被 generate_report.py 直接读取）
    <名称>_<代码>_基本信息.csv    —— 市值 / 行业等
    <名称>_<代码>_财务摘要.csv    —— 主要财务指标（按报告期）

作者：嗷呜（BNBU 金融数学）+ 小助手
"""
import os
import sys

# ---- 第 0 步：清掉环境里的代理变量 ----
# 说明：本机被注入了 HTTP_PROXY，不清掉会导致请求全部失败。
# 这是踩过的坑，务必保留。
for _k in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"]:
    os.environ.pop(_k, None)

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import akshare as ak


# ============================================================
# 函数 1：拉取日 K 线
# ============================================================
def fetch_daily_kline(code: str, days: int = 490) -> pd.DataFrame:
    """
    拉取 A 股日 K 线（前复权 qfq）。

    参数：
        code: 6 位股票代码，如 "600585"
        days: 取最近多少个交易日

    返回：DataFrame，列 = date / open / close / high / low / volume / amount /
                        amplitude / pct_change / change / turnover
    """
    # akshare 的东财接口需要 YYYYMMDD 格式的起止日期。
    # 为了拿够 days 个交易日，起点往前多推一些日历日（交易日约占日历日 7 成）。
    end = pd.Timestamp.today()
    start = end - pd.Timedelta(days=int(days * 1.6) + 30)

    df = ak.stock_zh_a_hist(
        symbol=code,
        period="daily",
        start_date=start.strftime("%Y%m%d"),
        end_date=end.strftime("%Y%m%d"),
        adjust="qfq",          # qfq = 前复权；不复权用 ""，后复权用 "hfq"
    )
    if df is None or df.empty:
        raise RuntimeError(f"未取到 {code} 的日 K 数据，请检查代码是否正确")

    # 中文列名 → 英文列名（统一成旧脚本的格式，保证下游脚本不用改）
    column_map = {
        "日期": "date",
        "开盘": "open",
        "收盘": "close",
        "最高": "high",
        "最低": "low",
        "成交量": "volume",       # 单位：手
        "成交额": "amount",       # 单位：元
        "振幅": "amplitude",      # 单位：%
        "涨跌幅": "pct_change",   # 单位：%
        "涨跌额": "change",       # 单位：元
        "换手率": "turnover",     # 单位：%
    }
    df = df.rename(columns=column_map)

    # 只保留需要的列（顺序和旧版前 7 列一致）
    keep = ["date", "open", "close", "high", "low", "volume",
            "pct_change", "amount", "amplitude", "change", "turnover"]
    df = df[[c for c in keep if c in df.columns]].copy()

    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

    # 只取最后 days 根（上面的日期推算是为了确保数量够）
    df = df.tail(days).reset_index(drop=True)

    # 成交量：手 → 股（1 手 = 100 股），与旧版口径保持一致
    df["volume"] = df["volume"] * 100

    return df


# ============================================================
# 函数 2：拉取基本信息（市值 / 行业）
# ============================================================
def fetch_basic_info(code: str) -> pd.DataFrame:
    """拉取个股基本信息：最新价、总股本、流通股、总市值、流通市值、行业"""
    return ak.stock_individual_info_em(symbol=code)


# ============================================================
# 函数 3：拉取财务摘要
# ============================================================
def fetch_financial_abstract(code: str) -> pd.DataFrame:
    """拉取财务摘要（按报告期的多期指标，列数很多）"""
    return ak.stock_financial_abstract(symbol=code)


# ============================================================
# 主流程
# ============================================================
def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    code = sys.argv[1]                                  # 股票代码
    name = sys.argv[2]                                  # 股票名称
    days = int(sys.argv[3]) if len(sys.argv) > 3 else 490

    print(f"正在拉取 {name}（{code}）最近 {days} 个交易日...")

    # --- 日 K 线 ---
    kline = fetch_daily_kline(code, days)
    kline_file = f"{name}_{code}_日K.csv"
    kline.to_csv(kline_file, index=False, encoding="utf-8-sig")
    print(f"  [OK] {kline_file}  {len(kline)} 行")
    print(f"       区间 {kline['date'].iloc[0]} ~ {kline['date'].iloc[-1]}"
          f"  期末收盘 {kline['close'].iloc[-1]}")

    # --- 基本信息 ---
    try:
        info = fetch_basic_info(code)
        info_file = f"{name}_{code}_基本信息.csv"
        info.to_csv(info_file, index=False, encoding="utf-8-sig")
        print(f"  [OK] {info_file}")
        # 打印成人类可读的形式
        row = dict(zip(info["item"], info["value"]))
        print(f"       行业 {row.get('行业')} | 总市值 {float(row.get('总市值', 0)) / 1e8:.2f} 亿元"
              f" | 流通市值 {float(row.get('流通市值', 0)) / 1e8:.2f} 亿元")
    except Exception as e:
        print(f"  [跳过] 基本信息获取失败：{e}")

    # --- 财务摘要 ---
    try:
        fin = fetch_financial_abstract(code)
        fin_file = f"{name}_{code}_财务摘要.csv"
        fin.to_csv(fin_file, index=False, encoding="utf-8-sig")
        print(f"  [OK] {fin_file}  {fin.shape[0]} 个指标 × {fin.shape[1] - 2} 期")
    except Exception as e:
        print(f"  [跳过] 财务摘要获取失败：{e}")

    print("全部完成")


if __name__ == "__main__":
    main()


# ============================================================
# ✏️ 练习区（留给你自己写，Copilot 会帮你补全）
# ============================================================
# 练习 1：写一个函数 calc_ma(df, window)，给传入的 DataFrame 增加一列
#         f"MA{window}"，值为收盘价的 window 日简单移动平均。
#
# 练习 2：写一个函数 max_drawdown(close_series)，计算最大回撤（返回负数百分比）。
#         提示：最大回撤 = min((价格 - 历史最高价) / 历史最高价)
#
# 练习 3（进阶）：修改 fetch_daily_kline，让 adjust 变成一个参数，
#         默认 "qfq"，这样调用时可以选择不复权数据做对比。
#
# 写完后可以让我检查，或者直接在终端跑一下验证。
