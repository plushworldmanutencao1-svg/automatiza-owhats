# Automatização WhatsApp → Sistema de Gruas 🤖

Processa conversas exportadas do WhatsApp para extrair dados de máquinas de forma automatizada e gera planilhas estruturadas para importação direto no sistema de gruas.

## 🎯 Funcionalidades

- ✅ Parse automático de arquivos TXT do WhatsApp
- ✅ Extração de dados essenciais (máquina, pelúcias, valor)
- ✅ **Cálculo automático de média** (Valor ÷ Pelúcias)
- ✅ Organização por semana e cidade
- ✅ Exportação em Excel com formatação
- ✅ Exportação em CSV para integração
- ✅ **SEM dependência de IA** - Lógica 100% determinística com Regex

## 📊 Dados Extraídos e Calculados

O programa extrai e organiza automaticamente:

| Campo | Descrição | Exemplo |
|-------|-----------|---------|
| `data` | Data do envio | 15/09/2026 |
| `cidade` | Cidade/Local | Lajeado - RS |
| `semana_mes` | Semana do mês | 3 |
| `maquina` | Número da máquina | 665 |
| `pelucias` | Quantidade de prêmios | 21 |
| `valor` | Faturamento semanal | 1.033,00 |
| **`media`** | **Média calculada (Valor ÷ Pelúcias)** | **49.19** |

## 🚀 Instalação

```bash
# Clone o repositório
git clone https://github.com/plushworldmanutencao1-svg/automatiza-owhats.git
cd automatiza-owhats

# Instale as dependências
pip install -r requirements.txt
```

## 📖 Como Usar

### Uso Básico

```bash
cd src
python main.py ../data/input/conversa.txt "Lajeado - RS"
```

Resultado: `dados_lajeado_rs.xlsx`

### Opções Avançadas

```bash
# Especificar arquivo de saída
python main.py dados.txt "Gravataí" --output resultado.xlsx

# Exportar em CSV
python main.py dados.txt "Porto Alegre" --format csv

# Exportar em ambos os formatos
python main.py dados.txt "Lajeado" --format both

# Modo verbose (detalhes do processamento)
python main.py dados.txt "Lajeado" --verbose

# Desativar formatação no Excel
python main.py dados.txt "Lajeado" --no-format
```

## 📁 Estrutura do Projeto

```
automatiza-owhats/
├── src/
│   ├── main.py           # Script principal
│   ├── parser.py         # Parser do WhatsApp
│   └── formatter.py      # Formatação de dados
├── data/
│   ├── input/            # 📥 Arquivos TXT do WhatsApp
│   └── output/           # 📤 Planilhas geradas
├── tests/                # Testes unitários
├── requirements.txt      # Dependências Python
├── .env.example          # Configurações
└── README.md            # Este arquivo
```

## 📝 Formato do Arquivo WhatsApp

Coloque seus arquivos TXT exportados do WhatsApp na pasta `data/input/`:

O programa reconhece automaticamente padrões como:

```
*Black* (665) A7 em 30
*Pelúcias:* 21
*R$* 1.033
```

## 🔄 Fluxo de Processamento

```
Arquivo TXT (WhatsApp)
         ↓
    [PARSER] → Extrai: Máquina, Pelúcias, Valor
         ↓
    [FORMATTER] → Calcula: Média = Valor ÷ Pelúcias
         ↓
    [EXPORT] → Excel com formatação
         ↓
    [IMPORTAR] → Sistema de Gruas
```

## 📊 Exemplo de Saída

A planilha gerada tem este formato:

| Data | Cidade | Semana | Máquina | Pelúcias | Valor | **Média** |
|------|--------|--------|---------|----------|-------|-----------|
| 01/09/2026 | Lajeado - RS | 1 | 665 | 21 | 1.033,00 | **49.19** |
| 01/09/2026 | Lajeado - RS | 1 | 666 | 17 | 1.910,00 | **112.35** |
| 08/09/2026 | Lajeado - RS | 2 | 665 | 24 | 901,00 | **37.54** |

## ✅ Validação

O programa valida automaticamente:

- ✓ Arquivo de entrada existe
- ✓ Dados extraídos corretamente
- ✓ Formatação de números (português/Brasil)
- ✓ Cálculo de média (previne divisão por zero)

## 🔧 Troubleshooting

### Erro: Nenhum dado encontrado

Verifique se:
- O arquivo está em formato TXT
- Contém linhas com máquinas (Black ou Big)
- Contém dados de "Pelúcias:" e "R$"
- Está no encoding UTF-8

### Números não estão sendo extraídos

O programa reconhece:
- Formato português: `1.234,56` → `1234.56`
- Formato simples: `1,5` → `1.5`
- Valor vazio ou `XXX` → Ignora o registro

## 🛠️ Desenvolvimento

### Testar o parser

```python
from src.parser import WhatsAppParser

parser = WhatsAppParser("Lajeado - RS")
records = parser.parse_file("data/input/conversa.txt")
print(records)
```

### Testar o formatter

```python
from src.parser import WhatsAppParser
from src.formatter import DataFormatter

parser = WhatsAppParser("Lajeado - RS")
records = parser.parse_file("data/input/conversa.txt")

formatter = DataFormatter()
df = formatter.process_records(records)
print(df.head())
```

## 📅 Cronograma Esperado

- **Sábado**: Operadores enviam conversas com dados da semana
- **Segunda**: Operadores de outros locais podem enviar dados atrasados
- **Processamento**: Execute o script para gerar planilha atualizada
- **Importação**: Importe no sistema de gruas

## 🔐 Segurança

- Nenhuma informação é enviada para servidores externos
- Processamento 100% local
- Sem dependência de APIs externas ou IA
- Sem análise de linguagem natural

## 📞 Próximas Etapas

- [ ] Integração direta com API do sistema de gruas
- [ ] Dashboard de acompanhamento de médias
- [ ] Alertas automáticos para máquinas com problemas
- [ ] Histórico consolidado de performance
- [ ] Processamento em lote de múltiplos arquivos

## 📄 Licença

Desenvolvido para Plush World - Sistema de Gruas
