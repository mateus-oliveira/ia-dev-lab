"""Contrato das features agregadas por lote de eventos.

Define a ordem canônica das colunas que o worker/ETL produz
(`player_modeling.worker.features.extract_features`), que são persistidas em
`player_features` e que os classificadores de `player_modeling.ml` consomem.
A ordem importa: é ela que o treino e a inferência precisam reproduzir.
"""

FEATURE_COLUMNS: tuple[str, ...] = (
    "n_events",
    "pct_attack",
    "pct_explore",
    "pct_social",
    "pct_quest_complete",
    "pct_retry",
    "avg_decision_time_ms",
    "fail_rate",
)

LABEL_COLUMN = "true_persona"
