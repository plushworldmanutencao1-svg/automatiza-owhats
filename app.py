#!/usr/bin/env python3
"""
Aplicação Web - Automatização WhatsApp → Sistema de Gruas
Interface gráfica simples para processar conversas do WhatsApp
"""

from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
import os
import sys
from pathlib import Path

# Adiciona pasta src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from parser import WhatsAppParser
from formatter import DataFormatter
from database import DatabaseManager

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Cria pasta de uploads se não existir
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Banco de dados global
db_path = 'dados_consolidados.xlsx'

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/api/processar', methods=['POST'])
def processar():
    """API para processar arquivo"""
    try:
        # Verifica arquivo
        if 'arquivo' not in request.files:
            return jsonify({'erro': 'Nenhum arquivo enviado'}), 400

        arquivo = request.files['arquivo']
        cidade = request.form.get('cidade', 'Sem Cidade')

        if not arquivo or arquivo.filename == '':
            return jsonify({'erro': 'Arquivo vazio'}), 400

        if not arquivo.filename.endswith('.txt'):
            return jsonify({'erro': 'Apenas arquivos .txt são aceitos'}), 400

        # Salva arquivo temporário
        filename = secure_filename(arquivo.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        arquivo.save(temp_path)

        # Processa arquivo
        parser = WhatsAppParser(cidade)
        records = parser.parse_file(temp_path)

        if not records:
            os.remove(temp_path)
            return jsonify({'erro': 'Nenhum dado encontrado no arquivo'}), 400

        # Formata dados
        formatter = DataFormatter()
        df = formatter.process_records(records)

        # Adiciona ao banco de dados
        db = DatabaseManager(db_path)
        added, duplicated = db.add_records(df.to_dict('records'))
        db.save()

        # Remove arquivo temporário
        os.remove(temp_path)

        # Retorna resultado
        return jsonify({
            'sucesso': True,
            'adicionados': added,
            'duplicados': duplicated,
            'total': len(db.get_dataframe()),
            'resumo': db.get_summary()
        })

    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/api/download')
def download():
    """API para baixar planilha"""
    try:
        if not os.path.exists(db_path):
            return jsonify({'erro': 'Nenhum dado disponível ainda'}), 404

        return send_file(
            db_path,
            as_attachment=True,
            download_name='dados_consolidados.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/api/status')
def status():
    """API para obter status do banco de dados"""
    try:
        if not os.path.exists(db_path):
            return jsonify({
                'existe': False,
                'registros': 0,
                'cidades': []
            })

        db = DatabaseManager(db_path)
        summary = db.get_summary()

        return jsonify({
            'existe': True,
            'registros': summary['total_registros'],
            'cidades': summary['cidades'],
            'maquinas': summary['maquinas_unicas'],
            'periodo': f"{summary['data_inicio']} a {summary['data_fim']}",
            'ultima_atualizacao': summary['ultima_atualizacao']
        })
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Servidor rodando em: http://localhost:5000")
    print("="*60)
    print("Abra este link no navegador para usar!")
    print("="*60 + "\n")
    app.run(debug=True, port=5000)
