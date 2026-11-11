# Agente de IA para Organização de Tarefas no Trello

Projeto desenvolvido para o desafio da **DIO** com **Python**, **Google Agent Development Kit (ADK)**, **Gemini** e **Trello** por meio da biblioteca `py-trello`.

Baseado no [exemplo do desafio (agents/agent04)](https://github.com/digitalinnovationone/agent-carbon-footprint/tree/main/agents/agent04), com melhorias na organização do código, normalização dos status e tratamento de erros.

> **Estado atual:** integração real com Gemini e Trello **validada pelo usuário em 11/11/2026**, com capturas de tela do ADK Web e do quadro Trello. Os dois prints de execução estão publicados na pasta [`evidencias/`](evidencias/).

## Objetivo

Criar um agente conversacional capaz de perguntar quais são as tarefas do dia, informar a data atual, criar cards no Trello, listar tarefas, mover cards entre listas e remover uma tarefa mediante confirmação.

## Ferramentas implementadas

| Ferramenta Python | Função |
| --- | --- |
| `get_temporal_context` | Informa a data/hora do dia no fuso configurado. |
| `adicionar_tarefa` | Cria card com nome, descrição e data na lista **A fazer**. |
| `listar_tarefas` | Lista tudo ou filtra por status. |
| `mudar_status_tarefa` | Move a tarefa entre **A fazer**, **Em andamento** e **Concluído**. |
| `remover_tarefa` | Exclui um card após confirmação explícita do usuário. |

O agente usa o modelo `gemini-3.8-flash` e registra as funções como ferramentas do Google ADK em `agenttaskmanager/agent.py`.

## Melhorias em relação ao exemplo original

1. **Data:** quando recebe `AAAA-MM-DD`, a data de vencimento é registrada ao meio-dia no fuso `America/Sao_Paulo`, minimizando o problema de exibição no dia anterior por conversão de fuso.
2. **Variações de status:** reconhece `concluído`, `concluido`, `feito`, `finalizado` e outras expressões por normalização de acentos.
3. **Remoção implementada:** a instrução do exemplo prometia remover tarefas, mas não oferecia a ferramenta; este projeto possui `remover_tarefa` com confirmação.
4. **Tratamento de erros:** operações retornam mensagens de erro estruturadas, sem afirmar sucesso quando a API falha.
5. **Conexão reaproveitada:** a construção do cliente e a busca pelo quadro foram centralizadas.
6. **Quadro configurável:** o nome vem de `TRELLO_BOARD_NAME`, em vez de ficar fixo no código.
7. **Proteção contra ambiguidade:** evita mover ou excluir quando existem cards com nomes iguais.

## Pré-requisitos

- Python **3.10 ou superior** (recomendado Python 3.11 ou 3.12).
- Conta no [Google AI Studio](https://aistudio.google.com/apikey) com chave Gemini.
- Conta no [Trello](https://trello.com/) e um quadro, por exemplo **DIO**, com três listas:
  - **A fazer**
  - **Em andamento**
  - **Concluído**
- Credenciais de API e token de acesso Trello com permissões de leitura e escrita.

## Instalação e configuração

### No Windows

Baixe os arquivos deste repositório, extraia em uma pasta e execute **`INICIAR_WINDOWS.bat`**. Ele cria um ambiente virtual, instala as dependências e abre o arquivo local de configuração na primeira execução.

### Pelo terminal

Execute os comandos a partir da raiz do projeto:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

No Linux/macOS use `python3 -m venv .venv` e `source .venv/bin/activate`.

Copie `agenttaskmanager/.env.exemplo` para `agenttaskmanager/.env` e preencha no **seu computador**:

```dotenv
GOOGLE_GENAI_USE_VERTEXAI=0
GOOGLE_API_KEY=SUA_CHAVE_GEMINI
TRELLO_API_KEY=SUA_CHAVE_TRELLO
TRELLO_API_SECRET=SEU_SEGREDO_TRELLO
TRELLO_TOKEN=SEU_TOKEN_TRELLO
TRELLO_BOARD_NAME=DIO
```

**Nunca publique o arquivo `.env`, credenciais, chaves, tokens ou segredos.** Ele está protegido pelo `.gitignore`.

### Como obter as credenciais

1. Crie o quadro e as três listas no Trello.
2. Acesse o [portal de Power-Ups](https://trello.com/power-ups/admin/), crie um aplicativo e obtenha a API Key e, caso aplicável, o API Secret.
3. Gere um token de autorização com escopos `read,write` seguindo o [tutorial oficial disponibilizado pela DIO](https://github.com/digitalinnovationone/agent-carbon-footprint/blob/main/agents/agent04/readme.md).
4. Gere a chave Gemini no [Google AI Studio](https://aistudio.google.com/apikey).
5. Salve as chaves apenas no arquivo `agenttaskmanager/.env` local.

## Executando o agente

No diretório raiz, com o ambiente virtual ativo:

```powershell
adk web
```

Abra o endereço informado no terminal, selecione o agente `agenttaskmanager` e converse com ele. Se `adk` não for encontrado, confirme a instalação das dependências e a ativação do ambiente virtual.

## Roteiro de validação

Execute estas ações com o agente e confira o quadro:

1. **Data:** “Bom dia! O que tenho para fazer hoje?” — o agente deve consultar o contexto temporal e perguntar suas tarefas.
2. **Criar:** “Crie a tarefa estudar Python, descrição revisar funções e listas, para hoje.”
3. **Listar:** “Liste as tarefas a fazer.”
4. **Mover:** “Comecei estudar Python, coloque em andamento.”
5. **Concluir:** “Concluí estudar Python.” — testa normalização de acento.
6. **Remover:** “Remova estudar Python.” — deve solicitar confirmação antes de excluir.

**Resultados observados em 11/11/2026:** a conversa no ADK mostrou execução de `get_temporal_context`, `adicionar_tarefa`, `mudar_status_tarefa` e `listar_tarefas`, com respostas de sucesso. O quadro Trello exibiu o card **Estudar Python** na lista **Concluído**, com vencimento em **11/11/2026**. Foram testadas a criação, a movimentação para **Em andamento** e depois **Concluído**, e a listagem por status. A ferramenta de exclusão **não foi testada**.

### Testes automatizados de lógica

```powershell
python -m unittest discover -s tests -v
```

O arquivo `tests/test_funcoes.py` cobre normalização de acentos, interpretação de status, tratamento de data sem mudança de dia e rejeição de data inválida. Os testes locais não necessitam de conexão com Trello.

## Evidências

Após testar no ambiente real, coloque prints em [`evidencias/`](evidencias/README.md):

- Chat do `adk web` com criação/movimentação de tarefa.
- Quadro Trello com o card aparecendo nas listas.

**A execução real foi confirmada visualmente e as capturas estão publicadas:** [print do ADK Web](evidencias/image(20261111-233956).png) e [print do quadro Trello](evidencias/image(20261111-233941).png). Evite incluir dados privados nos prints.

## Arquivos do projeto

```text
agente-ia-trello/
├── .gitignore
├── README.md
├── requirements.txt
├── INICIAR_WINDOWS.bat
├── agenttaskmanager/
│   ├── .env.exemplo
│   ├── __init__.py
│   └── agent.py
├── tests/
│   └── test_funcoes.py
└── evidencias/
    ├── README.md
    ├── image(20261111-233941).png
    └── image(20261111-233956).png
```

## Referências

- [Repositório-base da DIO](https://github.com/digitalinnovationone/agent-carbon-footprint/tree/main/agents/agent04)
- [Documentação do Google ADK](https://google.github.io/adk-docs/)
- [Biblioteca py-trello](https://github.com/sarumont/py-trello)
