# Padrões do frontend

Estas instruções complementam `../AGENTS.md`. A arquitetura e os comandos estão em `README.md` neste diretório.

## Arquitetura

- Organize por funcionalidade: `src/features/<dominio>/`. Coloque a tela, formulários e componentes específicos junto do domínio.
- `src/app/` compõe telas e coordena estado, navegação, sessão e ações. Use hooks para a lógica de coordenação; mantenha JSX de apresentação nos componentes.
- `src/components/ui/` contém componentes reutilizáveis sem conhecimento das telas ou da API; receba dados e callbacks por props.
- `src/components/layout/` contém navegação e cabeçalho. `src/components/Logo.jsx` é a identidade compartilhada.
- Centralize HTTP em `src/services/api.js`; mantenha cookies, serialização JSON, upload FormData, status de erro e cancelamento.
- Coloque funções puras e constantes em `src/lib/`; estilos globais em `src/styles/`.
- Dependências seguem `app → features → components/ui, lib, services`. Features podem compor outras features quando a tela realmente precisar, como a visão geral.
- Componentes genéricos, serviços e funções utilitárias não importam de `app`, `features` ou `components/layout`. O ESLint verifica essa fronteira.

## Código e interface

- Use componentes funcionais, composição e hooks. Não introduza classes, gerenciador global de estado ou roteador sem necessidade concreta.
- Componentes usam PascalCase, hooks `useNome`, funções e variáveis camelCase; use exports e imports diretos, sem arquivos barrel.
- Use um objeto de props para componentes; para funções comuns, prefira um objeto de opções quando houver muitos argumentos relacionados.
- Complexidade máxima: **10**. Máximo de **150 linhas por função**, incluindo comentários e linhas vazias. Máximo de **5 parâmetros**.
- Esses limites incluem hooks, componentes e callbacks; não use comentários de desativação ou exceções para contorná-los. Extraia responsabilidades reais em vez de comprimir o código.
- Siga as regras de hooks e dependências de efeitos. Limpe timers e requisições canceláveis nos efeitos.
- Preserve labels, `aria-label`, foco, navegação por teclado, estados vazios e erros visíveis. Mutações destrutivas continuam exigindo confirmação.
- Textos da interface em português; formatadores usam `pt-BR` e preservam o significado da moeda e das datas.
- Mantenha o estilo definido pelo Prettier. Não altere manualmente arquivos de `dist/` nem `package-lock.json`.

## Dependências e validação

- Use npm e mantenha o lockfile atualizado. Reutilize React, Vite e Lucide antes de adicionar bibliotecas.
- Testes usam `node:test`, mocks de HTTP e renderização React via Vite, sem chamadas externas.
- Teste regras de negócio e comportamento afetado por refatorações. Mudanças triviais de estilo não precisam de testes novos.
- Antes de entregar: `npm run check` (formatação, testes, lint e build).
- `npm run build` executa lint automaticamente e falha se houver qualquer erro ou aviso.
