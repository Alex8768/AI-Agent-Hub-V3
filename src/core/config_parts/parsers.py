from __future__ import annotations

from typing import List, Union
import json


def parse_json_or_csv_list(v: Union[str, List[str]]) -> List[str]:
    """Parse list from JSON array string or comma-separated string.

    - If v is already a list: return as-is
    - If v is a string like '["a","b"]': parse JSON
    - Else treat as 'a,b' csv
    """
    if isinstance(v, str):
        s = v.strip()
        if s.startswith("[") and s.endswith("]"):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return [str(x) for x in parsed if str(x).strip()]
            except json.JSONDecodeError:
                pass
        return [item.strip() for item in s.split(",") if item.strip()]
    return v
