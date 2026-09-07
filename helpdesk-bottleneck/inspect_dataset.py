from app.ingestion.loader import load_event_log
from app.ingestion.normalizer import normalize_event_log
from app.ingestion.validator import validate_event_log
from app.analytics.transition_bilder import build_transitions
from app.analytics.transition_metrics import calculate_transition_metrics
from app.analytics.transition_classifier import add_transition_categories
from app.analytics.bottleneck_candidates import get_operational_bottleneck_candidates
from app.analytics.bottleneck_score import add_bottleneck_score
from app.analytics.path_metrics import calculate_path_metrics
from app.analytics.candidate_analysis import analyze_bottleneck_candidate

df = load_event_log("data/raw/helpdesk.zip")
normalized_df = normalize_event_log(df)
transitions_df = build_transitions(normalized_df)
metrics_df = calculate_transition_metrics(transitions_df)
classified_metrics_df = add_transition_categories(metrics_df)
operational_candidates_df = get_operational_bottleneck_candidates(
    classified_metrics_df,
    min_transition_count=10
)
score_df = add_bottleneck_score(operational_candidates_df)
print("\nРазмер score_df:", score_df.shape)
print("Колонки score_df:", score_df.columns.to_list())

print(
    score_df[
        [
            "from_activity",
            "to_activity",
            "transition_count",
            "affected_cases",
            "case_share",
            "median_delay_days",
            "q75_delay_days",
            "q90_delay_days",
            "bottleneck_score",
        ]
    ].head(20)
)




candidate_report = analyze_bottleneck_candidate(
    scored_df=score_df,
    transition_df=transitions_df,
    from_activity="Resolve ticket",
    to_activity="Closed",
)

print("\nКандидат:")
print(candidate_report["candidate"])

print("\nПроверка финальной позиции:")
print(candidate_report["final_check"])

print("\nПроверка длинного хвоста:")
print(candidate_report["tail_check"])

print("\nПредложенная метка:")
print(candidate_report["label_result"])

print("\nЧто чаще всего было перед этим переходом:")
print(candidate_report["previous_transitions"].head(10))

print("\nЧто чаще всего было после этого перехода:")
print(candidate_report["next_transitions"].head(10))

print("\nПримеры кейсов:")
print(candidate_report["sample_cases"])

path_metrics_df = calculate_path_metrics(normalized_df)
report = validate_event_log(normalized_df)

print("\nОтчет валидации:")
print(report)
