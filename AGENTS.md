# Telegram Money

## Escopo e estrutura

- `frontend/`: painel React 19 com JavaScript, Vite e npm. Leia também `frontend/AGENTS.md` antes de alterar o painel.
- `backend/`: API e workers Python. Preserve contratos HTTP, autenticação, validações e proteção de origem.
- `docs/`: documentação operacional. `scripts/`: manutenção local e implantação.
- Consulte `README.md` para configurar o ambiente; nunca adicione credenciais, `.env`, bancos ou dados pessoais ao código.

## Padrões de alteração

- Faça a menor alteração que resolva a tarefa por completo e reutilize componentes existentes.
- Preserve textos em português, acessibilidade, comportamento de demonstração e tratamento de erros.
- Não adicione camadas, bibliotecas, pastas vazias ou abstrações sem uso concreto.
- Documente mudanças de arquitetura, configuração e comandos de desenvolvimento.
- No frontend, complexidade ciclomática máxima **10**, funções com no máximo **150 linhas** e **5 parâmetros**. Os limites são obrigatórios e verificados pelo ESLint.

## Verificação

- Frontend: `cd frontend && npm ci && npm run check`.
- Backend, se alterado: `cd backend && uv run pytest -q`.
- Não envie mensagens reais ao Telegram nem consulte provedores pagos nos testes; use mocks ou demonstração isolada.
- Ao concluir, informe o que mudou, os comandos executados e o que não foi verificado.
