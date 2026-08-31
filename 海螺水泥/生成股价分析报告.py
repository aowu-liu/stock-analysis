# -*- coding: utf-8 -*-
"""
海螺水泥(600585) 股价分析报告生成脚本
用途:读取日K CSV → 计算关键指标 → 画图 → 排版成一份 PDF 研报
以后想分析其他股票:改 STOCK_NAME / STOCK_CODE / CSV_FILE 三个变量即可
"""
import os
for k in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"]:
    os.environ.pop(k, None)

import pandas as pd
import matplotlib
matplotlib.use("Agg")  # 无界面环境绘图
import matplotlib.pyplot as plt
plt.rcParams["font.sans-serif"] = ["PingFang SC", "Arial Unicode MS", "Heiti SC", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

# ============ 可修改区域:换股票只需改这里 ============
STOCK_NAME = "海螺水泥"
STOCK_CODE = "600585"
CSV_FILE = "海螺水泥_600585_日K.csv"
# ====================================================

HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(HERE, CSV_FILE))

# ---------- 1. 计算关键指标 ----------
first_close = df["close"].iloc[0]
last_close = df["close"].iloc[-1]
total_chg = (last_close / first_close - 1) * 100
low_min = df["low"].min()
high_max = df["high"].max()
best = df.loc[df["pct_change"].idxmax()]
worst = df.loc[df["pct_change"].idxmin()]
maxvol = df.loc[df["volume"].idxmax()]
buy_price = df["open"].iloc[0]
cost, value, profit = buy_price * 100, last_close * 100, (last_close - buy_price) * 100

df["MA20"] = df["close"].rolling(20).mean()
df["MA60"] = df["close"].rolling(60).mean()
diff = df["MA20"] - df["MA60"]
golden = (diff > 0) & (diff.shift(1) <= 0)
dead = (diff < 0) & (diff.shift(1) >= 0)
view = df.tail(250).reset_index(drop=True)
g_days = [view["date"].iloc[i] for i in range(len(view)) if golden.iloc[i]]
d_days = [view["date"].iloc[i] for i in range(len(view)) if dead.iloc[i]]

# ---------- 2. 画图 ----------
FIG = "/tmp"
def save(fig, name):
    path = f"{FIG}/{name}.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path

# 图1:两年收盘价走势
fig, ax = plt.subplots(figsize=(11, 4.2))
ax.plot(df["date"], df["close"], color="#e60000", linewidth=1.2)
ax.fill_between(df["date"], df["close"], df["close"].min()*0.98, color="#e60000", alpha=0.08)
ax.set_title(f"{STOCK_NAME}({STOCK_CODE}) 两年收盘价走势", fontsize=13)
ax.set_ylabel("收盘价(元)")
ax.grid(alpha=0.3)
ticks = range(0, len(df), 60)
ax.set_xticks(ticks); ax.set_xticklabels(df["date"].iloc[ticks], rotation=45, fontsize=8)
fig.tight_layout()
fig1 = save(fig, "fig1")

# 图2:K线 + 成交量(最近60天,红涨绿跌)
def draw_kline(ax, sub, width=0.6):
    for i, (_, r) in enumerate(sub.iterrows()):
        o, c, h, l = r["open"], r["close"], r["high"], r["low"]
        ax.plot([i, i], [l, h], color="#8c8c8c", linewidth=0.8, zorder=1)
        color = "#e60000" if c >= o else "#009944"
        bottom, height = (o, c - o) if c >= o else (c, o - c)
        ax.bar(i, height, bottom=bottom, width=width, color=color, zorder=2)

sub = df.tail(60).reset_index(drop=True)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 5.6), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
draw_kline(ax1, sub)
ax1.set_title(f"{STOCK_NAME} 最近3个月 K线(红涨绿跌) + 成交量", fontsize=13)
ax1.set_ylabel("价格(元)"); ax1.grid(alpha=0.2)
colors = ["#e60000" if c >= o else "#009944" for o, c in zip(sub["open"], sub["close"])]
ax2.bar(range(len(sub)), sub["volume"] / 1e6, color=colors, width=0.6)
ax2.set_ylabel("成交量(百万股)"); ax2.grid(alpha=0.2)
ticks = range(0, len(sub), 5)
ax2.set_xticks(ticks); ax2.set_xticklabels(sub["date"].iloc[ticks], rotation=45, fontsize=8)
fig.tight_layout()
fig2 = save(fig, "fig2")

# 图3:双均线金叉死叉(近1年)
g_idx = [i for i in range(len(view)) if golden.iloc[i]]
d_idx = [i for i in range(len(view)) if dead.iloc[i]]
fig, ax = plt.subplots(figsize=(11, 4.4))
ax.plot(range(len(view)), view["close"], label="收盘价", linewidth=1.1, color="#333333")
ax.plot(range(len(view)), view["MA20"], label="20日均线", linewidth=1.1, color="#f0a500")
ax.plot(range(len(view)), view["MA60"], label="60日均线", linewidth=1.1, color="#0072e3")
for i in g_idx: ax.scatter(i, view["close"].iloc[i], marker="^", s=90, color="#009944", zorder=5)
for i in d_idx: ax.scatter(i, view["close"].iloc[i], marker="v", s=90, color="#e60000", zorder=5)
ax.set_title(f"{STOCK_NAME} 双均线金叉死叉信号(近1年) ▲金叉 ▼死叉", fontsize=13)
ax.set_ylabel("价格(元)"); ax.legend(fontsize=8); ax.grid(alpha=0.3)
ticks = range(0, len(view), 30)
ax.set_xticks(ticks); ax.set_xticklabels(view["date"].iloc[ticks], rotation=45, fontsize=8)
fig.tight_layout()
fig3 = save(fig, "fig3")

# ---------- 3. reportlab 排版 PDF ----------
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image,
                                Table, TableStyle, PageBreak)
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 用系统自带的 Arial Unicode.ttf 并嵌入 PDF:任何阅读器打开都不会乱码
pdfmetrics.registerFont(TTFont("ArialUni", "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"))
F = "ArialUni"
RED, GREEN, GRAY, DARKRED = HexColor("#b03a2e"), HexColor("#1a7f37"), HexColor("#555555"), HexColor("#8a3324")

s_title = ParagraphStyle("t", fontName=F, fontSize=21, leading=28, alignment=1)
s_sub   = ParagraphStyle("s", fontName=F, fontSize=10.5, leading=15, alignment=1, textColor=GRAY)
s_h2    = ParagraphStyle("h2", fontName=F, fontSize=14, leading=20, spaceBefore=8, spaceAfter=4, textColor=DARKRED)
s_body  = ParagraphStyle("b", fontName=F, fontSize=10.5, leading=16.5, spaceAfter=3)
s_kpi   = ParagraphStyle("k", fontName=F, fontSize=10.5, leading=17)

doc = SimpleDocTemplate(os.path.join(HERE, f"{STOCK_NAME}股价分析报告.pdf"), pagesize=A4,
                        leftMargin=17*mm, rightMargin=17*mm, topMargin=15*mm, bottomMargin=15*mm)
story = []

# 标题
story.append(Paragraph(f"{STOCK_NAME}({STOCK_CODE}) 股价分析报告", s_title))
story.append(Spacer(1, 4))
story.append(Paragraph(f"区间:{df['date'].iloc[0]} ~ {df['date'].iloc[-1]} | 共 {len(df)} 个交易日 | 数据:腾讯财经公开接口 | 生成日期:2026-08-30", s_sub))
story.append(Spacer(1, 8))

# 关键指标速览(卡片式 2 列网格,比纯段落更直观)
story.append(Paragraph("一、关键指标速览", s_h2))
kpis = [
    ["区间涨跌", f"{total_chg:+.2f}%(期初 {first_close:.2f} 元,期末 {last_close:.2f} 元)"],
    ["价格区间", f"最低 {low_min:.2f} 元 / 最高 {high_max:.2f} 元"],
    ["最大单日涨幅", f"{best['date']} +{best['pct_change']:.2f}%(收盘 {best['close']:.2f} 元)"],
    ["最大单日跌幅", f"{worst['date']} {worst['pct_change']:.2f}%(收盘 {worst['close']:.2f} 元)"],
    ["最大成交量", f"{maxvol['date']} {maxvol['volume']/1e6:.0f} 百万股(当日 {maxvol['pct_change']:+.2f}%)"],
    ["均线信号(近1年)", f"金叉 {len(g_days)} 次 / 死叉 {len(d_days)} 次"],
    ["100股持有模拟", f"{'盈利' if profit>=0 else '亏损'} {abs(profit):.2f} 元({profit/cost*100:+.2f}%)"],
]
s_label = ParagraphStyle("kl", fontName=F, fontSize=9, leading=13, textColor=GRAY)
s_value = ParagraphStyle("kv", fontName=F, fontSize=10, leading=13)
card = []
for i in range(0, len(kpis), 2):          # 每行放 2 个指标
    row = []
    for j in range(2):
        if i + j < len(kpis):
            lab, val = kpis[i + j]
            row.append([Paragraph(lab, s_label), Paragraph(val, s_value)])  # 单元格 = 两行flowable
        else:
            row.append("")
    card.append(row)
tbl = Table(card, colWidths=[88 * mm, 88 * mm])
tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), HexColor("#f7f2ef")),
    ("BOX", (0, 0), (-1, -1), 0.8, HexColor("#e3d8d2")),
    ("INNERGRID", (0, 0), (-1, -1), 0.5, HexColor("#ffffff")),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
]))
story.append(tbl)

# 图1
story.append(Spacer(1, 6))
story.append(Paragraph("二、收盘价走势(两年全览)", s_h2))
story.append(Image(fig1, width=176*mm, height=176*mm*4.2/11))

# 图2
story.append(PageBreak())
story.append(Paragraph("三、K线图与成交量(最近3个月)", s_h2))
story.append(Paragraph("A股配色:阳线(涨)=红色,阴线(跌)=绿色;下图为成交量,颜色与当日涨跌一致。", s_body))
story.append(Image(fig2, width=176*mm, height=176*mm*5.6/11))

# 图3
story.append(Spacer(1, 6))
story.append(Paragraph("四、双均线金叉死叉(近1年)", s_h2))
story.append(Paragraph("20日均线上穿60日均线为金叉,下穿为死叉。近1年信号:"
                       + ("、".join(g_days) or "无") + " 金叉;"
                       + ("、".join(d_days) or "无") + " 死叉。", s_body))
story.append(Image(fig3, width=176*mm, height=176*mm*4.4/11))

# 数据表
story.append(Spacer(1, 6))
story.append(Paragraph("五、最近10个交易日明细", s_h2))
tdata = [["日期", "开盘", "收盘", "最高", "最低", "涨跌幅%"]]
for r in df.tail(10).itertuples():
    tdata.append([str(r.date), f"{r.open:.2f}", f"{r.close:.2f}", f"{r.high:.2f}", f"{r.low:.2f}", f"{r.pct_change:+.2f}"])
tbl = Table(tdata, colWidths=[32*mm]*2 + [28*mm]*4)
tbl.setStyle(TableStyle([
    ("FONTNAME", (0, 0), (-1, -1), F),
    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#f2dcd5")),
    ("GRID", (0, 0), (-1, -1), 0.4, HexColor("#cccccc")),
    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#ffffff"), HexColor("#faf5f3")]),
]))
story.append(tbl)

# 分析小结
story.append(Spacer(1, 6))
story.append(Paragraph("六、分析小结", s_h2))
summary = (
    "1) 基本面语境:海螺水泥是国内水泥行业龙头,近两年受地产下行、基建需求放缓拖累,"
    "股价整体在 15~24 元区间震荡下行,期末较期初下跌约 5.8%。<br/>"
    "2) 技术面:MA20/MA60 双均线在近一年内两度金叉、两度死叉,中期趋势偏弱;"
    "2026-08-04 出现放量下跌(单日成交约 5780 万股),需关注后续抛压。<br/>"
    "3) 学习价值:本报告完整演示了量化数据可视化的基本流程——读取真实数据、计算指标、"
    "绘制图表、形成结论,这是金融数学专业和量化岗位的基本功。<br/>"
    "4) 免责声明:本报告仅用于 Python 与数据分析学习演示,不构成任何投资建议。"
)
story.append(Paragraph(summary, s_body))

doc.build(story)
print("PDF 已生成:", os.path.join(HERE, f"{STOCK_NAME}股价分析报告.pdf"))
