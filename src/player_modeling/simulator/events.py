"""Geração de eventos sintéticos de jogador por persona (Taxonomia de Bartle).

Esta lógica é compartilhada entre o script de geração do dataset offline
(`player_modeling.scripts.generate_raw_events`, usado para pré-treinar o
modelo enquanto a pipeline real não está pronta) e o worker publisher
(`player_modeling.simulator.publisher`), para que a distribuição de
eventos por persona não seja duplicada entre os dois usos.
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import Any

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
PERSONA_PROFILES: dict[str, dict[str, Any]] = {
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

NOISE_LEVEL = 0.5  # jitter multiplicativo aplicado aos pesos de cada lote de eventos
MIX_PROB = 0.45  # chance de um lote misturar uma segunda persona
MIX_RANGE = (0.2, 0.45)  # peso da persona secundaria na mistura


def session_weights(persona: str) -> dict[str, float]:
    """Monta os pesos de evento para um lote de eventos.

    Parte dos lotes mistura uma segunda persona (jogador nao e 100% puro
    em um arquetipo), e todos recebem jitter individual antes de
    renormalizar, para gerar dados realistas (nao 100% separaveis).

    :param persona: persona da Taxonomia de Bartle usada como base.

    :return: dicionario de tipo de evento para peso de probabilidade,
        normalizado para somar 1.
    """
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


def generate_events(
    weights_dict: dict[str, float],
    decision_time_range: tuple[int, int],
    session_id: str,
    player_id: str,
    n_events: int,
    start_time: datetime,
) -> list[dict[str, Any]]:
    """Gera uma lista de eventos brutos a partir de uma distribuição já calculada.

    :param weights_dict: pesos de tipo de evento, como retornado por
        :func:`session_weights`.
    :param decision_time_range: faixa (mínimo, máximo) em milissegundos
        usada para amostrar o tempo de decisão de cada evento.
    :param session_id: identificador da sessão/lote ao qual os eventos
        pertencem.
    :param player_id: identificador do jogador simulado.
    :param n_events: quantidade de eventos a gerar.
    :param start_time: instante inicial a partir do qual os timestamps
        dos eventos avançam.

    :return: lista de eventos no formato de `src/data/events.csv`
        (sem o rótulo de persona/`true_persona`).
    """
    types = list(weights_dict.keys())
    weights = list(weights_dict.values())
    dt_low, dt_high = decision_time_range

    t = start_time
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
    return events
