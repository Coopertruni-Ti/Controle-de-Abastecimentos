#!/bin/bash

echo "🚀 Dashboard de Abastecimentos - Script de Inicialização"
echo "========================================================="
echo ""

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Por favor, instale Python 3.8+"
    exit 1
fi

echo "✅ Python 3 encontrado: $(python3 --version)"
echo ""

# Verificar se requirements estão instalados
echo "📦 Verificando dependências..."
if ! python3 -c "import streamlit" &> /dev/null; then
    echo "⚠️  Streamlit não encontrado. Instalando dependências..."
    pip3 install -r requirements.txt
else
    echo "✅ Dependências já instaladas"
fi

echo ""

# Verificar se credenciais existem
if [ ! -f "google_creds.json" ]; then
    echo "❌ Arquivo google_creds.json não encontrado!"
    echo "   Por favor, adicione suas credenciais do Google Sheets"
    exit 1
fi

echo "✅ Credenciais encontradas"
echo ""

# Iniciar o dashboard
echo "🚀 Iniciando Dashboard..."
echo "   Acesse: http://localhost:8501"
echo ""
streamlit run app.py
