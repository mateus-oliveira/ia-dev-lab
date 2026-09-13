"""Taxonomia de Bartle: os arquétipos de jogador do domínio."""

from enum import Enum


class BartlePersona(str, Enum):
    """Arquétipos de jogadores segundo a Taxonomia de Bartle.

    A ordem de declaração é significativa e não deve ser alterada: `PERSONAS`
    é derivada dela e alimenta o sorteio semeado de personas em
    `player_modeling.scripts.generate_raw_events`. Reordenar mudaria o
    dataset produzido por uma mesma semente, e `src/data/` não pode ser
    sobrescrito (ver "Não modificar dados brutos" no CLAUDE.md).
    """

    ACHIEVER = "Achiever"
    EXPLORER = "Explorer"
    SOCIALIZER = "Socializer"
    KILLER = "Killer"


PERSONAS: list[str] = [persona.value for persona in BartlePersona]
