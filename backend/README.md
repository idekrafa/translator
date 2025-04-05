# Tradutor de Livros - Backend

Backend para aplicação de tradução e diagramação de livros usando FastAPI e OpenAI GPT-4.

## Funcionalidades

- Tradução de capítulos de livro do inglês para diversos idiomas usando OpenAI GPT-4
- Formatação de texto traduzido em documentos DOCX e PDF
- Aplicação de layout específico (6x9 polegadas)
- Formatação com letra capitular (drop cap)
- Paginação adequada para impressão

## Requisitos

- Python 3.8+
- Dependências listadas em `requirements.txt`
- API key da OpenAI

## Instalação

1. Clone o repositório
2. Crie um ambiente virtual:
   ```
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   ```
3. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
4. Crie um arquivo `.env` baseado no `.env.example` e adicione sua API key da OpenAI:
   ```
   OPENAI_API_KEY=sua_api_key_aqui
   ```

## Executando a aplicação

```bash
python run.py
```

A aplicação estará disponível em http://localhost:8000. A documentação da API estará disponível em http://localhost:8000/docs.

## Estrutura do projeto

```
backend/
├── app/
│   ├── api/               # Rotas da API
│   ├── core/              # Configurações centrais
│   ├── models/            # Modelos de dados (Pydantic)
│   ├── services/          # Serviços de negócio
│   └── utils/             # Utilidades
├── output/                # Arquivos de saída
├── .env                   # Variáveis de ambiente
├── .env.example           # Exemplo de variáveis de ambiente
├── requirements.txt       # Dependências
└── run.py                 # Script para executar a aplicação
```

## API Endpoints

- `GET /` - Informações básicas sobre a API
- `POST /api/translation/translate` - Inicia um trabalho de tradução
- `GET /api/translation/status/{job_id}` - Verifica o status de um trabalho de tradução
- `GET /api/translation/download/{job_id}` - Baixa um livro traduzido 