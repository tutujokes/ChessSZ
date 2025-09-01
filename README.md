# Chessify

Monorepo para análise de partidas de xadrez.

## Estrutura
- `frontend/`: Next.js + TypeScript
- `backend/`: FastAPI + Python

## Como iniciar

### Frontend
```bash
cd frontend
npm run dev
```

### Backend
```bash
cd backend
venv\Scripts\activate
uvicorn main:app --reload
```

## Funcionalidades
- Análise de partidas via PGN/FEN
- Classificação de lances (bom, ótimo, erro, etc.)
- Suporte a português e espanhol
- Interface responsiva

## Requisitos
- Node.js
- Python 3.11+

## Licença
MIT
