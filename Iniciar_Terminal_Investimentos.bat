@echo off
title Hub Agregador 360 de Portfolio & Screener Quantitativo Forense
cd /d "%~dp0"
echo ===============================================================================
echo    INICIANDO HUB AGREGADOR 360 DE PORTFOLIO E SCREENER QUANTITATIVO FORENSE
echo ===============================================================================
echo Carregando os 6 Modulos Centrais (Macro, Equity, Crypto, Filings, Geopolitica, Screener e Risco)...
echo O painel interativo e o exportador do Relatorio Master Completo (.pdf) abrirao no seu navegador.
echo.
python -m streamlit run app.py --server.headless=false
pause
