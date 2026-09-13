"""Vocabulário do domínio de Player Modeling.

Camada transversal: declara *o que as coisas são* neste domínio — a
Taxonomia de Bartle, os tipos de evento de jogador e as colunas de feature
— para que `api/`, `ml/`, `simulator/` e `worker/` compartilhem uma única
fonte da verdade em vez de importarem umas das outras.

Regra de entrada, verificada por teste
(`src/tests/player_modeling/domain/test_domain_layer.py`): **nenhum módulo
deste pacote importa qualquer outro módulo de `player_modeling`.** Só entra
aqui declaração de vocabulário e contrato de dados; comportamento fica no
módulo funcional correspondente (geração de eventos em `simulator/`,
agregação de features em `worker/`, treino e inferência em `ml/`).
"""
