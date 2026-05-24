from typing import List
import pandas as pd
from core.types import KLineRaw, parse_date


def df_to_raw(df: pd.DataFrame) -> List[KLineRaw]:
    result: List[KLineRaw] = []
    for i in range(len(df)):
        row = df.iloc[i]
        raw = KLineRaw(
            index=i,
            date=parse_date(str(row["date"])),
            h=float(row["high"]),
            l=float(row["low"]),
            o=float(row["open"]),
            c=float(row["close"]),
            v=float(row.get("volume", 0.0)),
        )
        result.append(raw)
    return result
