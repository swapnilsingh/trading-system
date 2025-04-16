def parse_ohlcv_list(ohlcv_list):
    import json
    import pandas as pd
    return pd.DataFrame([json.loads(entry) for entry in ohlcv_list])
