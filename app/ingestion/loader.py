from pathlib import Path
from zipfile import ZipFile

import pandas as pd

def load_event_log(file_path: str|Path) -> pd.DataFrame:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError (f'Файл не найден: {path}')
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    elif suffix == ".zip":
        with ZipFile(path) as archive:          
            file_names = archive.namelist()
            for name in file_names:
                if name.endswith('.csv'):
                    with archive.open(name) as file:
                        return pd.read_csv(file)     
        raise ValueError(f"В архиве {path.name} не найдено CSV-файлов")
    else:
        raise ValueError (f'Не поддержеваемый тип файла:{suffix}')               