"""
generate_fake_dataset.py

Gera uma base de dados sintetica de eventos de jogadores para pre-treinar
o classificador de perfil comportamental (taxonomia de Bartle) do projeto
BehaviorLens, sem depender do pipeline real (simulador -> RabbitMQ -> worker)
estar pronto.

A persona usada para gerar cada jogador funciona como rotulo verdadeiro
(ground truth), permitindo treinar um classificador supervisionado mesmo
sem nenhum dataset real rotulado disponivel.

Saidas (em --outdir, padrao "./src/data"):
    events.csv             -> eventos brutos, no formato que o Worker/ETL
                               consumiria da fila (sem o rotulo de persona)
    sessions_features.csv  -> features agregadas por sessao + rotulo
                               (true_persona), prontas para treinar o modelo

Uso:
    python generate_fake_dataset.py --players 200 --seed 42
    python generate_fake_dataset.py --players 200 --sanity-check
"""

import argparse
import csv
import os
import random
import uuid
from datetime import datetime, timedelta
from typing import Any

from player_modeling.simulator.events import (
    EVENT_TYPES,
    PERSONA_PROFILES,
    PERSONAS,
    generate_events,
    session_weights,
)
from player_modeling.worker.features import extract_features as _extract_features

__all__ = ["PERSONAS", "EVENT_TYPES", "PERSONA_PROFILES", "session_weights"]


def generate_session(
    persona: str, player_id: str, session_index: int, min_events: int, max_events: int
) -> tuple[str, list[dict[str, Any]]]:
    """Gera os eventos brutos de uma sessao de jogo para um jogador/persona."""
    profile = PERSONA_PROFILES[persona]
    weights_dict = session_weights(persona)

    n_events = random.randint(min_events, max_events)
    session_id = str(uuid.uuid4())
    t = datetime(2026, 9, 1) + timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))

    events = generate_events(
        weights_dict, profile["decision_time_ms"], session_id, player_id, n_events, t
    )
    return session_id, events


def extract_features(
    session_id: str, player_id: str, persona: str, events: list[dict[str, Any]]
) -> dict[str, Any]:
    """Agrega eventos em features e adiciona o rótulo de treino `true_persona`.

    Reaproveita `player_modeling.worker.features.extract_features` (a
    versão real, usada pelo worker subscriber, que não conhece persona) e
    acrescenta `true_persona` por fora, apenas para compor o dataset de
    treino `sessions_features.csv`.
    """
    features = _extract_features(session_id, player_id, events)
    features["true_persona"] = persona
    return features


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gera dataset sintetico de jogadores para o BehaviorLens"
    )
    parser.add_argument("--players", type=int, default=200, help="numero de jogadores sinteticos")
    parser.add_argument("--min-events", type=int, default=20, help="minimo de eventos por sessao")
    parser.add_argument("--max-events", type=int, default=80, help="maximo de eventos por sessao")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--outdir", default="src/data")
    parser.add_argument(
        "--sanity-check",
        action="store_true",
        help="treina um classificador rapido para validar que o dataset e separavel",
    )
    args = parser.parse_args()

    random.seed(args.seed)
    os.makedirs(args.outdir, exist_ok=True)

    all_events = []
    all_features = []
    persona_counts = {p: 0 for p in PERSONAS}

    for i in range(args.players):
        persona = random.choice(PERSONAS)
        persona_counts[persona] += 1
        player_id = f"player_{i:04d}"
        session_id, events = generate_session(
            persona, player_id, i, args.min_events, args.max_events
        )
        all_events.extend(events)
        all_features.append(extract_features(session_id, player_id, persona, events))

    events_path = os.path.join(args.outdir, "events.csv")
    features_path = os.path.join(args.outdir, "sessions_features.csv")

    with open(events_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_events[0].keys()))
        writer.writeheader()
        writer.writerows(all_events)

    with open(features_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_features[0].keys()))
        writer.writeheader()
        writer.writerows(all_features)

    print(f"Jogadores gerados: {args.players}")
    print(f"Distribuicao por persona: {persona_counts}")
    print(f"Eventos brutos:        {events_path}  ({len(all_events)} linhas)")
    print(f"Features por sessao:   {features_path}  ({len(all_features)} linhas)")

    if args.sanity_check:
        run_sanity_check(features_path)


def run_sanity_check(features_path: str) -> None:
    """Treina um RandomForest rapido so para confirmar que o dataset tem
    sinal suficiente para separar as personas (nao e o modelo final)."""
    try:
        import pandas as pd
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.metrics import classification_report
        from sklearn.model_selection import train_test_split
    except ImportError:
        print("\n[sanity-check pulado] instale as dependencias com:")
        print("  pip install pandas scikit-learn --break-system-packages")
        return

    df = pd.read_csv(features_path)
    feature_cols = [
        "pct_attack",
        "pct_explore",
        "pct_social",
        "pct_quest_complete",
        "pct_retry",
        "avg_decision_time_ms",
        "fail_rate",
    ]
    X = df[feature_cols]
    y = df["true_persona"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    clf = RandomForestClassifier(n_estimators=200, random_state=42)
    clf.fit(X_train, y_train)
    preds = clf.predict(X_test)

    print("\n=== sanity check (RandomForest, so para validar o dataset) ===")
    print(classification_report(y_test, preds))


if __name__ == "__main__":
    main()
