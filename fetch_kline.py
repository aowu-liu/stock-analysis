# -*- coding: utf-8 -*-
"""
通用 A 股日K数据拉取脚本（腾讯财经公开接口）
用法:
    python fetch_kline.py 600900 长江电力
    python fetch_kline.py 600585 海螺水泥
输出:
    <名称>_<代码>_日K.csv (date,open,close,high,low,volume,pct_change)
"""
import os
# 本机有代理环境变量注入时先清掉,避免请求被拦截
for k in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"]:
    os.environ.pop(k, None)

import sys
import time
import requests
import pandas as pd

def fetch_daily(code: str, days: int = 600) -> pd.DataFrame:
    """拉取日K线(前复权),返回 DataFrame"""
    url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
    params = {"param": f"{code},day,,,{days},qfq"}
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, timeout=15)
            r.raise_for_status()
            node = r.json()["data"][code]
            rows = node.get("qfqday") or node.get("day")
            if not rows:
                raise ValueError(f"接口返回空数据: {code}")
            df = pd.DataFrame(
                [row[:6] for row in rows],   # 取前6列: 日期,开,收,高,低,成交量(手)
                columns=["date", "open", "close", "high", "low", "volume"]
            )
            df["volume"] = df["volume"].astype(float) * 100  # 手 -> 股
            for c in ["open", "close", "high", "low"]:
                df[c] = df[c].astype(float)
            df["pct_change"] = (df["close"].pct_change() * 100).round(2)
            df = df[["date", "open", "close", "high", "low", "volume", "pct_change"]]
            return df
        except Exception as e:
            print(f"第{attempt+1}次尝试失败: {e}")
            time.sleep(2)
    raise RuntimeError(f"拉取 {code} 数据失败")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python fetch_kline.py <代码> <名称> [天数]")
        sys.exit(1)
    code, name = sys.argv[1], sys.argv[2]
    days = int(sys.argv[3]) if len(sys.argv) > 3 else 600
    market = "sh" if code.startswith("6") else ("sz" if code.startswith(("0", "3")) else "")
    symbol = f"{market}{code}"
    df = fetch_daily(symbol, days)
    out = f"{name}_{code}_日K.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"已保存 {out}: {len(df)} 行, {df['date'].iloc[0]} ~ {df['date'].iloc[-1]}")
    print(f"期末收盘 {df['close'].iloc[-1]:.2f} 元, 区间涨跌 {(df['close'].iloc[-1]/df['close'].iloc[0]-1)*100:+.2f}%")
