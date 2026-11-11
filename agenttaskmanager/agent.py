"""Agente de tarefas com Google ADK e Trello.

Não compartilhe chaves no chat, nos logs ou no GitHub.
"""

from __future__ import annotations

from datetime import datetime
import os
import unicodedata
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from google.adk.agents import Agent
from trello import TrelloClient

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

STATUS_CANONICOS = {
    'a fazer': ('A fazer', 'A FAZER', 'TO DO', 'TODO'),
    'em andamento': ('Em andamento', 'EM ANDAMENTO', 'DOING', 'IN PROGRESS'),
    'concluido': ('Concluído', 'CONCLUÍDO', 'CONCLUIDO', 'DONE'),
}


def _normalizar(texto: str) -> str:
    """Normaliza acentos, espaços e caixa para comparação de nomes."""
    texto = unicodedata.normalize('NFKD', str(texto or ''))
    return ' '.join(''.join(c for c in texto if not unicodedata.combining(c)).casefold().split())


def _status(texto: str) -> str | None:
    normalizado = _normalizar(texto)
    sinonimos = {
        'afazer': 'a fazer', 'todo': 'a fazer', 'to do': 'a fazer', 'pendente': 'a fazer',
        'andamento': 'em andamento', 'fazendo': 'em andamento', 'doing': 'em andamento',
        'in progress': 'em andamento',
        'concluido': 'concluido', 'concluida': 'concluido', 'feito': 'concluido',
        'feita': 'concluido', 'finalizado': 'concluido', 'finalizada': 'concluido',
        'done': 'concluido',
    }
    if normalizado in STATUS_CANONICOS:
        return normalizado
    return sinonimos.get(normalizado)


def _trello_client() -> TrelloClient:
    credenciais = {
        'api_key': os.getenv('TRELLO_API_KEY'),
        'api_secret': os.getenv('TRELLO_API_SECRET'),
        'token': os.getenv('TRELLO_TOKEN'),
    }
    if not all(credenciais.values()):
        raise ValueError('Credenciais do Trello ausentes. Configure o arquivo .env local.')
    return TrelloClient(**credenciais)


def _quadro():
    nome = os.getenv('TRELLO_BOARD_NAME', 'DIO').strip()
    quadros = [q for q in _trello_client().list_boards() if _normalizar(q.name) == _normalizar(nome)]
    if not quadros:
        raise ValueError(f'Quadro {nome!r} não encontrado no Trello.')
    if len(quadros) > 1:
        raise ValueError(f'Existem vários quadros chamados {nome!r}. Renomeie o quadro para torná-lo único.')
    return quadros[0]


def _listas():
    listas = _quadro().list_lists()
    saida = {}
    for lista in listas:
        for status, nomes in STATUS_CANONICOS.items():
            if _normalizar(lista.name) in {_normalizar(n) for n in nomes}:
                if status in saida:
                    raise ValueError(f'Existem duas listas equivalentes a {status!r}.')
                saida[status] = lista
    return saida


def _lista_obrigatoria(status: str):
    listas = _listas()
    if status not in listas:
        raise ValueError(f'Lista {status!r} não encontrada. Crie A fazer, Em andamento e Concluído.')
    return listas[status]


def _encontrar_card_unico(nome_da_task: str):
    encontrados = []
    for status, lista in _listas().items():
        for card in lista.list_cards():
            if _normalizar(card.name) == _normalizar(nome_da_task):
                encontrados.append((status, lista, card))
    if not encontrados:
        raise ValueError(f'Tarefa {nome_da_task!r} não encontrada.')
    if len(encontrados) > 1:
        raise ValueError(f'Existem {len(encontrados)} tarefas com esse nome. Renomeie a desejada para evitar alterações indevidas.')
    return encontrados[0]


def get_temporal_context() -> dict:
    """Devolve a data e hora atuais no fuso configurado (padrão: Brasília)."""
    try:
        tz = ZoneInfo(os.getenv('TZ', 'America/Sao_Paulo'))
        agora = datetime.now(tz)
        return {'data': agora.date().isoformat(), 'hora': agora.strftime('%H:%M:%S'), 'fuso': str(tz)}
    except Exception as exc:
        return {'erro': f'Não foi possível consultar data/hora: {exc}'}


def _data_trello(due_date: str) -> str:
    """Converte YYYY-MM-DD para meio-dia no fuso local, evitando o dia anterior na UI."""
    tz = ZoneInfo(os.getenv('TZ', 'America/Sao_Paulo'))
    entrada = str(due_date).strip()
    if not entrada:
        raise ValueError('Informe a data no formato AAAA-MM-DD.')
    try:
        if len(entrada) == 10:
            dia = datetime.strptime(entrada, '%Y-%m-%d').date()
            return datetime(dia.year, dia.month, dia.day, 12, 0, tzinfo=tz).isoformat()
        dt = datetime.fromisoformat(entrada.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tz)
        return dt.isoformat()
    except ValueError as exc:
        raise ValueError('Data inválida. Use AAAA-MM-DD ou data/hora ISO 8601.') from exc


def adicionar_tarefa(nome_da_task: str, descricao_da_task: str, due_date: str) -> dict:
    """Cria um card na lista A fazer com nome, descrição e vencimento."""
    try:
        if not nome_da_task.strip():
            raise ValueError('Nome da tarefa não pode ficar vazio.')
        lista = _lista_obrigatoria('a fazer')
        data = _data_trello(due_date)
        card = lista.add_card(name=nome_da_task.strip(), desc=descricao_da_task.strip(), due=data)
        return {'sucesso': True, 'mensagem': f'Tarefa {nome_da_task!r} criada em A fazer.', 'card_id': card.id, 'vencimento': data}
    except Exception as exc:
        return {'sucesso': False, 'erro': str(exc)}


def listar_tarefas(status: str = 'todas') -> dict:
    """Lista as tarefas do quadro ou filtra por A fazer, Em andamento e Concluído."""
    try:
        if _normalizar(status) in ('todas', 'todos', 'all'):
            listas = _listas()
        else:
            chave = _status(status)
            if chave is None:
                raise ValueError('Status inválido. Use todas, a fazer, em andamento ou concluído.')
            listas = {chave: _lista_obrigatoria(chave)}
        tarefas = []
        for chave, lista in listas.items():
            for card in lista.list_cards():
                tarefas.append({'nome': card.name, 'descricao': card.desc, 'vencimento': str(card.due) if card.due else None, 'status': chave, 'id': card.id})
        return {'sucesso': True, 'quantidade': len(tarefas), 'tarefas': tarefas}
    except Exception as exc:
        return {'sucesso': False, 'erro': str(exc)}


def mudar_status_tarefa(nome_da_task: str, novo_status: str) -> dict:
    """Move uma tarefa para A fazer, Em andamento ou Concluído."""
    try:
        chave = _status(novo_status)
        if chave is None:
            raise ValueError('Status inválido. Use a fazer, em andamento ou concluído.')
        origem, _, card = _encontrar_card_unico(nome_da_task)
        destino = _lista_obrigatoria(chave)
        if origem == chave:
            return {'sucesso': True, 'mensagem': f'Tarefa já está em {chave}.'}
        card.change_list(destino.id)
        return {'sucesso': True, 'mensagem': f'{card.name}: {origem} → {chave}'}
    except Exception as exc:
        return {'sucesso': False, 'erro': str(exc)}


def remover_tarefa(nome_da_task: str, confirmar: bool = False) -> dict:
    """Remove um card apenas após confirmação explícita do usuário."""
    try:
        if not confirmar:
            return {'sucesso': False, 'confirmacao_necessaria': True, 'mensagem': f'Confirma a exclusão definitiva da tarefa {nome_da_task!r}?'}
        _, _, card = _encontrar_card_unico(nome_da_task)
        card.delete()
        return {'sucesso': True, 'mensagem': f'Tarefa {nome_da_task!r} excluída.'}
    except Exception as exc:
        return {'sucesso': False, 'erro': str(exc)}


root_agent = Agent(
    model='gemini-3.8-flash',
    name='root_agent',
    description='Assistente de tarefas em português integrado ao Trello.',
    instruction=(
        'Você é um assistente brasileiro de organização de tarefas integrado ao Trello. '
        'Na primeira resposta, use get_temporal_context para informar a data de hoje e pergunte quais tarefas a pessoa precisa fazer. '
        'Se o usuário informar várias tarefas, crie um card individual para cada uma após obter nome, descrição e data. '
        'Se faltar data, pergunte se pode usar a data de hoje antes de criar. '
        'Sempre use ferramentas para operações reais; não diga que criou, moveu ou excluiu um card sem retorno de sucesso. '
        'Ofereça listar tudo ou filtrar por A fazer, Em andamento ou Concluído. '
        'Quando a pessoa informar progresso, use mudar_status_tarefa. Aceite variações como concluído, concluido, feito e finalizado. '
        'Para excluir, solicite confirmação clara da pessoa ANTES de chamar remover_tarefa com confirmar=True. '
        'Nunca peça chaves, tokens ou segredos pelo chat; indique a configuração local do arquivo .env. '
        'Se houver erro da API, explique resumidamente sem inventar resultados.'
    ),
    tools=[get_temporal_context, adicionar_tarefa, listar_tarefas, mudar_status_tarefa, remover_tarefa],
)
