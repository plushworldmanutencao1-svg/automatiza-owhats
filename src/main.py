#!/usr/bin/env python3
"""
Automatização WhatsApp → Sistema de Gruas

Processa conversas exportadas do WhatsApp para extrair dados de máquinas
e gerar planilha estruturada para importação no sistema de gruas.
"""

import os
import sys
import argparse
from pathlib import Path
from parser import WhatsAppParser
from formatter import DataFormatter

def main():
    parser = argparse.ArgumentParser(
        description='Processa conversas do WhatsApp para sistema de gruas',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python main.py dados.txt "Lajeado - RS"
  python main.py dados.txt "Gravataí" --output resultado.xlsx
  python main.py dados.txt "Porto Alegre" --format csv
        """
    )

    parser.add_argument('input', help='Arquivo TXT exportado do WhatsApp')
    parser.add_argument('city', help='Nome da cidade/local')
    parser.add_argument(
        '--output', '-o',
        help='Arquivo de saída (padrão: dados_<cidade>.xlsx)',
        default=None
    )
    parser.add_argument(
        '--format', '-f',
        choices=['excel', 'csv', 'both'],
        default='excel',
        help='Formato de saída (padrão: excel)'
    )
    parser.add_argument(
        '--no-format',
        action='store_true',
        help='Desativa formatação no Excel'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Modo verbose (mostra detalhes do processamento)'
    )

    args = parser.parse_args()

    # Valida arquivo de entrada
    if not os.path.exists(args.input):
        print(f"❌ Erro: Arquivo '{args.input}' não encontrado", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        print(f"📂 Processando: {args.input}")
        print(f"🏙️  Cidade: {args.city}")

    try:
        # Parse do arquivo
        print("🔍 Extractando dados...")
        whatsapp_parser = WhatsAppParser(args.city)
        records = whatsapp_parser.parse_file(args.input)

        if not records:
            print("⚠️  Nenhum dado de máquina encontrado no arquivo", file=sys.stderr)
            sys.exit(1)

        if args.verbose:
            print(f"✅ {len(records)} registros encontrados")

        # Formatação dos dados
        print("📊 Organizando dados...")
        formatter = DataFormatter()
        df = formatter.process_records(records)

        # Define arquivo de saída
        if args.output:
            output_file = args.output
        else:
            city_clean = args.city.replace(' ', '_').replace('-', '').lower()
            output_file = f"dados_{city_clean}.xlsx"

        # Exporta dados
        if args.format in ['excel', 'both']:
            print(f"💾 Exportando Excel: {output_file}")
            formatter.export_excel(
                output_file,
                include_formatacao=not args.no_format
            )

        if args.format in ['csv', 'both']:
            csv_file = output_file.replace('.xlsx', '.csv')
            print(f"💾 Exportando CSV: {csv_file}")
            formatter.export_csv(csv_file)

        # Mostra resumo
        summary = formatter.get_summary()
        print("\n" + "="*50)
        print("📈 RESUMO DOS DADOS")
        print("="*50)
        print(f"Total de registros: {summary['total_registros']}")
        print(f"Cidades: {', '.join(summary['cidades'])}")
        print(f"Máquinas únicas: {len(summary['maquinas_unicas'])}")
        print(f"Período: {summary['data_inicio']} a {summary['data_fim']}")
        print(f"Média geral: {summary['media_geral']:.2f}")
        print("="*50)

        print(f"\n✅ Processamento concluído com sucesso!")
        print(f"📁 Arquivo salvo: {output_file}")

    except Exception as e:
        print(f"❌ Erro ao processar: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
