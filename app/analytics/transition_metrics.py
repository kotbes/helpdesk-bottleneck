import pandas as pd
import numpy as np

REQUIRED_COLUMNS = ['case_id','from_activity','to_activity','delta_seconds']

def calculate_transition_metrics(df: pd.DataFrame) -> pd.DataFrame:
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]

    if missing_columns:
        raise ValueError (f'Отсутствуют обязательные колонки: {missing_columns}')
    
    working_df = df.copy()

    working_df['delta_days'] = working_df['delta_seconds'] / 86400 
    
    total_cases = working_df['case_id'].nunique()


    metrics_df =(
        working_df.groupby(['from_activity', 'to_activity'])
        .agg(
        transition_count=('delta_days','count'),
        affected_cases = ('case_id','nunique'),
        
        avg_delay_days=('delta_days','mean'),
        median_delay_days=('delta_days','median'),
        min_delay_days=('delta_days','min'),
        max_delay_days=('delta_days','max'),
        
        q25_delay_days=('delta_days', lambda x: x.quantile(0.25)),
        q75_delay_days=('delta_days', lambda x: x.quantile(0.75)),
        q90_delay_days=('delta_days', lambda x: x.quantile(0.90))
        ).reset_index()
        )
    
    metrics_df['case_share'] =  (metrics_df['affected_cases']/total_cases)

    metrics_df['iqr_delay_days'] = (metrics_df['q75_delay_days']-metrics_df['q25_delay_days'])
    metrics_df = metrics_df.sort_values(
        by='median_delay_days',
        ascending=False
    ).reset_index(drop=True)

    return metrics_df
