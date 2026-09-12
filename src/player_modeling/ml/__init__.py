"""Treinamento e inferência do modelo de perfil (Taxonomia de Bartle).

`knn.py` implementa o classificador KNN: treino a partir do dataset
sintético rotulado (`src/data/sessions_features.csv`), predição da persona
de um jogador a partir de suas features agregadas e avaliação da qualidade
do modelo (ver ADR 0010).
"""
