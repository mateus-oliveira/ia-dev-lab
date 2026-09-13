"""Tipos de evento de jogador reconhecidos pelo domínio.

Vocabulário compartilhado entre quem **produz** eventos (o simulador hoje,
uma plataforma de jogos real no futuro) e quem os **consome** (o worker/ETL).
Declarado aqui para que o consumidor não precise depender do produtor.
"""

EVENT_TYPES: list[str] = [
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
