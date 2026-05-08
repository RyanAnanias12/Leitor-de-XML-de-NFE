# Analisador NF-e

Sistema local para leitura e análise de XMLs de NF-e em pastas e subpastas.

## Instalação (uma única vez)

```
pip install flask
```

## Como usar

1. Execute `iniciar.bat` (ou `python app.py`)
2. Abra o navegador em: http://localhost:5000
3. Cole o caminho da pasta (ex: `C:\Users\suporte\OneDrive - USER\Área de Trabalho\NOVEMBRO-2019`)
4. Clique em **Escanear XMLs**
5. Selecione qualquer nota para ver os detalhes

## O que é exibido por nota

- Emitente e destinatário completos
- Chave e protocolo de autorização
- Todos os valores: NF, produtos, ICMS, ICMS-ST, PIS, COFINS
- Itens com código, descrição, NCM, CFOP, quantidade e valores
- Transporte e forma de pagamento

## Visão geral (dashboard)

Ao carregar a pasta, aparece automaticamente:
- Faturamento total e por nota
- Breakdown tributário (ICMS + ST + PIS + COFINS)
- Destinos por UF (ranking)

## Filtros disponíveis

- Busca por texto (destinatário, NF, CNPJ, arquivo)
- Filtro por UF do destinatário
- Ordenação por data, valor ou número da NF
