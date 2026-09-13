"""Testes do script de avaliação dos classificadores de personas.

Escritos **depois** da implementação, de propósito: este script é a tarefa
de controle da Etapa 2 da atividade (implementada sem TDD), e estes testes
existem para medir o que a ausência de TDD deixou passar.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from player_modeling.api.app import app
from player_modeling.api.schemas import PersonaResponse
from player_modeling.ml import decision_tree, knn
from player_modeling.scripts.evaluate_model import (
    ALL_MODELS,
    MODEL_MODULES,
    build_parser,
    main,
    select_models,
)


def test_default_model_option_selects_every_model() -> None:
    """Sem `--model`, o script avalia todos os modelos disponíveis."""
    args = build_parser().parse_args([])

    assert args.model == ALL_MODELS
    assert set(select_models(args.model)) == set(MODEL_MODULES)


def test_model_option_selects_a_single_model() -> None:
    """Com `--model knn`, apenas o KNN é avaliado."""
    args = build_parser().parse_args(["--model", knn.MODEL_KEY])

    assert set(select_models(args.model)) == {knn.MODEL_KEY}


def test_unknown_model_is_rejected_by_the_parser() -> None:
    """Um modelo inexistente é rejeitado antes de qualquer treino."""
    with pytest.raises(SystemExit):
        build_parser().parse_args(["--model", "rede-neural"])


def test_model_options_cover_every_registered_model() -> None:
    """Todo modelo registrado é oferecido na opção `--model`.

    Protege contra adicionar um modelo em `ml/` e esquecer do script.
    """
    for model_key in MODEL_MODULES:
        assert build_parser().parse_args(["--model", model_key]).model == model_key

    assert set(MODEL_MODULES) == {knn.MODEL_KEY, decision_tree.MODEL_KEY}


def test_registered_models_match_the_api_response_contract() -> None:
    """Os modelos do script, os treinados pela API e os campos da resposta coincidem.

    Nada além deste teste liga as três camadas: registrar um modelo novo em
    `ml/` sem adicionar o campo correspondente em `PersonaResponse` produziria
    uma resposta silenciosamente incompleta.
    """
    response_models = set(PersonaResponse.model_fields) - {"player_id"}

    assert set(MODEL_MODULES) == response_models

    with TestClient(app):
        assert set(app.state.persona_classifiers) == response_models


def test_main_prints_accuracy_for_every_model(capsys: pytest.CaptureFixture[str]) -> None:
    """A execução padrão imprime a acurácia de cada modelo e a comparação final.

    :param capsys: Fixture do pytest que captura a saída padrão.
    """
    exit_code = main([])
    output = capsys.readouterr().out

    assert exit_code == 0
    for model_key in MODEL_MODULES:
        assert f"=== {model_key} ===" in output
    assert "=== comparação ===" in output


def test_main_omits_comparison_for_a_single_model(capsys: pytest.CaptureFixture[str]) -> None:
    """Com um único modelo não há comparação a fazer.

    :param capsys: Fixture do pytest que captura a saída padrão.
    """
    exit_code = main(["--model", knn.MODEL_KEY])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "=== comparação ===" not in output


def test_main_reports_missing_dataset(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Dataset inexistente devolve código de saída != 0 com mensagem em stderr.

    :param tmp_path: Diretório temporário fornecido pelo pytest.
    :param capsys: Fixture do pytest que captura a saída padrão.
    """
    exit_code = main(["--dataset", str(tmp_path / "inexistente.csv")])

    assert exit_code == 1
    assert "Falha ao avaliar" in capsys.readouterr().err


def test_main_rejects_test_size_out_of_range(capsys: pytest.CaptureFixture[str]) -> None:
    """Uma fração de teste fora de (0, 1) não deve produzir avaliação silenciosa.

    :param capsys: Fixture do pytest que captura a saída padrão.
    """
    exit_code = main(["--test-size", "1.5"])

    assert exit_code == 1
    assert capsys.readouterr().err != ""


def test_main_rejects_negative_test_size(capsys: pytest.CaptureFixture[str]) -> None:
    """Uma fração de teste negativa não deve produzir avaliação silenciosa.

    :param capsys: Fixture do pytest que captura a saída padrão.
    """
    exit_code = main(["--test-size", "-0.3"])

    assert exit_code == 1
    assert capsys.readouterr().err != ""


def test_main_does_not_print_partial_results_before_failing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Uma falha no meio da avaliação não deve deixar resultado parcial na tela.

    Com dois modelos e um dataset inválido, o script não deve imprimir o
    resultado do primeiro modelo e só então falhar.

    :param tmp_path: Diretório temporário fornecido pelo pytest.
    :param capsys: Fixture do pytest que captura a saída padrão.
    """
    incomplete = tmp_path / "incompleto.csv"
    incomplete.write_text("n_events,true_persona\n10,Killer\n", encoding="utf-8")

    exit_code = main(["--dataset", str(incomplete)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
