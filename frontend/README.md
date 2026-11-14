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
│                            # Modal, ConfirmDialog, ErrorBox, gráficos e paginação
├── features/
│   ├── auth/
│   ├── assets/
│   ├── alerts/
│   ├── documents/
│   ├── events/
│   ├── notifications/
│   ├── overview/            # Dashboard e cálculos da carteira
│   ├── queue/               # Fila de IA e limites de recursos
│   ├── reports/
│   ├── settings/
│   └── treasury/
├── lib/                     # Constantes e formatadores puros
├── services/api.js          # Cliente HTTP compartilhado
└── styles/
    ├── global.css           # Layout e componentes do painel
    └── dashboard.css        # Composição visual da dashboard
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

## Indicadores da dashboard

A visão geral combina evolução patrimonial, alocação por classe, concentração nos maiores ativos, contribuição diária e resultado por posição. Os cálculos ficam em `features/overview/portfolioMetrics.js`, sem bibliotecas de gráficos adicionais. Posições zeradas e valores sem cotação em BRL não entram nos totais; preços médios ausentes são excluídos do resultado e identificados na cobertura dos dados.

A variação diária consolidada usa o patrimônio anterior implícito na variação de cada cotação, em vez de uma média simples de percentuais. Os históricos têm eixos temporais, referência de custo e consulta por mouse ou pelo controle de teclado. São estimativas com as quantidades atuais, sem reconstruir operações, proventos ou taxas. O estilo da dashboard está em `styles/dashboard.css`.

## Componentes e dados da dashboard

| Área               | Implementação                                                                                   |
| ------------------ | ----------------------------------------------------------------------------------------------- |
| Composição         | `Overview.jsx` organiza indicadores, gráficos, maiores posições, últimos sinais e cobertura     |
| Indicadores        | `OverviewStats.jsx`: patrimônio, custo, resultado, variação diária e contagens                  |
| Evolução           | `PortfolioHistoryChart.jsx`: períodos de 7/30/60/90 dias e alternância patrimônio/resultado     |
| Alocação           | `AllocationChart.jsx`: rosca por classe, legenda com valor e participação                       |
| Impacto diário     | `DailyMovers.jsx`: cinco maiores contribuições em módulo e contagens de alta/estabilidade/queda |
| Ganhos e perdas    | `ProfitLossChart.jsx`: posições com custo, filtros e expansão da lista                          |
| Cotação individual | `PortfolioChart.jsx`: seleção de ativo e histórico somente na moeda corrente da cotação         |
| Concentração       | `ConcentrationChart.jsx`: três maiores pesos e ranking das cinco maiores posições               |
| Cobertura e ações  | `OverviewAside.jsx`: dados disponíveis, acesso aos ativos, Telegram e resumo                    |
| Compartilhados     | `components/ui/LineChart.jsx`, `DivergingBars.jsx`, `lib/chartGeometry.js` e formatadores       |

Os percentuais de resultado usam o custo das posições efetivamente incluídas. Um preço médio zero ou ausente é tratado como custo desconhecido na dashboard; a posição continua no patrimônio quando tem valor em BRL, mas fica fora do ganho. Variação ausente ou menor ou igual a -100% não entra no cálculo diário, pois não permite recuperar um patrimônio anterior válido. Sem denominador válido, os indicadores exibem indisponibilidade.

A rosca mantém cores por classe. As barras de resultado/impacto partem de um eixo central; não impõem largura mínima fictícia a valores zero. O eixo horizontal dos históricos usa datas, preservando intervalos irregulares. A linha de referência usa custo/preço médio quando disponível; no resultado histórico, usa zero. O resultado consolidado histórico é bloqueado enquanto houver posição cotada sem custo.

## Consultas, estados e atualização

- `usePanelData.js` carrega sessão/overview e listas mapeadas para a página ativa, com atualização nominal de 30 segundos. Configurações começam indisponíveis e seus formulários só montam após a resposta; salvar recarrega os valores da página.
- `useChartHistory.js` consulta os endpoints de histórico, aborta requisições substituídas e separa carregamento, erro e dados insuficientes. Não reutiliza visualmente o histórico de outro ativo/período enquanto aguarda a nova resposta. Na dashboard, novas posições/cotações recebidas pelo overview também revalidam os históricos.
- `QueuePage.jsx` consulta sua própria API ao montar, após ações e pelo botão de atualização; seus jobs não fazem parte do polling de listas de `usePanelData`.
- `services/api.js` serializa objetos JSON uma vez e preserva FormData/AbortSignal. Mutações recebem objetos, não `JSON.stringify(...)`. Respostas com `ok: false` apresentam o erro mesmo quando o HTTP é 200.
- `usePagination` pagina o conjunto recebido. O frontend não presume que endpoints limitados entregam o histórico inteiro; ampliar o lote/consultar páginas do servidor requer integração explícita.

A proteção de origem é aplicada pela API. O navegador envia cookies na mesma origem e o backend compara `Origin` a `APP_ORIGIN`; o cliente não gera token CSRF próprio.

## Acessibilidade e verificação visual

Os controles de gráfico usam labels, botões com `aria-pressed`, selects nativos e um controle de intervalo acessível por teclado. Eixos, valores textuais e sinais acompanham as cores. A dashboard reorganiza cartões e painéis em telas estreitas; tabelas preservam rolagem horizontal interna quando necessário. Mantenha estados vazios, mensagens de falha e a identificação da demonstração.

Para conferir o visual, compile o painel e use a demonstração em banco isolado conforme o [README principal](../README.md#desenvolvimento-e-demonstração). Não use scripts de captura que se conectem ao banco pessoal apenas para gerar imagens de documentação. As capturas antigas em `docs/screenshots/` não comprovam o layout atual.

Os testes de cálculo estão em `tests/portfolio.test.js`; renderização/estados, em `tests/views.test.js`; serialização/erros, em `tests/api.test.js`; limites obrigatórios, em `tests/lint.test.js`. Testes de renderização não substituem inspeção no navegador. A validação registrada em [situação da implementação](../docs/implementacao.md#evidências-da-revisão-de-14112026) documenta o que foi observado, sem afirmar cobertura de código de 100%.
