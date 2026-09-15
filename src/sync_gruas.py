import os
import requests
import pandas as pd
from datetime import timedelta
from typing import Dict


class GruasSyncError(Exception):
    """Erro ao sincronizar com o sistema de gruas"""


def _inicio_da_semana(data: pd.Timestamp) -> str:
    """Retorna a segunda-feira da semana da data informada, em ISO (AAAA-MM-DD)"""
    segunda = data - timedelta(days=data.weekday())
    return segunda.strftime('%Y-%m-%d')


def montar_registros_semanais(df: pd.DataFrame) -> list:
    """
    Agrega o banco de dados consolidado (linhas por dia/máquina) em totais
    semanais por cidade+máquina, no formato esperado pelo endpoint
    /api/contabil/importar-whatsapp do sistema de gruas.
    """
    if df is None or df.empty:
        return []

    trabalho = df.copy()
    trabalho['semana_inicio'] = trabalho['data'].apply(_inicio_da_semana)

    registros = []
    agrupado = trabalho.groupby(['cidade', 'maquina', 'semana_inicio'], as_index=False).agg(
        quantidade_premios=('pelucias', 'sum'),
        faturamento=('valor', 'sum'),
        dias=('data', 'count'),
    )

    for _, linha in agrupado.iterrows():
        registros.append({
            'cidade': linha['cidade'],
            'maquina': str(linha['maquina']),
            'semana_inicio': linha['semana_inicio'],
            'quantidade_premios': int(linha['quantidade_premios']),
            'faturamento': round(float(linha['faturamento']), 2),
            'mensagem_original': f"Consolidado automaticamente de {int(linha['dias'])} dia(s) via WhatsApp",
        })

    return registros


def sincronizar(df: pd.DataFrame) -> Dict:
    """
    Envia os totais semanais de todo o banco de dados consolidado pro
    sistema de gruas. Reenviar é seguro: o endpoint substitui o lançamento
    da mesma máquina/semana/origem em vez de duplicar.
    """
    api_url = os.environ.get('SISTEMA_GRUAS_API_URL', '').rstrip('/')
    api_key = os.environ.get('SISTEMA_GRUAS_API_KEY', '')

    if not api_url or not api_key:
        raise GruasSyncError(
            'Configure SISTEMA_GRUAS_API_URL e SISTEMA_GRUAS_API_KEY (arquivo .env) '
            'para sincronizar com o sistema de gruas.'
        )

    registros = montar_registros_semanais(df)
    if not registros:
        return {'processados': 0, 'criados': 0, 'atualizados': 0, 'erros': []}

    resposta = requests.post(
        f'{api_url}/api/contabil/importar-whatsapp',
        json={'registros': registros},
        headers={'x-api-key': api_key},
        timeout=30,
    )

    if resposta.status_code != 200:
        detalhe = resposta.text
        try:
            detalhe = resposta.json().get('error', detalhe)
        except ValueError:
            pass
        raise GruasSyncError(f'Erro {resposta.status_code} do sistema de gruas: {detalhe}')

    return resposta.json()
