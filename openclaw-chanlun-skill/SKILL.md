---
name: chanlun
display_name: 缠论技术分析
description: |
  缠论技术分析技能。当用户要求用缠论分析股票K线时激活。
  支持A股、港股、美股和主流加密货币的日线/周线/分钟线分析。
trigger:
  - "缠论"
  - "缠论分析"
  - "用缠论"
  - "缠论看"
  - "缠论视角"
  - "背驰" and "笔"
  - "中枢" and "笔"
  - "买卖点" and "缠论"
  - "1买" or "2买" or "3买" and "缠论"
  - "分型" and "笔" and "分析"
---

# 缠论技术分析 Skill

## 核心职责

接收一只股票的K线数据（DataFrame OHLCV），返回缠论结构化分析结果。

## 输入格式

技能接受以下参数：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| symbol | string | 是 | 股票代码，如 `000001` `BTCUSDT` `AAPL` |
| market | string | 否 | 市场：`A`（A股akshare）、`HK`（港股yfinance）、`US`（美股/加密，Binance） |
| period | string | 否 | K线周期：`1m` `5m` `15m` `30m` `60m` `day` `week` |
| start_date | string | 否 | 开始日期 YYYYMMDD |
| end_date | string | 否 | 结束日期 YYYYMMDD，默认当前 |

## 输出 schema

技能返回以下结构（Python dict，JSON 序列化后打印）：

```python
{
  "klines_count": int,        # 原始K线条数
  "cl_klines_count": int,      # 包含处理后K线条数
  "fractals": [               # 分型列表
    {
      "type": "ding" | "di",  # 顶分型/底分型
      "date": str,             # 分型日期
      "val": float,            # 分型值（价格）
      "real": bool,            # 是否有效分型
    }
  ],
  "strokes": [               # 笔（Bi）列表
    {
      "index": int,
      "type": "up" | "down",  # 笔方向
      "start_date": str,
      "end_date": str,
      "high": float,
      "low": float,
      "done": bool,
      "td": bool,             # 是否突破/td信号
      "qs_beichi": bool,       # 趋势背驰（价格新低但MACD未新低）
      "pz_beichi": bool,       # 盘整背驰
      "mmds": list[str],        # 买卖点信号如 ["2buy","l2buy","1buy"]
      "mm_score": float,        # 缠论买卖点综合评分 0-100
    }
  ],
  "zhongshus": [             # 中枢列表
    {
      "index": int,
      "zg": float,           # 中枢上界
      "zd": float,            # 中枢下界
      "gg": float,            # 向上离开段高点
      "dd": float,            # 向下离开段低点
      "stroke_indices": list[int],
    }
  ],
  "current_trend": "上涨" | "下跌",
  "summary": {
    "divergence_count": int,    # 背驰次数
    "buy_signals": int,        # 买入信号总数
    "sell_signals": int,        # 卖出信号总数
    "signal_strength": "strong" | "medium" | "weak",
  }
}
```

## 工作流程

### Step 1: 获取K线数据

根据 `market` 参数选择数据源：

```
market = "A"   → akshare.stock_zh_a_hist(symbol, period, start_date, end_date)
market = "HK"  → yfinance.download(symbol, period, start_date[:4])
market = "US"   → 如果 symbol 是主流币种（BTC/ETH/SOL 等）用 Binance klines API
                → 否则用 yfinance.download(symbol, ...)
```

数据列名统一映射为：`date open high low close volume`

### Step 2: 运行 ChanLunEngine

```python
from chanlun_engine import ChanLunEngine
engine = ChanLunEngine(df)
result = engine.analyze()
```

### Step 3: 运行测试验证

```bash
cd openclaw-chanlun-skill/scripts
python3 -m pytest test/ -v
```

### Step 4: 格式化输出

将 `result` dict 序列化为 JSON 打印。

### Step 4: 解读报告

根据输出提供文字解读：
- 笔方向与中枢位置
- 背驰出现的位置与含义
- 买卖点信号的市场含义
- 当前趋势判断

## 缠论概念速查

| 概念 | 缠论定义 |
|------|---------|
| 顶/底分型 | 三根K线形成的独立极值结构 |
| 笔（Bi） | 分型间连接单元，需本级别笔破坏前一级别笔 |
| 中枢 | 三段重叠区间，趋势的锚点 |
| 趋势背驰 | 价格新低但 MACD histogram 面积未新低，动能衰竭信号 |
| 盘整背驰 | 价格新高/新低但 MACD 柱未跟随 |
| 2买/3买 | 笔内部回调位置的结构性买入点 |
| 1买 | 趋势反转第一买点（左尾抄底） |
| l2买 | 次级回调不破前低 |

## 数据源能力矩阵

| 市场 | 数据源 | 成功率 |
|------|--------|-------|
| A股 | akshare | 极高 |
| 港股 | yfinance | 高 |
| 美股 | yfinance | 高 |
| 主流加密 | Binance klines | 极高 |
| 山寨币 | Binance klines | 取决于是否在Binance上架 |

## 错误处理

| 错误类型 | 处理方式 |
|---------|---------|
| 数据获取失败 | 打印 `{"error": "fetch failed: <原因>"}` |
| 分析崩溃 | 打印 `{"error": "analysis failed: <原因>"}` |
| 无数据 | 打印 `{"error": "no data for <symbol>"}` |
| 股票代码无效 | 打印 `{"error": "invalid symbol"}` |

## 示例对话

**用户**: 帮我用缠论分析平安银行的日线
**Skill 行为**: 获取 `000001` 日线数据 → ChanLunEngine.analyze() → 格式化输出并解读

**用户**: BTC 4H 出现背驰了吗
**Skill 行为**: 获取 BTC/USDT 4H 数据 → 检查 strokes 中 qs_beichi/pz_beichi 字段 → 报告背驰笔位置与含义

**用户**: 最近有哪些股票出现1买信号
**Skill 行为**: 批量扫描多只股票 → 筛选 mmds 含 "1buy" 的笔 → 报告标的与时间
