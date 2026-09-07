import pandas as pd
import numpy as np

def calculate_path_metrics(normalized_df: pd.DataFrame) -> pd.DataFrame:
    
    REQUIRED_COLUMNS = ["case_id",'activity',"timestamp"]

    missing_columns =[col for col in REQUIRED_COLUMNS if col not in normalized_df.columns]
        
    if missing_columns:
        raise ValueError(f"Отсутствуют обязательные колонки: {missing_columns}")
    
    working_df = normalized_df.copy()

    working_df = working_df.sort_values(
        by=['case_id','timestamp']
    ).reset_index(drop=True)

    case_path_df = (
        working_df.groupby('case_id')['activity']
        .agg(lambda activities:" -> ".join(activities.astype(str)))
        .reset_index(name='variant_path')
    )

    case_duration_df = (
        working_df.groupby('case_id')
        .agg(
            start_time = ('timestamp','min'),
            end_time = ('timestamp','max'),
            event_count = ('activity','count'),
            unique_activity_count = ('activity','nunique')
        )
        .reset_index()
    )


    case_level_df = case_path_df.merge(
        case_duration_df,
        on='case_id',
        how='inner'
    )

    case_level_df["case_duration_seconds"] = (
    case_level_df["end_time"] - case_level_df["start_time"]
    ).dt.total_seconds()

    case_level_df["case_duration_days"] = (
        case_level_df["case_duration_seconds"] / 86400
    )

    total_cases = case_level_df['case_id'].nunique()

    path_metrics_df = (
        case_level_df.groupby('variant_path')
        .agg(
        case_count = ('case_id','nunique'),
        avg_case_duration_days = ('case_duration_days','mean'),
        median_case_duration_days = ('case_duration_days','median'),
        max_duration_days = ('case_duration_days','max'),
        avg_event_count =('event_count','mean'),
        median_event_count=('event_count','median')
        ).reset_index()
    )
    path_metrics_df['case_share'] = (
        path_metrics_df['case_count']/total_cases
    )

    path_metrics_df['path_impact_score']=(
        path_metrics_df['median_case_duration_days']*np.log1p(path_metrics_df['case_count'])
    )

    path_metrics_df = path_metrics_df.sort_values(
        by='path_impact_score',
        ascending=False
    ).reset_index(drop=True)

    return path_metrics_df