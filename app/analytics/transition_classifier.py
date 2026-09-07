import pandas as pd

def add_transition_categories(metrics_df: pd.DataFrame) -> pd.DataFrame:
    required_columns = ['from_activity','to_activity']
    missing_columns = [col for col in required_columns if col not in metrics_df.columns]

    if missing_columns:
        raise ValueError(f'Отсустствуют обязательные колонки:{missing_columns}')

    classified_df = metrics_df.copy()

    classified_df['transition_category'] = 'bottleneck_candidate'

    classified_df['is_operational_bottleneck_candidate']= True

    return classified_df