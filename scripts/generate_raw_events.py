"""
generate_fake_dataset.py

Gera uma base de dados sintetica de eventos de jogadores para pre-treinar
o classificador de perfil comportamental (taxonomia de Bartle) do projeto
BehaviorLens, sem depender do pipeline real (simulador -> RabbitMQ -> worker)
estar pronto.

A persona usada para gerar cada jogador funciona como rotulo verdadeiro
(ground truth), permitindo treinar um classificador supervisionado mesmo
sem nenhum dataset real rotulado disponivel.

Saidas (em --outdir, padrao "./data"):
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

PERSONAS = ["Achiever", "Explorer", "Socializer", "Killer"]

EVENT_TYPES = [
    "move",
    "attack",
    "explore_area",
    "chat",
    "quest_complete",
    "quest_fail",
    "retry",
    "trade",
    "loot",
    "idle",
]

# Cada persona tem uma distribuicao de probabilidade sobre os tipos de
# evento e uma faixa de tempo de decisao (ms) diferente. Isso cria sinal
# suficiente para o classificador aprender, com alguma sobreposicao
# proposital entre personas para ficar realista (nao 100% separavel).
PERSONA_PROFILES = {
    "Achiever": {
        "event_weights": {
            "quest_complete": 0.30,
            "loot": 0.20,
            "move": 0.15,
            "attack": 0.10,
            "retry": 0.10,
            "explore_area": 0.05,
            "chat": 0.03,
            "trade": 0.03,
            "quest_fail": 0.03,
            "idle": 0.01,
        },
        "decision_time_ms": (400, 1100),
    },
    "Explorer": {
        "event_weights": {
            "explore_area": 0.35,
            "move": 0.25,
            "loot": 0.10,
            "idle": 0.08,
            "chat": 0.07,
            "quest_complete": 0.06,
            "attack": 0.04,
            "trade": 0.03,
            "retry": 0.01,
            "quest_fail": 0.01,
        },
        "decision_time_ms": (550, 1600),
    },
    "Socializer": {
        "event_weights": {
            "chat": 0.35,
            "trade": 0.20,
            "move": 0.15,
            "quest_complete": 0.10,
            "explore_area": 0.08,
            "idle": 0.05,
            "attack": 0.03,
            "loot": 0.02,
            "retry": 0.01,
            "quest_fail": 0.01,
        },
        "decision_time_ms": (600, 1700),
    },
    "Killer": {
        "event_weights": {
            "attack": 0.45,
            "move": 0.20,
            "loot": 0.12,
            "retry": 0.08,
            "quest_fail": 0.05,
            "explore_area": 0.05,
            "chat": 0.02,
            "quest_complete": 0.01,
            "trade": 0.01,
            "idle": 0.01,
        },
        "decision_time_ms": (200, 800),
    },
}

NOISE_LEVEL = 0.5  # jitter multiplicativo aplicado aos pesos de cada sessao
MIX_PROB = 0.45  # chance de uma sessao misturar uma segunda persona
MIX_RANGE = (0.2, 0.45)  # peso da persona secundaria na mistura


def session_weights(persona):
    """Monta os pesos de evento para uma sessao: parte das sessoes misturam
    uma segunda persona (jogador nao e 100% puro em um arquetipo), e todas
    recebem jitter individual antes de renormalizar."""
    base = dict(PERSONA_PROFILES[persona]["event_weights"])

    if random.random() < MIX_PROB:
        secondary = random.choice([p for p in PERSONAS if p != persona])
        mix_w = random.uniform(*MIX_RANGE)
        other = PERSONA_PROFILES[secondary]["event_weights"]
        base = {et: (1 - mix_w) * base[et] + mix_w * other[et] for et in base}

    jittered = {
        et: max(0.001, w * (1 + random.uniform(-NOISE_LEVEL, NOISE_LEVEL)))
        for et, w in base.items()
    }
    total = sum(jittered.values())
    return {et: w / total for et, w in jittered.items()}


def generate_session(persona, player_id, session_index, min_events, max_events):
    """Gera os eventos brutos de uma sessao de jogo para um jogador/persona."""
    profile = PERSONA_PROFILES[persona]
    weights_dict = session_weights(persona)
    types = list(weights_dict.keys())
    weights = list(weights_dict.values())
    dt_low, dt_high = profile["decision_time_ms"]

    n_events = random.randint(min_events, max_events)
    session_id = str(uuid.uuid4())
    t = datetime(2026, 9, 1) + timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))

    events = []
    for _ in range(n_events):
        event_type = random.choices(types, weights=weights, k=1)[0]
        decision_time = max(50, int(random.gauss((dt_low + dt_high) / 2, (dt_high - dt_low) / 4)))
        if event_type == "quest_fail":
            outcome = "fail"
        elif event_type == "retry":
            outcome = "retry"
        else:
            outcome = "success" if random.random() < 0.85 else "fail"

        t += timedelta(seconds=random.randint(2, 40))
        events.append(
            {
                "event_id": str(uuid.uuid4()),
                "session_id": session_id,
                "player_id": player_id,
                "timestamp": t.isoformat(),
                "event_type": event_type,
                "decision_time_ms": decision_time,
                "outcome": outcome,
            }
        )
    return session_id, events


def extract_features(session_id, player_id, persona, events):
    """Replica o que o modulo de extracao de features do Worker faria."""
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
        "true_persona": persona,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Gera dataset sintetico de jogadores para o BehaviorLens"
    )
    parser.add_argument("--players", type=int, default=200, help="numero de jogadores sinteticos")
    parser.add_argument("--min-events", type=int, default=20, help="minimo de eventos por sessao")
    parser.add_argument("--max-events", type=int, default=80, help="maximo de eventos por sessao")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--outdir", default="data")
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


def run_sanity_check(features_path):
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
