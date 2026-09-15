#!/usr/bin/env python3
"""
API de Importação - WhatsApp → Banco de Dados
Processa conversas do WhatsApp e armazena automaticamente
"""

from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
import sys

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from parser import WhatsAppParser
from formatter import DataFormatter
from database import DatabaseManager
from sync_gruas import sincronizar, GruasSyncError

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db_path = 'dados_consolidados.xlsx'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/processar', methods=['POST'])
def processar():
    """Processa arquivo e armazena no banco de dados automaticamente"""
    try:
        if 'arquivo' not in request.files:
            return jsonify({'erro': 'Nenhum arquivo enviado'}), 400

        arquivo = request.files['arquivo']
        cidade = request.form.get('cidade', 'Sem Cidade')

        if not arquivo or arquivo.filename == '':
            return jsonify({'erro': 'Arquivo vazio'}), 400

        if not arquivo.filename.endswith('.txt'):
            return jsonify({'erro': 'Apenas .txt aceitos'}), 400

        # Salva temporariamente
        filename = secure_filename(arquivo.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        arquivo.save(temp_path)

        # Parse
        parser = WhatsAppParser(cidade)
        records = parser.parse_file(temp_path)

        if not records:
            os.remove(temp_path)
            return jsonify({'erro': 'Nenhum dado encontrado'}), 400

        # Formata
        formatter = DataFormatter()
        df = formatter.process_records(records)

        # Armazena no banco
        db = DatabaseManager(db_path)
        added, duplicated = db.add_records(df.to_dict('records'))
        db.save()

        os.remove(temp_path)

        return jsonify({
            'sucesso': True,
            'adicionados': added,
            'duplicados': duplicated,
            'total': len(db.get_dataframe()),
            'resumo': db.get_summary()
        })

    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/api/sincronizar', methods=['POST'])
def sincronizar_gruas():
    """Envia os totais semanais consolidados pro sistema de gruas"""
    try:
        if not os.path.exists(db_path):
            return jsonify({'erro': 'Nenhum dado para sincronizar ainda'}), 400

        db = DatabaseManager(db_path)
        resultado = sincronizar(db.get_dataframe())
        return jsonify(resultado)

    except GruasSyncError as e:
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/api/status')
def status():
    """Status atual do banco de dados"""
    try:
        if not os.path.exists(db_path):
            return jsonify({
                'existe': False,
                'registros': 0,
                'cidades': [],
                'ultima_atualizacao': '-'
            })

        db = DatabaseManager(db_path)
        summary = db.get_summary()

        return jsonify({
            'existe': True,
            'registros': summary['total_registros'],
            'cidades': summary['cidades'],
            'ultima_atualizacao': summary['ultima_atualizacao']
        })
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 Servidor: http://localhost:5000")
    print("📱 Arraste arquivos .txt do WhatsApp - cidade extraída automaticamente")
    print("="*70 + "\n")
    app.run(debug=True, port=5000, host='127.0.0.1')
