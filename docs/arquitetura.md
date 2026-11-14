# Arquitetura do Telegram Money

Este documento descreve a arquitetura técnica do Telegram Money, os padrões de organização dos componentes, fluxos de dados, garantias de segurança e o plano de evolução do sistema.

---

## 1. Visão Geral e Princípios

O **Telegram Money** é uma solução de monitoramento patrimonial e cotações voltada para **uso estritamente pessoal** (single-owner). Os princípios orientadores da arquitetura são:

1. **Simplicidade e Propósito Claro**: Foco no investidor individual; não há multi-tenancy, cobrança, RBAC ou registro aberto de usuários.
2. **Modularidade por Domínio**: Separação clara de responsabilidades no backend (FastAPI com `APIRouter` e services isolados) e no frontend (React 19 organizado por `features/`).
3. **Privacidade e Soberania dos Dados**: Dados financeiros residem localmente ou sob infraestrutura própria; resumos de IA são processados localmente (LM Studio ou Ollama); sem telemetria ou analytics externos.
4. **Resiliência e Idempotência**: Coleta e entrega de notificações usam chaves de deduplicação e estado transacional persistente.
5. **Segurança por Padrão**: Proteção CSRF por validação de origem estrita, cookies de sessão `HttpOnly`/`SameSite=Strict`, senhas com salt e PBKDF2, e cabeçalhos de segurança (CSP, no-referrer, nosniff, frame-deny).

---

## 2. Visão de Contêineres e Processos

```mermaid
flowchart TD
    subgraph Browser ["Navegador Web"]
        SPA["Painel React 19 (Vite)"]
    end

    subgraph TelegramCloud ["Telegram"]
        BotUser["Chat Privado do Proprietário"]
    end

    subgraph LocalStack ["Stack de Serviços (Docker Compose / Local)"]
        API["FastAPI API (app.main)\n- Port 8000\n- APIRouters modulares\n- SPA Static Server"]
        Worker["Celery Worker\n(app.tasks)\n- Coleta de cotações\n- Processamento IA\n- Envio de notificações"]
        Beat["Celery Beat\n(app.tasks)\n- Agendamento de ticks\n- Coleta periódica"]
        Bot["Bot Process (app.bot)\n- aiogram 3 (Long Polling)\n- Comandos inline"]
        DB[("PostgreSQL 16 / SQLite\n- Dados cadastrais\n- Cotações e Fila de eventos")]
        RedisStore[("Redis 7\n- Broker de tarefas\n- Distributed Locks")]
    end

    subgraph External ["Gateways Externos"]
        Brapi["brapi.dev\n(Cotações B3 & Proventos)"]
        Tesouro["Tesouro Nacional\n(CSV oficial)"]
        LMStudio["LM Studio / Ollama\n(IA local OpenAI-compatible)"]
    end

    SPA -->|HTTP / API REST| API
    API --> DB
    API -.->|Despacho sob demanda| RedisStore
    Worker --> RedisStore
    Beat --> RedisStore
    Worker --> DB
    Worker --> Brapi
    Worker --> Tesouro
    Worker --> LMStudio
    Worker -->|HTTP Bot API| TelegramCloud
    Bot --> DB
    Bot <-->|Long Polling| TelegramCloud
    BotUser <--> TelegramCloud
```

### Componentes em Execução

| Componente | Tecnologia | Responsabilidade |
| --- | --- | --- |
| **API** | FastAPI (Python 3.12+), Uvicorn | Expõe endpoints REST modulares, valida sessões/origem e entrega arquivos estáticos compilados do frontend. |
| **Painel Web** | React 19, Vite, Vanilla CSS | Interface de usuário responsiva em pt-BR com navegação por abas e gestão do portfólio. |
| **Worker** | Celery com Redis | Executa tarefas demoradas em segundo plano (coleta de cotações, geração de relatórios, resumos de IA, entrega de mensagens). |
| **Beat** | Celery Beat | Disparador de agendamentos para o worker (quotes a cada N seg, notificações a cada 10s, Tesouro às 10h10/15h10). |
| **Bot** | aiogram 3 | Processo independente de polling com a API do Telegram; atende comandos rápidos (`/carteira`, `/cotacao`, etc.). |
| **Banco de Dados** | PostgreSQL 16 / SQLite WAL | Persistência relacional com SQLAlchemy 2.0 e versionamento com Alembic. |
| **Broker de Fila** | Redis 7 | Mensageria Celery e locks atômicos de concorrência. |

---

## 3. Arquitetura do Backend

A camada de backend foi estruturada segundo o padrão modular do FastAPI, separando claramente infraestrutura, rotas, regras de negócio e persistência.

```
backend/
├── app/
│   ├── main.py              # Ponto de entrada: lifespan, middlewares, montagem de rotas e estáticos
│   ├── auth.py              # Hash de senhas, sessões seguras e dependency injection de proprietário
│   ├── config.py            # Pydantic Settings com carregamento de variáveis de ambiente
│   ├── crud.py              # Utilitários de acesso a dados (rows, audit)
│   ├── db.py                # Engine SQLAlchemy 2.0, sessão local e hook PRAGMA SQLite
│   ├── models.py            # Entidades Declarative ORM mapeadas com Mapped[]
│   ├── schemas.py           # Contratos de entrada e validação Pydantic v2
│   ├── bot.py               # Bot aiogram e lógica de atendimento no Telegram
│   ├── tasks.py             # Definição e locks de tarefas Celery
│   ├── seed.py              # Dados mock para execução em DEMO_MODE
│   ├── cli.py               # Ferramentas administrativas de terminal (reset de senha, import-b3)
│   ├── routers/             # Submódulos modulares por domínio funcional
│   │   ├── auth.py          # /api/auth/login, /api/auth/logout, /api/me, /api/preferences
│   │   ├── portfolio.py     # /api/overview, /api/assets, importação B3 (/api/assets/import-b3), histórico
│   │   ├── rules.py         # /api/rules (CRUD e ativação/desativação)
│   │   ├── notifications.py # /api/notifications e reenvio manual
│   │   ├── events.py        # /api/events (proventos e fatos relevantes)
│   │   ├── documents.py     # /api/documents, upload de PDF e acionamento de resumos
│   │   ├── treasury.py      # /api/treasury (taxas do Tesouro Direto)
│   │   ├── reports.py       # /api/reports (relatórios de mercado sob demanda)
│   │   ├── integrations.py  # Conexão Telegram, teste de envio, verificação de IA
│   │   └── system.py        # /health, /api/setup, /api/audit
│   └── services/            # Serviços de domínio e clientes externos
│       ├── ai.py            # Integração local com LM Studio e Ollama
│       ├── alerts.py        # Avaliação de regras de disparo e deduplicação
│       ├── delivery.py      # Fila e envio de mensagens para o Telegram
│       ├── documents.py     # Extração de texto e orquestração de resumos
│       ├── events.py        # Upsert idempotente de eventos corporativos
│       ├── portfolio.py     # Consolidação patrimonial e parser de posição B3 (.xlsx/.csv)
│       ├── providers.py     # Clientes de coleta (brapi v2 e Tesouro CSV)
│       └── reports.py       # Montagem de relatórios formatados em texto
```

---

## 4. Arquitetura do Frontend

O frontend adota arquitetura modular por funcionalidades (**Feature-driven Architecture**) com controles estritos de qualidade:

- **src/features/**: Cada tela ou domínio funcional (`assets`, `alerts`, `documents`, `events`, `overview`, `reports`, `settings`, `treasury`, `notifications`) agrupa seus componentes, formulários e lógica especializada.
- **src/app/**: Orquestração geral da aplicação (`App.jsx`, `useApp.js`, `usePanelData.js`).
- **src/components/ui/**: Componentes de design system agnósticos a domínio (`Button`, `Modal`, `Badge`, `Field`, etc.).
- **src/services/api.js**: Cliente HTTP centralizado que cuida de CSRF headers, credenciais de cookies, tratamento de erro tipado e suporte a cancelamento por `AbortSignal`.
- **Limites de Engenharia**:
  - Complexidade ciclomática máxima: 10.
  - Linhas máximas por função: 150.
  - Parâmetros máximos por função: 5.
  - Zero warnings no ESLint e 100% de cobertura nos testes do painel.

---

## 5. Fluxos de Dados Críticos

### 5.1 Coleta de Mercado e Avaliação de Alertas

```mermaid
sequenceDiagram
    autonumber
    participant Beat as Celery Beat
    participant Worker as Celery Worker
    participant Brapi as brapi.dev
    participant DB as Banco de Dados
    participant Delivery as Worker (Delivery)
    participant TG as Telegram Bot API

    Beat->>Worker: Dispara market.poll (lock "quotes")
    Worker->>Brapi: GET /api/quote/{tickers}
    Brapi-->>Worker: Cotações atualizadas
    Worker->>DB: Persiste Quotes (deduplicação por quoted_at)
    Worker->>Worker: Avalia AlertRules ativas
    alt Condição satisfeita e regra desarmada
        Worker->>DB: Enfileira Notification (status="pending")
        Worker->>DB: Marca regra como triggered=True
    else Cotação retornou à normalidade
        Worker->>DB: Rearma regra (triggered=False)
    end
    Beat->>Delivery: Dispara notifications.deliver (lock "delivery")
    Delivery->>DB: Busca notificações com status="pending"
    Delivery->>Delivery: Valida preferências (silêncio, pausa, limite/hora)
    Delivery->>TG: POST /sendMessage
    TG-->>Delivery: 200 OK (message_id)
    Delivery->>DB: Atualiza status="sent", sent_at, message_id
```

### 5.2 Importação e Resumo com IA Local

```mermaid
sequenceDiagram
    autonumber
    participant User as Usuário (Painel)
    participant API as FastAPI Router
    participant DB as Banco de Dados
    participant Worker as Celery Worker
    participant LM as LM Studio / Ollama

    User->>API: POST /api/documents/pdf (multipart)
    API->>API: Extrai texto com PyMuPDF (max 10MB, 80 págs)
    API->>DB: Salva Document (status="pending", hash único)
    API-->>User: 201 Created (id, status)
    Worker->>DB: Busca Document pending
    Worker->>LM: POST /v1/chat/completions (json_schema)
    LM-->>Worker: JSON estruturado (facts, risks, missing)
    Worker->>Worker: Valida evidências literais no texto original
    alt Evidências válidas
        Worker->>DB: Salva summary, status="ready"
        Worker->>DB: Enfileira Notification para o Telegram
    else Evidências inválidas ou erro
        Worker->>DB: Marca status="failed", grava erro legível
    end
```

---

## 6. Garantias de Segurança

1. **Proteção contra Cross-Site Request Forgery (CSRF)**:
   - Todo request mutativo (`POST`, `PUT`, `PATCH`, `DELETE`) em rotas `/api/` é interceptado por middleware que verifica o header `Origin` contra `settings.app_origin`. Requisições de origens diferentes são bloqueadas com HTTP 403.
2. **Sessão Segura**:
   - Cookie `tm_session` é gravado com flags `HttpOnly`, `SameSite=Strict` e `Secure` (em produção com HTTPS). O token trafega apenas como cookie e seu hash SHA-256 é verificado na tabela `auth_sessions`.
3. **Proteção de Força Bruta**:
   - Janela deslizante de 15 minutos com bloqueio após 10 tentativas incorretas (`LoginAttempt`).
4. **Isolamento de Redes no Compose**:
   - `db` e `redis` não expõem portas no host. Somente a `api` expõe `127.0.0.1:8000`.

---

## 7. Próximos Passos de Evolução Arquitetural (Roadmap)

Embora a arquitetura atual seja robusta e modularizada, as seguintes evoluções estruturais podem ser consideradas para simplificação futura:

1. **Unificação do Runtime de Background (Async Tasks vs Celery/Redis)**:
   - *Cenário Atual*: Celery + Celery Beat + Redis adicionam 3 contêineres e ~500MB de RAM para 1 usuário.
   - *Evolução Possível*: Adotar um agendador assíncrono nativo em Python (`APScheduler` integrado com `asyncio` e background tasks do FastAPI), reduzindo a infraestrutura para apenas 1 ou 2 contêineres e eliminando completamente a dependência de Redis.
2. **Contratos Estritos de Saída (Pydantic Response Models)**:
   - Adicionar schemas `response_model` em cada rota dos routers para formalizar 100% dos retornos no OpenAPI / Swagger e eliminar a necessidade de `jsonable_encoder`.
3. **Revalidação Otimizada no Frontend**:
   - Substituir o polling fixo de 30s por revalidação orientada a foco de janela (`document.visibilityState`) e mutações bem-sucedidas.
