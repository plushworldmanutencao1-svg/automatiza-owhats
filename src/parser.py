import re
from datetime import datetime
from typing import List, Dict, Optional

class WhatsAppParser:
    """Parser para extrair dados de conversas exportadas do WhatsApp"""

    # Regex para linha de data/hora e autor
    DATETIME_PATTERN = r'(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2})\s*-\s*(.+?):\s*(.*)$'

    # Regex para máquinas (Black/Big número)
    MACHINE_PATTERN = r'\*?(Black|Big)\*?\s+\((\d+)\)'

    # Regex para dados estruturados
    DATA_PATTERNS = {
        'pelucias': r'\*?Pelúcias:\*?\s*(\d+)',
        'valor': r'\*?R\$\*?\s*([\d.,]+)',
    }

    def __init__(self, city_name: str):
        self.city_name = city_name
        self.records = []

    def parse_file(self, filepath: str) -> List[Dict]:
        """Parse arquivo TXT do WhatsApp e extrai dados de máquinas"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Dividir por mensagens (linhas com data/hora)
        lines = content.split('\n')
        current_message = []
        current_datetime = None
        current_author = None

        for line in lines:
            # Verifica se é uma nova mensagem (tem data/hora)
            match = re.match(self.DATETIME_PATTERN, line)

            if match:
                # Processa mensagem anterior se existir
                if current_message:
                    self._process_message(
                        current_datetime,
                        current_author,
                        '\n'.join(current_message)
                    )

                # Inicia nova mensagem
                current_datetime = match.group(1)  # DD/MM/YYYY
                current_author = match.group(3)
                current_message = [match.group(4)]  # Conteúdo após ":"
            else:
                # Continua mensagem anterior
                if current_message is not None:
                    current_message.append(line)

        # Processa última mensagem
        if current_message:
            self._process_message(
                current_datetime,
                current_author,
                '\n'.join(current_message)
            )

        return self.records

    def _process_message(self, date_str: str, author: str, content: str):
        """Processa conteúdo de uma mensagem para extrair dados de máquinas"""

        # Verifica se é uma mensagem relevante (contém máquina)
        if not re.search(self.MACHINE_PATTERN, content):
            return

        # Extrai dados da máquina
        machine_match = re.search(self.MACHINE_PATTERN, content)
        if not machine_match:
            return

        machine_number = machine_match.group(2)

        # Extrai outros dados
        data = {
            'data': date_str,
            'cidade': self.city_name,
            'maquina': machine_number,
        }

        # Extrai cada campo de dados
        for field, pattern in self.DATA_PATTERNS.items():
            match = re.search(pattern, content)
            if match:
                value = match.group(1).strip()
                if field == 'valor':
                    data[field] = self._normalize_number(value)
                else:
                    data[field] = int(value)
            else:
                data[field] = None

        # Só adiciona se tiver valor E pelúcias
        if data.get('valor') and data.get('pelucias'):
            self.records.append(data)

    @staticmethod
    def _normalize_number(value: str) -> float:
        """Converte string com número português para float"""
        if not value or value.upper() == 'XXX':
            return None

        # Remove espaços
        value = value.strip()

        # Trata formato português (1.234,56 → 1234.56)
        if ',' in value and '.' in value:
            # Formato: 1.234,56
            value = value.replace('.', '').replace(',', '.')
        elif ',' in value:
            # Formato: 1,5
            value = value.replace(',', '.')

        try:
            return float(value)
        except ValueError:
            return None

    def get_records(self) -> List[Dict]:
        """Retorna todos os registros extraídos"""
        return self.records
