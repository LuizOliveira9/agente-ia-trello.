"""Testes sem conexão externa; funções puras do agente."""
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from agenttaskmanager.agent import _normalizar, _status, _data_trello


class TestFuncoes(unittest.TestCase):
    def test_acento_e_espacos(self):
        self.assertEqual(_normalizar('  CONCLUÍDO  '), 'concluido')

    def test_status(self):
        for valor in ('concluído', 'concluido', 'Feito', 'finalizado'):
            self.assertEqual(_status(valor), 'concluido')
        self.assertEqual(_status('EM ANDAMENTO'), 'em andamento')
        self.assertIsNone(_status('desconhecido'))

    def test_data_sem_deslocamento_de_dia(self):
        data = datetime.fromisoformat(_data_trello('2026-11-11'))
        self.assertEqual(data.astimezone(ZoneInfo('America/Sao_Paulo')).date().isoformat(), '2026-11-11')
        self.assertEqual(data.hour, 12)

    def test_data_invalida(self):
        with self.assertRaises(ValueError):
            _data_trello('2026-99-99')


if __name__ == '__main__':
    unittest.main()
