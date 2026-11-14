# Correções da revisão das alterações locais

Ordem de execução e critérios de conclusão:

- [x] 1. Segurança: fechar testes públicos depois do setup, autorizar origens dos gateways e bloquear execução real na demonstração.
- [x] 2. Dados: carregar configurações antes dos formulários, salvar somente o domínio alterado e preservar custo médio na importação de custódia.
- [x] 3. Fila: corrigir JSON, persistir cancelamento, adquirir tarefas e slots atomicamente, aplicar limites e timeout e unificar o intervalo de coleta.
- [x] 4. Resultados: recuperar cotação anterior ao período, indicar histórico estimado/incompleto, importar posições zeradas, exibir falhas de integração e corrigir escolhas do CLI.
- [x] 5. Validação: substituir o XLSX pessoal por fixture sintética, testar regressões, executar checks do frontend/backend e documentar configuração e migração.

Não executar integrações reais, publicar, enviar mensagens ou alterar dados pessoais durante as verificações.

## Validação inicial das correções (registro histórico)

- Frontend: `cd frontend && npm ci && npm run format && npm run check` — 25 testes, formatação, lint e build aprovados.
- Backend: `cd backend && UV_CACHE_DIR=/private/tmp/telegram-money-uv-cache uv run pytest -q` — 103 testes aprovados; um aviso de depreciação do TestClient/HTTPX.
- Ruff nos serviços e testes de regressão alterados e `git diff --check` aprovados.
- A migração foi testada em SQLite temporário: upgrade, consolidação de duplicatas, downgrade e novo upgrade.
- Na etapa inicial, requisições externas foram simuladas e ainda não havia validação em navegador, Docker ou PostgreSQL.
- Na etapa inicial, o banco de uso ainda não havia sido migrado. A atualização operacional posterior está registrada abaixo; instalações novas continuam seguindo o procedimento do README.

## Atualizações posteriores em 14/11/2026

O registro inicial acima descreve o estado ao concluir a revisão de código. As etapas seguintes ampliaram a validação e atualizaram a instalação:

- Dashboard reorganizada com seis gráficos, indicadores filtrados por moeda/custo, cobertura e consulta por teclado. Nenhuma dependência de gráficos foi adicionada.
- `npm ci` e `npm run check` aprovados com 33 testes de frontend, incluindo cálculos, intervalos temporais, carteira vazia e renderização. O registro anterior de 25 testes foi sucedido por essa suíte.
- Demonstração verificada no navegador com dados fictícios, em desktop e largura de 390 px; filtro de prejuízo, período/ativo e teclado do gráfico funcionaram. Sem erros/warnings de console observados.
- Rebuild realizado no contexto `desktop-linux`: `compose build api`, pausa de worker/beat e recriação de API/worker/beat com espera de saúde. Banco e Redis foram preservados; o bot opcional permaneceu desativado.
- API saudável e dashboard atualizada presente na imagem; worker respondeu `pong`, beat ficou em execução e `alembic current` confirmou `d3e4f5a6b7c8 (head)` em PostgreSQL. Assim, a indicação inicial de banco não migrado foi superada pela atualização autorizada dos containers.
- Não foram executados testes manuais de entrega Telegram, provedores pagos, carga ou restauração de backup nessa atualização.

Instalação, rebuild e recuperação estão no [README](../README.md); a descrição atual do sistema está em [Arquitetura](arquitetura.md) e na [matriz de implementação](implementacao.md). As contagens acima são evidências desta revisão, não metas fixas ou percentuais de cobertura de código.
