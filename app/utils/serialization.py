from datetime import date, datetime

import numpy as np
import pandas as pd


def sanitize_properties(props: dict) -> dict:
    if not isinstance(props, dict):
        return {}
    sanitized = {}
    for k, v in props.items():
        if pd.isna(v):  # Handle NaN, NaT, None
            sanitized[k] = None
        elif isinstance(v, (np.integer, int)):
            sanitized[k] = int(v)
        elif isinstance(v, (np.floating, float)):
            sanitized[k] = float(v)
        elif isinstance(v, (np.bool_, bool)):
            sanitized[k] = bool(v)
        elif isinstance(v, (datetime, date)):
            sanitized[k] = v.isoformat()
        else:
            sanitized[k] = str(v) if v is not None else None
    return sanitized
