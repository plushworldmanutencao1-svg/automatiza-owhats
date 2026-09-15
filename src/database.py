import pandas as pd
import os
from datetime import datetime
from typing import List, Dict, Tuple

class DatabaseManager:
    """Gerencia banco de dados consolidado de múltiplas conversas/cidades"""

    def __init__(self, db_path: str = "dados_consolidados.xlsx"):
        self.db_path = db_path
        self.df = None
        self._load_database()

    def _load_database(self):
        """Carrega banco de dados existente ou cria novo"""
        if os.path.exists(self.db_path):
            self.df = pd.read_excel(self.db_path)
            # Garante que a coluna de data é datetime
            self.df['data'] = pd.to_datetime(self.df['data'])
        else:
            # Cria DataFrame vazio com estrutura esperada
            self.df = pd.DataFrame(columns=[
                'data', 'cidade', 'maquina',
                'pelucias', 'valor', 'media', 'data_atualizacao'
            ])

    def add_records(self, new_records: List[Dict]) -> Tuple[int, int]:
        """
        Adiciona novos registros ao banco de dados
        Evita duplicatas verificando data + cidade + máquina

        Returns: (total_adicionados, total_duplicados)
        """
        if not new_records:
            return 0, 0

        # Converte novos registros para DataFrame
        new_df = pd.DataFrame(new_records)
        new_df['data'] = pd.to_datetime(new_df['data'], format='%d/%m/%Y', errors='coerce')

        # Adiciona data de atualização
        new_df['data_atualizacao'] = datetime.now().strftime('%d/%m/%Y %H:%M')

        added = 0
        duplicated = 0

        for _, new_record in new_df.iterrows():
            # Verifica se registro já existe
            if self._record_exists(new_record):
                duplicated += 1
                continue

            # Adiciona novo registro
            self.df = pd.concat([self.df, pd.DataFrame([new_record])], ignore_index=True)
            added += 1

        # Garante que coluna 'data' é datetime após concatenações
        self.df['data'] = pd.to_datetime(self.df['data'], format='%d/%m/%Y', errors='coerce')

        # Ordena por data
        self.df = self.df.sort_values(['data', 'cidade', 'maquina']).reset_index(drop=True)

        return added, duplicated

    def _record_exists(self, record: Dict) -> bool:
        """Verifica se registro já existe (mesma data, cidade, máquina)"""
        if self.df.empty:
            return False

        # Garante que data é datetime
        if 'data' not in self.df.columns or not pd.api.types.is_datetime64_any_dtype(self.df['data']):
            return False

        matching = self.df[
            (self.df['data'].dt.strftime('%Y-%m-%d') == record['data'].strftime('%Y-%m-%d')) &
            (self.df['cidade'] == record['cidade']) &
            (self.df['maquina'] == record['maquina'])
        ]

        return len(matching) > 0

    def update_record(self, record: Dict) -> bool:
        """
        Atualiza um registro existente se os valores forem diferentes
        (para casos onde há correções nos dados)
        """
        # Encontra registro
        mask = (
            (self.df['data'].dt.strftime('%Y-%m-%d') == record['data'].strftime('%Y-%m-%d')) &
            (self.df['cidade'] == record['cidade']) &
            (self.df['maquina'] == record['maquina'])
        )

        if not mask.any():
            return False

        # Verifica se algo mudou
        existing = self.df[mask].iloc[0]
        if (existing['pelucias'] == record['pelucias'] and
            existing['valor'] == record['valor']):
            return False

        # Atualiza record
        self.df.loc[mask, 'pelucias'] = record['pelucias']
        self.df.loc[mask, 'valor'] = record['valor']
        self.df.loc[mask, 'media'] = record['media']
        self.df.loc[mask, 'data_atualizacao'] = datetime.now().strftime('%d/%m/%Y %H:%M')

        return True

    def save(self):
        """Salva banco de dados em Excel"""
        if self.df is None or self.df.empty:
            raise ValueError("Nenhum dado para salvar")

        # Prepara DataFrame para exportação
        export_df = self.df.copy()
        export_df['data'] = export_df['data'].dt.strftime('%d/%m/%Y')

        # Reordena colunas
        column_order = [
            'data', 'cidade', 'maquina',
            'pelucias', 'valor', 'media', 'data_atualizacao'
        ]
        export_df = export_df[column_order]

        # Exporta para Excel
        with pd.ExcelWriter(self.db_path, engine='openpyxl') as writer:
            export_df.to_excel(writer, sheet_name='Dados', index=False)
            self._apply_formatting(writer, export_df)

        return self.db_path

    def _apply_formatting(self, writer, df):
        """Aplica formatação ao Excel"""
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

        worksheet = writer.sheets['Dados']

        # Estilo do cabeçalho
        header_fill = PatternFill(start_color="2F5496", end_color="2F5496", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        # Estilo de borda
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        # Aplica formatação ao cabeçalho
        for col_num, column_title in enumerate(df.columns, 1):
            cell = worksheet.cell(row=1, column=col_num)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
            cell.border = thin_border

        # Aplica formatação às células
        for row in worksheet.iter_rows(min_row=2, max_row=worksheet.max_row, min_col=1, max_col=len(df.columns)):
            for cell in row:
                cell.border = thin_border
                cell.alignment = Alignment(horizontal="left", vertical="center")

        # Ajusta largura das colunas
        column_widths = {
            'A': 12,  # data
            'B': 18,  # cidade
            'C': 10,  # maquina
            'D': 10,  # pelucias
            'E': 12,  # valor
            'F': 10,  # media
            'G': 18,  # data_atualizacao
        }

        for col, width in column_widths.items():
            worksheet.column_dimensions[col].width = width

        # Formata colunas numéricas
        for row in worksheet.iter_rows(min_row=2, max_row=worksheet.max_row):
            # Valor (coluna E)
            if row[4].value is not None:
                row[4].number_format = '#,##0.00'
            # Média (coluna F)
            if row[5].value is not None:
                row[5].number_format = '0.00'

    def get_summary(self) -> Dict:
        """Retorna resumo do banco de dados"""
        if self.df is None or self.df.empty:
            return {}

        return {
            'total_registros': len(self.df),
            'cidades': self.df['cidade'].unique().tolist(),
            'maquinas_unicas': int(self.df['maquina'].nunique()),
            'data_inicio': self.df['data'].min().strftime('%d/%m/%Y'),
            'data_fim': self.df['data'].max().strftime('%d/%m/%Y'),
            'media_geral': self.df['media'].mean(),
            'valor_total': self.df['valor'].sum(),
            'ultima_atualizacao': self.df['data_atualizacao'].max() if 'data_atualizacao' in self.df.columns else 'N/A',
        }

    def get_dataframe(self) -> pd.DataFrame:
        """Retorna DataFrame do banco de dados"""
        return self.df
