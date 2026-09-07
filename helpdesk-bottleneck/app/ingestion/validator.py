import pandas as pd

REQUIRED_COLUMNS = ['case_id','activity','resource','timestamp']

def validate_event_log(df: pd.DataFrame) -> dict:
    errors = []
    warning = []
    stats = {}
    
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_columns:
        return{
            "is_valid": False,
            "errors": [f'Отсутствуют обязательные колонки:{missing_columns}'],
            "warning": [],
            "stats":{}
        }
    
    empty_case_id = int(df['case_id'].isna().sum())
    empty_activity = int(df['activity'].isna().sum())
    empty_timestamp = int(df['timestamp'].isna().sum())
    empty_resource = int(df['resource'].isna().sum())


    stats["row_count"] = int(len(df))
    stats["column_count"] = int(len(df.columns))
    stats["case_count"] = int(df["case_id"].nunique())
    stats["empty_case_id"] = empty_case_id
    stats["empty_activity"] = empty_activity
    stats["empty_timestamp"] = empty_timestamp

    if empty_case_id > 0:
        errors.append(f"Пустых case_id: {empty_case_id}")

    if empty_activity > 0:
        errors.append(f"Пустых activity: {empty_activity}")

    if empty_timestamp > 0:
        errors.append(f"Пустых или битых timestamp: {empty_timestamp}")

    if empty_resource > 0:
        errors.append(f"Пустых resource: {empty_resource}")
    
    duplicate_rows = int(df.duplicated(subset=["case_id", "activity", "resource", "timestamp"]).sum())

    stats["duplicate_rows"] = duplicate_rows

    if duplicate_rows > 0:
        warning.append(f"Найдено дубликатов событий: {duplicate_rows}")        

        return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warning,
        "stats": stats
    }