#!/usr/bin/env python3
"""
Automatização WhatsApp → Sistema de Gruas

Processa conversas exportadas do WhatsApp para extrair dados de máquinas
e gerar planilha estruturada para importação no sistema de gruas.

Suporta múltiplos arquivos (múltiplas cidades) com consolidação automática
e detecção de duplicatas.
"""

import os
import sys
import argparse
from pathlib import Path
from parser import WhatsAppParser
from formatter import DataFormatter
from database import DatabaseManager

def process_single_file(input_path: str, city: str, verbose: bool = False):
    """Processa um único arquivo e retorna records"""

    if verbose:
        print(f"📂 Processando: {input_path}")
        print(f"🏙️  Cidade: {city}")

    # Parse do arquivo
    print("🔍 Extractando dados...")
    whatsapp_parser = WhatsAppParser(city)
    records = whatsapp_parser.parse_file(input_path)

    if not records:
        print(f"⚠️  Nenhum dado encontrado em {input_path}")
        return []

    if verbose:
        print(f"✅ {len(records)} registros encontrados")

    # Formatação dos dados
    formatter = DataFormatter()
    df = formatter.process_records(records)

    # Converte de volta para records (com média calculada)
    return df.to_dict('records')

def main():
    parser = argparse.ArgumentParser(
        description='Processa conversas do WhatsApp para sistema de gruas',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso ÚNICO arquivo:
  python main.py dados.txt
  python main.py dados.txt "Lajeado - RS"

Exemplos de MÚLTIPLOS arquivos (consolidado):
  python main.py dados1.txt "Lajeado" dados2.txt "Gravataí" dados3.txt "Porto Alegre"
        """
    )

    parser.add_argument(
        'input',
        nargs='+',
        help='Arquivo(s) TXT'
    )
    parser.add_argument(
        '--output', '-o',
        default='dados_consolidados.xlsx',
        help='Arquivo de saída (padrão: dados_consolidados.xlsx)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Modo verbose (mostra detalhes)'
    )

    args = parser.parse_args()

    try:
        # Detecta modo de operação pelo número de argumentos
        if len(args.input) == 1:
            # Modo único arquivo (sem cidade)
            input_file = args.input[0]
            city = "Sem Cidade"

            if not os.path.exists(input_file):
                print(f"❌ Erro: Arquivo '{input_file}' não encontrado")
                sys.exit(1)

            process_single(input_file, city, args.output, args.verbose)

        elif len(args.input) == 2 and os.path.exists(args.input[0]) and not os.path.exists(args.input[1]):
            # Modo único arquivo + cidade
            input_file = args.input[0]
            city = args.input[1]

            if not os.path.exists(input_file):
                print(f"❌ Erro: Arquivo '{input_file}' não encontrado")
                sys.exit(1)

            process_single(input_file, city, args.output, args.verbose)

        else:
            # Modo múltiplos arquivos: arquivo1 "Cidade1" arquivo2 "Cidade2" ...
            if len(args.input) % 2 != 0:
                print("❌ Erro: Modo múltiplos arquivos precisa de pares arquivo+cidade")
                print("   Exemplo: python main.py arquivo1.txt \"Cidade1\" arquivo2.txt \"Cidade2\"")
                sys.exit(1)

            files_and_cities = []
            for i in range(0, len(args.input), 2):
                files_and_cities.append((args.input[i], args.input[i + 1]))

            process_multiple(files_and_cities, args.output, args.verbose)

    except Exception as e:
        print(f"❌ Erro: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

def process_single(input_path: str, city: str, output_path: str, verbose: bool):
    """Processa um único arquivo e gera Excel"""

    records = process_single_file(input_path, city, verbose)
    if not records:
        sys.exit(1)

    # Exporta direto
    db = DatabaseManager(output_path)
    db.add_records(records)
    db.save()

    summary = db.get_summary()
    print("\n" + "="*60)
    print("📈 RESUMO DOS DADOS")
    print("="*60)
    print(f"Cidade: {city}")
    print(f"Total de registros: {summary['total_registros']}")
    print(f"Máquinas únicas: {summary['maquinas_unicas']}")
    print(f"Período: {summary['data_inicio']} a {summary['data_fim']}")
    print(f"Média geral: {summary['media_geral']:.2f}")
    print("="*60)

    print(f"\n✅ Processamento concluído!")
    print(f"📁 Arquivo salvo: {output_path}")

def process_multiple(files_and_cities: list, output_path: str, verbose: bool):
    """Processa múltiplos arquivos e consolida em um banco de dados"""

    print("🔄 MODO CONSOLIDADO - Múltiplos Arquivos/Cidades\n")

    # Carrega banco de dados
    db = DatabaseManager(output_path)

    total_added = 0
    total_duplicated = 0

    for input_path, city in files_and_cities:
        if not os.path.exists(input_path):
            print(f"⚠️  Arquivo não encontrado: {input_path}")
            continue

        print(f"\n📂 Processando: {input_path} ({city})")
        records = process_single_file(input_path, city, verbose=False)

        if not records:
            continue

        # Adiciona ao banco de dados
        added, duplicated = db.add_records(records)
        print(f"   ✅ Adicionados: {added} | ⚠️  Duplicados: {duplicated}")

        total_added += added
        total_duplicated += duplicated

    # Salva banco de dados consolidado
    print(f"\n💾 Salvando banco de dados consolidado...")
    db.save()

    # Resumo final
    summary = db.get_summary()
    print("\n" + "="*60)
    print("📊 BANCO DE DADOS CONSOLIDADO")
    print("="*60)
    print(f"Total de registros: {summary['total_registros']}")
    print(f"Cidades: {', '.join(summary['cidades'])}")
    print(f"Máquinas únicas: {summary['maquinas_unicas']}")
    print(f"Período: {summary['data_inicio']} a {summary['data_fim']}")
    print(f"Média geral: {summary['media_geral']:.2f}")
    print(f"Valor total: R$ {summary['valor_total']:,.2f}")
    print(f"Última atualização: {summary['ultima_atualizacao']}")
    print("="*60)

    print(f"\n✅ Consolidação concluída!")
    print(f"📁 Banco de dados: {output_path}")
    print(f"   Adicionados nesta execução: {total_added}")
    print(f"   Duplicados não adicionados: {total_duplicated}")

if __name__ == '__main__':
    main()
