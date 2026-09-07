import pandas as pd

REQUIRED_TRANSITION_COLUMNS = ['case_id','from_activity','to_activity','delta_seconds','from_timestamp','to_timestamp']

REQUIRED_SCORE_COLUMNS = [
        'from_activity',
        'to_activity',
        'transition_count',
        'affected_cases' ,
        'case_share',
        'median_delay_days',
        'q75_delay_days',
        'q90_delay_days',
        'bottleneck_score'
]

def _transition_context(transition_df: pd.DataFrame) -> pd.DataFrame:

    missing_columns = [col for col in REQUIRED_TRANSITION_COLUMNS if col not in transition_df.columns]

    if missing_columns:
        raise ValueError(f'Отсутствуют обязательные колонки: {missing_columns}')
    
    context_df = transition_df.copy()

    context_df = context_df.sort_values(
        by= ['case_id','from_timestamp']
        ).reset_index(drop=True)

    context_df['delta_days'] = context_df['delta_seconds']/86400
    # отделить именно "переходы" в контексте одельного кейса для удобного наблюдения патернов относительно переходов до и после них
    context_df['transition_name'] = (context_df['from_activity'] + '->' + context_df['to_activity'])

    context_df['previous_transition_name'] = context_df.groupby('case_id')['transition_name'].shift(1)
    context_df['next_transition_name'] = context_df.groupby('case_id')['transition_name'].shift(-1)

    return context_df

def _get_candidate_metrics(
        scored_df: pd.DataFrame,
        from_activity: str,
        to_activity: str
) -> dict:
    missing_columns = [col for col in REQUIRED_SCORE_COLUMNS if col not in scored_df.columns]

    if missing_columns:
        raise ValueError(f'Отсутствуют обязательные колонки: {missing_columns}')
    
    candidate_row = scored_df[
        (scored_df['from_activity'] == from_activity) &
        (scored_df['to_activity'] == to_activity)
    ]

    if candidate_row.empty:
        raise ValueError(f'Переход {from_activity} -> {to_activity} не найден в scored_df')

    candidate_metrics = candidate_row.iloc[0].to_dict()

    return candidate_metrics

def _get_candidates_rows(
        context_df: pd.DataFrame,
        to_activity: str,
        from_activity: str
    )->pd.DataFrame:
    
    candidates_rows_df = context_df[
        (context_df['to_activity'] == to_activity) &
        (context_df['from_activity'] == from_activity)
    ].copy()

    if candidates_rows_df.empty:
        raise ValueError(f'Переход {from_activity} -> {to_activity} не найден в context_df')

    return candidates_rows_df
#Наглядные примеры в отчете до и после с колличсевтом и частотой
def _build_transition_frequency(candidates_rows_df: pd.DataFrame, column_name: str, result_column_name: str) -> pd.DataFrame:

    freq_df = candidates_rows_df[column_name].value_counts(dropna=False).reset_index()

    freq_df.columns = [result_column_name, 'count']

    freq_df['share'] = freq_df['count'] / len(candidates_rows_df)

    return freq_df
#Наглядные примеры 
def _sample_cases(
        candidates_rows_df: pd.DataFrame,
        sample_size: int
)->pd.DataFrame:

    sampled_df = candidates_rows_df[
        [
            'case_id',
            'from_timestamp',
            'to_timestamp',
            'from_activity',
            'to_activity',
            'delta_days',
            'previous_transition_name',
            'next_transition_name'
        ]
    ].head(sample_size)
    
    return sampled_df
#Проверка на формальное закрытие
def _checking_final_position(
        candidates_rows_df: pd.DataFrame,
        context_df: pd.DataFrame,
        to_activity: str
)->dict:
    candidate_transition_count = len(candidates_rows_df)

    last_transition_count = int(
        candidates_rows_df['next_transition_name'].isna().sum()
    )
    
    last_transition_share = float(
        candidates_rows_df['next_transition_name'].isna().mean()
    )

    last_transition_per_case = (context_df.groupby('case_id').tail(1))

    final_share = float((last_transition_per_case['to_activity']==to_activity).mean())

    return {
        'candidate_transition_count': int(candidate_transition_count),
        'last_transition_share': last_transition_share,
        'last_transition_count': last_transition_count,
        'final_share': final_share
    }

def _analyze_long_tail(candidate_metrics: dict,) -> dict:
    
    median = candidate_metrics['median_delay_days']
    q75 = candidate_metrics['q75_delay_days']
    q90 = candidate_metrics['q90_delay_days']

    if median <=0:
        return {
            'has_long_tail': False,
            'q75_median_ratio': None,
            'q90_median_ratio': None,
            'comment': 'Медианная задержка не положительная, анализ длинного хвоста не применим'
        }
    q75_median_ratio = q75 / median
    q90_median_ratio = q90 / median

    has_long_tail = q90_median_ratio >= 3

    if has_long_tail:
        comment = 'Переход имеет длинный хвост задержек, что может указывать на наличие редких, но очень длительных случаев'
    else:
        comment = 'Переход не имеет выраженного длинного хвоста задержек'

    return {
        'has_long_tail': has_long_tail,
        'q75_median_ratio': float(q75_median_ratio),
        'q90_median_ratio': float(q90_median_ratio),
        'comment':comment
    }

def _add_candidate_label(
        final_check: dict,
        tail_check: dict
    ) -> dict:
    last_transition_share = final_check['last_transition_share']
    final_share = final_check['final_share']

    has_long_tail = tail_check['has_long_tail']

    reason = []
    risk_flag = []

    if has_long_tail:
        risk_flag.append('long_tail_risk')
        reason.append(tail_check['comment'])

    is_final_position = (
        last_transition_share >= 0.9 and final_share >= 0.9
    )    

    is_stable_delay = not has_long_tail

    if is_final_position and is_stable_delay:
        label = 'formal_closure_candidate'
        confidence = 'high'
        recommended_action = 'Исключить из анализа'

        reason.append(
            'Переход часто является последним переходом кейса'
        )
        reason.append(
            'Конечная активность перехода часто является финальной активностью кейса'
        )
        reason.append(
            'Задержка не имеет выраженного длинного хвоста'
        )
        reason.append(
            "Высокий bottleneck_score может быть связан с формальным ожиданием "
            "после фактического решения, а не с ограничением системы" 
        )
    elif is_final_position and has_long_tail:
        
        label = "bottleneck_candidate"
        confidence = "medium"
        recommended_action = "manual_review_required"

        reason.append(
            "Переход часто находится в финальной позиции"
        )
        reason.append(
            "Но у перехода есть длинный хвост задержек"
        )
        reason.append(
            "Такой переход нельзя автоматически исключить как простое формальное закрытие"
        )
    else:
        label = "bottleneck_candidate"
        confidence = "low"
        recommended_action = "manual_review_required"

        reason.append(
            "Переход не выглядит как финальное формальное закрытие"
        )
        reason.append(
            "Для подтверждения ограничения нужен ручной анализ контекста: "
            "что было до перехода, что было после него и какой бизнес-смысл у активности"
        )

    return {
        "label": label,
        "confidence": confidence,
        "recommended_action": recommended_action,
        "risk_flags": risk_flag,
        "reasons": reason,
    }

def analyze_bottleneck_candidate(
        scored_df: pd.DataFrame,
        transition_df: pd.DataFrame,
        from_activity: str,
        to_activity: str,
        sample_size: int = 10
) -> dict:
    
    #1) нужен контекст какие до, какие после появляются переходы для наглядности
    contex_df = _transition_context(transition_df)
    
    #2) теперь нужно дать метку выбранному переходу, для этого небоходимо: проверить его метрики и нахождение в терминальной позиции, а также наличие длинного хвоста
    candidate_metrics = _get_candidate_metrics(
        scored_df=scored_df,
        from_activity=from_activity,
        to_activity=to_activity
    )
    # 3. Берем все реальные строки выбранного перехода из context_df.
    candidates_rows_df = _get_candidates_rows(
        context_df=contex_df,
        from_activity=from_activity,
        to_activity=to_activity,        
    )
    # 4. Проверка является ли переход финальным
    final_check = _checking_final_position(
        candidates_rows_df=candidates_rows_df,
        context_df=contex_df,
        to_activity=to_activity
    )

    # 5. Проверка длинного хвоста
     
    tail_check = _analyze_long_tail(candidate_metrics=candidate_metrics)

    # 6. переходы до: колличество и частота
    previous_transition = _build_transition_frequency(
        candidates_rows_df=candidates_rows_df,
        column_name='previous_transition_name',
        result_column_name='previous_transition_name'
    )
    # 7. переходы после: колличество и частота
    next_transition = _build_transition_frequency(
        candidates_rows_df=candidates_rows_df,
        column_name='next_transition_name',
        result_column_name='next_transition_name'
    )
    # 8. Вывести примеры
    sample_cases = _sample_cases(
        candidates_rows_df=candidates_rows_df,
        sample_size=sample_size
    )

    # 9. Предложение метки

    label_result = _add_candidate_label( 
        final_check=final_check,
        tail_check=tail_check
    )

    return {
        "candidate": {
            "from_activity": from_activity,
            "to_activity": to_activity,
        },
        "final_check": final_check,
        "tail_check": tail_check,
        "label_result": label_result,
        "previous_transitions": previous_transition,
        "next_transitions": next_transition,
        "sample_cases": sample_cases,
    }

