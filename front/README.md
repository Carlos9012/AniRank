# AniRank — Frontend

Interface em React (Vite) para o backend do AniRank.

## Conceito visual

O elemento-assinatura é um selo circular vermelho estilo **hanko** (carimbo
japonês usado para autenticar documentos), aplicado sobre a nota de cada
anime — ligando visualmente a ideia de "avaliar/carimbar" ao nome "AniRank".
Fundo índigo escuro (não preto puro), tipografia condensada (Bebas Neue) para
títulos, Inter para corpo, JetBrains Mono para dados numéricos.

## Setup

```powershell
cd frontend
npm install

copy .env.example .env
# edite .env se seu backend não estiver em http://localhost:8000
```

## Rodar

```powershell
npm run dev
```

Acessa `http://localhost:5173`. **O backend precisa estar rodando** (`uvicorn app.main:app --reload`) — o frontend não funciona sozinho, ele só consome a API.

## Estrutura

```
src/
├── api/              # um arquivo por domínio (auth, animes, list, recommendations)
├── components/       # Navbar, AnimeCard, ScoreBadge, EmptyState, ProtectedRoute
├── context/          # AuthContext — guarda o usuário logado e o token
├── pages/            # uma página por rota
└── styles/           # tokens.css (design system) + global.css
```

## Páginas

| Rota | Página | Endpoint(s) consumido(s) |
|---|---|---|
| `/login`, `/register` | Autenticação | `/auth/login`, `/auth/register`, `/auth/me` |
| `/` | Catálogo + busca AniList | `/animes`, `/animes/search`, `/animes/import/{id}` |
| `/anime/:id` | Detalhe + similares | `/animes/{id}`, `/recommendations/by-anime/{id}`, `/list` |
| `/my-list` | Lista pessoal | `/list` |
| `/discover` | Busca por descrição | `/recommendations/by-description` |
| `/for-you` | Recomendação personalizada | `/recommendations/personalized` |

## Autenticação

O token JWT fica em `localStorage` (`anirank_token`) e é anexado automaticamente
em toda requisição via interceptor do axios (`src/api/client.js`). Se o backend
retornar 401, a sessão local é limpa.

## O que ainda não está aqui, de propósito

- Sem testes automatizados
- Sem tratamento de erro refinado por endpoint (mensagens genéricas em alguns casos)
- Sem paginação infinita — usa paginação por página simples
- Sem dark/light mode toggle — o design é escuro por padrão, coerente com o conceito

Esses são candidatos naturais de próxima iteração, não esquecimentos.
