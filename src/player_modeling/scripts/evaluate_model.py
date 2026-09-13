"""Script de linha de comando para avaliar os classificadores de personas.

Mede a qualidade dos modelos sobre o dataset sintético rotulado
(`src/data/sessions_features.csv`), fora do caminho de inicialização e de
requisição da API: a avaliação reserva um conjunto de teste, enquanto os
modelos que servem a API são treinados com o dataset completo (ver ADR 0010).

Uso:
    PYTHONPATH=src poetry run python -m player_modeling.scripts.evaluate_model
    PYTHONPATH=src poetry run python -m player_modeling.scripts.evaluate_model --model knn
"""

import argparse
import sys
from pathlib import Path
from types import ModuleType

from player_modeling.ml import decision_tree, knn
from player_modeling.ml.persona_model import (
    DEFAULT_RANDOM_STATE,
    DEFAULT_TEST_SIZE,
    ClassifierEvaluation,
)

MODEL_MODULES: dict[str, ModuleType] = {
    knn.MODEL_KEY: knn,
    decision_tree.MODEL_KEY: decision_tree,
}

ALL_MODELS = "both"


def build_parser() -> argparse.ArgumentParser:
    """Monta o parser de argumentos do script de avaliação.

    :return: Parser configurado com as opções de modelo, dataset, divisão e semente.
    """
    parser = argparse.ArgumentParser(
        description="Avalia os classificadores de personas da Taxonomia de Bartle."
    )
    parser.add_argument(
        "--model",
        choices=[*MODEL_MODULES, ALL_MODELS],
        default=ALL_MODELS,
        help=f"Modelo a avaliar (padrão: {ALL_MODELS}, avalia todos).",
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


def select_models(model: str) -> dict[str, ModuleType]:
    """Resolve a opção `--model` para os módulos de modelo a avaliar.

    :param model: Valor recebido em `--model`.

    :return: Módulos a avaliar, indexados pela chave do modelo.
    """
    if model == ALL_MODELS:
        return dict(MODEL_MODULES)
    return {model: MODEL_MODULES[model]}


def format_evaluation(model_key: str, evaluation: ClassifierEvaluation) -> str:
    """Formata o resultado da avaliação de um modelo para exibição no terminal.

    :param model_key: Chave do modelo avaliado.
    :param evaluation: Resultado devolvido por `evaluate_classifier`.

    :return: Texto com acurácia, personas avaliadas e relatório por classe.
    """
    classes = ", ".join(evaluation.classes)
    return (
        f"=== {model_key} ===\n"
        f"Acurácia: {evaluation.accuracy:.4f}\n"
        f"Personas avaliadas: {classes}\n\n"
        f"{evaluation.report}"
    )


def format_summary(accuracies: dict[str, float]) -> str:
    """Formata a comparação final de acurácia entre os modelos avaliados.

    :param accuracies: Acurácia obtida por cada modelo, indexada pela chave.

    :return: Texto com uma linha por modelo, em ordem decrescente de acurácia.
    """
    ranked = sorted(accuracies.items(), key=lambda item: item[1], reverse=True)
    lines = "\n".join(f"  {model_key:<16} {accuracy:.4f}" for model_key, accuracy in ranked)
    return f"=== comparação ===\n{lines}"


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada do script: avalia os modelos e imprime o resultado.

    :param argv: Argumentos de linha de comando; usa `sys.argv[1:]` se omitido.

    :return: 0 em caso de sucesso; 1 se o dataset estiver ausente ou inválido.
    """
    args = build_parser().parse_args(argv)
    modules = select_models(args.model)

    accuracies: dict[str, float] = {}
    try:
        for model_key, module in modules.items():
            evaluation = module.evaluate_classifier(
                dataset_path=args.dataset,
                test_size=args.test_size,
                random_state=args.seed,
            )
            accuracies[model_key] = evaluation.accuracy
            print(format_evaluation(model_key, evaluation))
    except (FileNotFoundError, ValueError) as error:
        print(f"Falha ao avaliar o classificador: {error}", file=sys.stderr)
        return 1

    if len(accuracies) > 1:
        print(format_summary(accuracies))
    return 0


if __name__ == "__main__":
    sys.exit(main())
