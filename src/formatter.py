import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
import os

class DataFormatter:
    """Formata dados extraídos do WhatsApp para banco de dados"""

    def __init__(self):
        self.df = None

    def process_records(self, records: List[Dict]) -> pd.DataFrame:
        """Processa registros e organiza em estrutura de banco de dados"""

        if not records:
            raise ValueError("Nenhum registro para processar")

        # Converte para DataFrame
        self.df = pd.DataFrame(records)

        # Converte datas
        self.df['data'] = pd.to_datetime(self.df['data'], format='%d/%m/%Y')


        # Calcula a média: valor / pelúcias
        self.df['media'] = self.df.apply(
            lambda row: row['valor'] / row['pelucias'] if row['pelucias'] > 0 else 0,
            axis=1
        )

        # Ordena por data e máquina
        self.df = self.df.sort_values(['data', 'maquina'])

        # Reordena colunas para o banco de dados
        self.df = self._reorganize_columns()

        return self.df

    def _reorganize_columns(self) -> pd.DataFrame:
        """Reorganiza colunas na ordem esperada pelo sistema de gruas"""

        column_order = [
            'data',
            'cidade',
            'maquina',
            'pelucias',
            'valor',
            'media',
        ]

        # Garante que todas as colunas existem
        for col in column_order:
            if col not in self.df.columns:
                self.df[col] = None

        return self.df[column_order]

    def get_dataframe(self) -> pd.DataFrame:
        """Retorna DataFrame processado"""
        return self.df

    def export_excel(self, filepath: str, include_formatacao: bool = True):
        """Exporta dados para Excel com formatação"""

        if self.df is None:
            raise ValueError("Nenhum dado processado. Execute process_records() primeiro.")

        # Cria DataFrame para exportação
        export_df = self.df.copy()
        export_df['data'] = export_df['data'].dt.strftime('%d/%m/%Y')

        # Exporta para Excel
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            export_df.to_excel(writer, sheet_name='Dados', index=False)

            if include_formatacao:
                self._apply_formatting(writer, export_df)

        return filepath

    def _apply_formatting(self, writer, df):
        """Aplica formatação ao Excel"""
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

        worksheet = writer.sheets['Dados']

        # Estilo do cabeçalho
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
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
            'C': 12,  # semana_mes
            'D': 10,  # maquina
            'E': 10,  # pelucias
            'F': 14,  # valor
            'G': 10,  # media
        }

        for col, width in column_widths.items():
            worksheet.column_dimensions[col].width = width

        # Formata colunas numéricas
        for row in worksheet.iter_rows(min_row=2, max_row=worksheet.max_row):
            # Valor (coluna F)
            if row[5].value is not None:
                row[5].number_format = '#,##0.00'
            # Média (coluna G)
            if row[6].value is not None:
                row[6].number_format = '0.00'

    def export_csv(self, filepath: str):
        """Exporta dados para CSV"""

        if self.df is None:
            raise ValueError("Nenhum dado processado. Execute process_records() primeiro.")

        export_df = self.df.copy()
        export_df['data'] = export_df['data'].dt.strftime('%d/%m/%Y')
        export_df.to_csv(filepath, index=False, encoding='utf-8', sep=';')

        return filepath

    def get_summary(self) -> Dict:
        """Retorna resumo dos dados"""

        if self.df is None:
            return {}

        return {
            'total_registros': len(self.df),
            'cidades': self.df['cidade'].unique().tolist(),
            'maquinas_unicas': self.df['maquina'].unique().tolist(),
            'data_inicio': self.df['data'].min().strftime('%d/%m/%Y'),
            'data_fim': self.df['data'].max().strftime('%d/%m/%Y'),
            'media_geral': self.df['media'].mean(),
            'valor_total': self.df['valor'].sum(),
            'pelucias_total': self.df['pelucias'].sum(),
        }
