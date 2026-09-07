import pandas as pd 

REQUIRED_COLUMNS = ["case_id",'activity','resource',"timestamp"]

def build_transitions(df: pd.DataFrame) -> pd.DataFrame:
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    
    if missing_columns:
        raise ValueError (f'Отсутствуют обязатеьные колонки: {missing_columns}')
    
    working_df = df.copy()

    working_df ['to_activity'] = working_df.groupby('case_id')['activity'].shift(-1)
    working_df ['to_resource'] = working_df.groupby('case_id')['resource'].shift(-1)
    working_df ['to_timestamp'] = working_df.groupby('case_id')['timestamp'].shift(-1)

    working_df = working_df.rename(
        columns={
            'activity':'from_activity',
            'resource':'from_resource',
            'timestamp':'from_timestamp'
        }
    )

    transitions_df = working_df[working_df['to_activity'].notna()].copy()

    transitions_df['delta_seconds'] =(transitions_df['to_timestamp']-transitions_df['from_timestamp']).dt.total_seconds()

    transitions_df = transitions_df[
        ["case_id",'from_activity','to_activity','from_resource','to_resource','from_timestamp','to_timestamp','delta_seconds']
    ].reset_index(drop=True)

    return transitions_df