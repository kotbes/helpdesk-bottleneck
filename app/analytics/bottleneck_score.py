import numpy as np
import pandas as pd

REQUIRED_COLUMNS = ['transition_count','median_delay_days']

def add_bottleneck_score(candidates_df:pd.DataFrame) -> pd.DataFrame:
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in candidates_df.columns]

    if missing_columns:
        raise ValueError(f'Отсустствуют обязательные колонки:{missing_columns}')
    
    scored_df = candidates_df.copy()

    scored_df['transition_count_log']= np.log1p(scored_df['transition_count'])

    scored_df['bottleneck_score']=(
        scored_df['median_delay_days']*scored_df['transition_count_log']
    )

    scored_df = scored_df.sort_values(
        by='bottleneck_score',
        ascending=False
    ).reset_index(drop=True)

    return scored_df
