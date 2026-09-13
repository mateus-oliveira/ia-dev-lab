## ADDED Requirements

### Requirement: Bloqueio de escrita do agente nos dados de origem

O harness SHALL impedir, antes da execução, que o agente de IA altere, sobrescreva, trunque, mova ou remova os arquivos de dataset de origem do projeto (`src/data/events.csv` e `src/data/sessions_features.csv`), independentemente da ferramenta usada e independentemente de a ação ter sido solicitada explicitamente na conversa. O bloqueio SHALL devolver ao agente uma mensagem indicando a regra violada e o caminho sancionado de regeneração do dataset.

#### Scenario: Edição direta de arquivo de origem é bloqueada

- **WHEN** o agente tenta escrever ou editar um arquivo de dataset de origem por uma ferramenta de edição de arquivo
- **THEN** a chamada é bloqueada antes de qualquer escrita, o arquivo permanece byte a byte inalterado, e o agente recebe a mensagem com o motivo do bloqueio

#### Scenario: Sobrescrita por shell é bloqueada

- **WHEN** o agente tenta executar um comando de shell que redireciona saída para um arquivo de dataset de origem (`>` ou `>>`) ou que aplica a ele um utilitário de escrita ou remoção (`rm`, `mv`, `cp`, `tee`, `truncate`, `dd`, `sed`)
- **THEN** a chamada é bloqueada antes da execução e o arquivo permanece inalterado

#### Scenario: Caminho equivalente não escapa do bloqueio

- **WHEN** o agente referencia um arquivo de dataset de origem por um caminho equivalente ao caminho protegido (prefixado por `./`, com segmentos redundantes, ou absoluto dentro do repositório)
- **THEN** a chamada é bloqueada da mesma forma que a referência canônica

### Requirement: Leitura e regeneração oficial permanecem permitidas

O bloqueio SHALL restringir-se a escrita: leitura, inspeção e análise dos arquivos de dataset de origem SHALL permanecer permitidas, e a execução do script oficial de geração do dataset (`src/player_modeling/scripts/generate_raw_events.py`) NÃO SHALL ser bloqueada, por ser o caminho de regeneração sancionado pelo `CLAUDE.md`.

#### Scenario: Leitura do dataset é permitida

- **WHEN** o agente executa um comando de leitura sobre um arquivo de dataset de origem (por exemplo, exibir, contar linhas ou filtrar conteúdo)
- **THEN** a chamada é permitida e executa normalmente

#### Scenario: Script oficial de geração é permitido

- **WHEN** o agente executa o script oficial de geração do dataset sintético
- **THEN** a chamada é permitida, ainda que o script regrave os arquivos de dataset

### Requirement: Falha do hook não interrompe a sessão do agente

Quando o hook receber um payload que não puder interpretar (conteúdo não-JSON ou sem as chaves esperadas), ele SHALL permitir a execução da ferramenta em vez de bloqueá-la, para que uma falha do próprio controle não inviabilize a sessão de trabalho.

#### Scenario: Payload malformado é tratado como permitido

- **WHEN** o hook recebe um payload que não é JSON válido ou que não contém as chaves esperadas
- **THEN** a execução da ferramenta é permitida e nenhum erro é propagado ao agente
