import pandas as pd

REQUIRED_COLUMNS = ['from_activity','to_activity',
                    'median_delay_days', 'is_operational_bottleneck_candidate']

def get_operational_bottleneck_candidates(
        classified_metrics_df: pd.DataFrame,
        min_transition_count: int = 5
)-> pd.DataFrame:
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in classified_metrics_df.columns]

    if missing_columns:
        raise ValueError(f'Отсустствуют обязательные колонки:{missing_columns}')
    
    candidates_df = classified_metrics_df.copy()

    candidates_df = candidates_df[
        candidates_df['is_operational_bottleneck_candidate']
    ].copy()

    candidates_df = candidates_df[
        candidates_df['transition_count'] >= min_transition_count
    ].copy()

    candidates_df = candidates_df.sort_values(
        by=['median_delay_days','transition_count'],
        ascending=[False, False]
    ).reset_index(drop=True)

    return candidates_df

