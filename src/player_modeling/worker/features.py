"""Agregação de eventos brutos em features por lote (worker/ETL).

Compartilhado entre o worker subscriber (`player_modeling.worker.subscriber`)
e o script de geração do dataset offline
(`player_modeling.scripts.generate_raw_events`), para que a lógica de
agregação não seja duplicada entre os dois usos.
"""

from typing import Any

from player_modeling.simulator.events import EVENT_TYPES


def extract_features(
    session_id: str, player_id: str, events: list[dict[str, Any]]
) -> dict[str, Any]:
    """Agrega uma lista de eventos brutos em uma linha de features por lote.

    Não recebe nem retorna persona/`true_persona`: esse rótulo não existe
    nas mensagens reais consumidas da fila, apenas no dataset de treino
    gerado offline (`generate_raw_events.py`), que adiciona esse campo por
    fora do resultado desta função.

    :param session_id: identificador da sessão/lote ao qual os eventos pertencem.
    :param player_id: identificador do jogador dono dos eventos.
    :param events: lista de eventos brutos no formato de `src/data/events.csv`.

    :return: dicionário com `session_id`, `player_id`, `n_events` e as
        features agregadas (`pct_attack`, `pct_explore`, `pct_social`,
        `pct_quest_complete`, `pct_retry`, `avg_decision_time_ms`,
        `fail_rate`), no mesmo formato de `src/data/sessions_features.csv`
        (sem a coluna `true_persona`).
    """
    n = len(events)
    counts = {et: 0 for et in EVENT_TYPES}
    total_decision_time = 0
    fails = 0
    for ev in events:
        counts[ev["event_type"]] += 1
        total_decision_time += ev["decision_time_ms"]
        if ev["outcome"] == "fail":
            fails += 1

    return {
        "session_id": session_id,
        "player_id": player_id,
        "n_events": n,
        "pct_attack": round(counts["attack"] / n, 3),
        "pct_explore": round(counts["explore_area"] / n, 3),
        "pct_social": round((counts["chat"] + counts["trade"]) / n, 3),
        "pct_quest_complete": round(counts["quest_complete"] / n, 3),
        "pct_retry": round(counts["retry"] / n, 3),
        "avg_decision_time_ms": round(total_decision_time / n, 1),
        "fail_rate": round(fails / n, 3),
    }
