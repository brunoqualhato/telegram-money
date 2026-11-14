# Frontend · Telegram Money

Painel em React 19, JavaScript e Vite. A integração React do Vite oferece transformação JSX automática e Fast Refresh. A interface existente está organizada por funcionalidade, com componentes compartilhados e lógica de coordenação em hooks.

## Desenvolvimento

Requisitos: Node.js 22.13+ e npm. Dentro de `frontend/`:

```bash
npm ci
npm run dev
```

O Vite escuta em `127.0.0.1:5173` e encaminha `/api` e `/health` para `127.0.0.1:8000`. Configure `APP_ORIGIN` no backend com a origem exata usada no navegador, conforme o README principal.

| Comando                | Finalidade                                    |
| ---------------------- | --------------------------------------------- |
| `npm run dev`          | Servidor local com Fast Refresh               |
| `npm run lint`         | ESLint sem avisos permitidos                  |
| `npm run lint:fix`     | Correções automáticas disponíveis no ESLint   |
| `npm run format`       | Formatar fontes e configuração                |
| `npm run format:check` | Verificar formatação                          |
| `npm test`             | Testes de API, renderização e limites do lint |
| `npm run build`        | Lint obrigatório e compilação para `dist/`    |
| `npm run check`        | Formatação, testes, lint e build              |
| `npm run preview`      | Servir o build localmente                     |

## Estrutura e padrão de projeto

A arquitetura usa organização por funcionalidades, composição de componentes e separação da coordenação de estado em hooks.

```text
src/
├── main.jsx                 # Montagem do React e importação dos estilos
├── app/
│   ├── App.jsx              # Estrutura principal
│   ├── PageContent.jsx      # Composição das telas
│   ├── AppDialogs.jsx       # Seleção dos formulários e confirmações
│   ├── useApp.js            # Estado da interface e ações
│   ├── usePanelData.js      # Sessão, consultas e atualização periódica
│   └── getPageInfo.js        # Busca, filtro e dados derivados
├── components/
│   ├── Logo.jsx
│   ├── layout/              # Sidebar e Header
│   └── ui/                  # Button, IconButton, Field, Badge, Empty,
│                            # Modal, ConfirmDialog e ErrorBox
├── features/
│   ├── auth/
│   ├── assets/
│   ├── alerts/
│   ├── documents/
│   ├── events/
│   ├── notifications/
│   ├── overview/
│   ├── reports/
│   ├── settings/
│   └── treasury/
├── lib/                     # Constantes e formatadores puros
├── services/api.js          # Cliente HTTP compartilhado
└── styles/global.css
```

O fluxo é `app → features → components/ui, lib, services`. A visão geral compõe componentes de ativos e notificações. As camadas compartilhadas não dependem das telas; essa fronteira é verificada pelo ESLint. Componentes recebem props e callbacks; os hooks da aplicação coordenam chamadas ao cliente HTTP. A navegação continua local ao painel, sem dependência de roteador.

Para acrescentar uma funcionalidade, crie seus componentes no domínio correspondente e faça a composição em `PageContent.jsx`. Extraia para `components/ui/` apenas o que já tem uso compartilhado e não depende do domínio. Coloque funções puras em `lib/` e chamadas HTTP no cliente compartilhado.

## Qualidade obrigatória

O arquivo `eslint.config.js` usa flat config e aplica as regras abaixo a JavaScript e JSX, incluindo configuração e testes:

| Regra                    | Limite                                           |
| ------------------------ | ------------------------------------------------ |
| `complexity`             | 10                                               |
| `max-lines-per-function` | 150 linhas, contando comentários e linhas vazias |
| `max-params`             | 5 parâmetros                                     |

Também são verificados hooks, dependências dos efeitos, imports e variáveis não utilizados. Comentários inline não podem desativar regras. `npm run build` executa lint antes de compilar, inclusive no Docker. Os testes exercitam os valores aceitos e rejeitados de cada limite.

As instruções para manutenção por agentes ficam em [AGENTS.md](AGENTS.md) e no [AGENTS.md da raiz](../AGENTS.md).
