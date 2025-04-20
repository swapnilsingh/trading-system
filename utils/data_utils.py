def parse_ohlcv_list(ohlcv_list):
    import json
    import pandas as pd
    import logging

    logger = logging.getLogger("IndicatorService")

    # If the input list is already a list of dictionaries, directly convert it to a DataFrame
    if all(isinstance(entry, dict) for entry in ohlcv_list):
        df = pd.DataFrame(ohlcv_list)
    else:
        # Parse each entry from JSON format if it's a string
        try:
            parsed = [json.loads(entry) for entry in ohlcv_list]
            df = pd.DataFrame(parsed)
        except Exception as e:
            logger.error(f"❌ Error parsing OHLCV data from string: {e}")
            return pd.DataFrame()

    # Check if 'timestamp' column exists
    if 'timestamp' not in df.columns:
        logger.error(f"❌ Missing 'timestamp' column in OHLCV data")
        return pd.DataFrame()

    # Log the first few rows to check the data structure
    logger.info(f"Parsed OHLCV data: {df.head()}")

    return df
