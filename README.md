# Tradutor de Livros

Aplicação para tradução e diagramação de textos de livros, utilizando GPT-4 para tradução e formatação específica para impressão.

## Funcionalidades

- Tradução de textos do inglês para diversos idiomas usando GPT-4
- Formatação em layout de livro 6x9 polegadas
- Letra capitular no início dos capítulos
- Paginação estilo livro de capa dura
- Geração de documentos em formato DOCX e PDF
- Interface web amigável

## Estrutura do Projeto

O projeto é dividido em duas partes principais:

- **Backend**: API desenvolvida em Python com FastAPI
- **Frontend**: Interface de usuário desenvolvida com React, TypeScript e Tailwind CSS

## Requisitos

- Python 3.8+
- Node.js 18+
- API key da OpenAI
- Docker e Docker Compose (opcional, para implantação com contêineres)

## Instalação

### Configuração do Backend

1. Navegue até a pasta `backend`:
   ```bash
   cd backend
   ```

2. Crie um ambiente virtual Python:
   ```bash
   python -m venv venv
   source venv/bin/activate   # No Windows: venv\Scripts\activate
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Crie um arquivo `.env` com sua API key da OpenAI:
   ```
   OPENAI_API_KEY=seu_api_key_aqui
   ```

### Configuração do Frontend

1. Navegue até a pasta `frontend`:
   ```bash
   cd frontend
   ```

2. Instale as dependências:
   ```bash
   npm install
   ```

## Execução

### Desenvolvimento

1. Inicie o backend:
   ```bash
   cd backend
   ./dev.sh
   ```

2. Em outro terminal, inicie o frontend:
   ```bash
   cd frontend
   npm run dev
   ```

3. Acesse a aplicação em http://localhost:5173

### Com Docker Compose

1. Configure sua API key da OpenAI no ambiente:
   ```bash
   export OPENAI_API_KEY=seu_api_key_aqui
   ```

2. Inicie os serviços:
   ```bash
   docker-compose up -d
   ```

3. Acesse a aplicação em http://localhost:3000

## Uso

1. Na tela inicial, configure o idioma de destino e o número de capítulos
2. Para cada capítulo, insira o conteúdo em inglês (até 10 páginas por capítulo)
3. Após finalizar, o sistema irá processar os textos, traduzir e formatar
4. Ao finalizar, você poderá baixar o documento formatado

## Especificações Técnicas

- **Tamanho de página**: 6 x 9 polegadas
- **Fonte**: Georgia, tamanho 11
- **Letra capitular**: Primeira letra do capítulo em destaque
- **Número do capítulo**: Tamanho 30, posicionado à direita
- **Paginação**: Números à esquerda em páginas pares e à direita em páginas ímpares

## Limitações

- Processamento de no máximo 10 páginas por capítulo
- Tempo de processamento proporcional ao tamanho do texto
- Requer conexão com a internet para acessar a API do OpenAI
