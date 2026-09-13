"""Script de linha de comando para avaliar o classificador de personas.

Mede a qualidade do modelo sobre o dataset sintético rotulado
(`src/data/sessions_features.csv`), fora do caminho de inicialização e de
requisição da API: a avaliação reserva um conjunto de teste, enquanto o
modelo que serve a API é treinado com o dataset completo (ver ADR 0010).

Uso:
    PYTHONPATH=src poetry run python -m player_modeling.scripts.evaluate_model
    PYTHONPATH=src poetry run python -m player_modeling.scripts.evaluate_model --test-size 0.2
"""

import argparse
import sys
from pathlib import Path

from player_modeling.ml.knn import (
    DEFAULT_RANDOM_STATE,
    DEFAULT_TEST_SIZE,
    ClassifierEvaluation,
    evaluate_classifier,
)


def build_parser() -> argparse.ArgumentParser:
    """Monta o parser de argumentos do script de avaliação.

    :return: Parser configurado com as opções de dataset, divisão e semente.
    """
    parser = argparse.ArgumentParser(
        description="Avalia o classificador KNN de personas da Taxonomia de Bartle."
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=None,
        help="Caminho alternativo do CSV de features rotuladas.",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=DEFAULT_TEST_SIZE,
        help=f"Fração do dataset reservada para teste (padrão: {DEFAULT_TEST_SIZE}).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_RANDOM_STATE,
        help=f"Semente da divisão treino/teste (padrão: {DEFAULT_RANDOM_STATE}).",
    )
    return parser


def format_evaluation(evaluation: ClassifierEvaluation) -> str:
    """Formata o resultado da avaliação para exibição no terminal.

    :param evaluation: Resultado devolvido por `evaluate_classifier`.

    :return: Texto com acurácia, personas avaliadas e relatório por classe.
    """
    classes = ", ".join(evaluation.classes)
    return (
        f"Acurácia: {evaluation.accuracy:.4f}\n"
        f"Personas avaliadas: {classes}\n\n"
        f"{evaluation.report}"
    )


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada do script: avalia o classificador e imprime o resultado.

    :param argv: Argumentos de linha de comando; usa `sys.argv[1:]` se omitido.

    :return: 0 em caso de sucesso; 1 se o dataset estiver ausente ou inválido.
    """
    args = build_parser().parse_args(argv)

    try:
        evaluation = evaluate_classifier(
            dataset_path=args.dataset,
            test_size=args.test_size,
            random_state=args.seed,
        )
    except (FileNotFoundError, ValueError) as error:
        print(f"Falha ao avaliar o classificador: {error}", file=sys.stderr)
        return 1

    print(format_evaluation(evaluation))
    return 0


if __name__ == "__main__":
    sys.exit(main())
