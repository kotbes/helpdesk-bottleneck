import pandas as pd

def normalize_event_log(df: pd.DataFrame) -> pd.DataFrame:
    COLUMN_MAPPING = {'Case ID':"case_id",
    'Activity':'activity',
    'Resource':'resource',
    'Complete Timestamp':"timestamp"}
    
    missing_columns =[col for col in COLUMN_MAPPING.keys() if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Отсутствуют обязательные колонки: {missing_columns}")
    
    normalized_df = df.rename(columns=COLUMN_MAPPING)[list(COLUMN_MAPPING.values())].copy()

    normalized_df["timestamp"] = pd.to_datetime(
        normalized_df['timestamp'],
        errors='coerce'
    )

    normalized_df = normalized_df.sort_values(by=['case_id','timestamp']).reset_index(drop=True)

    return normalized_df

