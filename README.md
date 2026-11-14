# Telegram Money

Monitor financeiro pessoal com painel React 19, API FastAPI, PostgreSQL, Redis, Celery e bot Telegram. Um proprietário acompanha posições, cotações, proventos, documentos e alertas. Não executa ordens nem se conecta à corretora.

O projeto está em desenvolvimento. Cotações podem estar atrasadas; cobertura e disponibilidade dependem das fontes. Gráficos e relatórios não representam retorno total nem reconstroem operações passadas.

## Documentação

| Documento                                                 | Conteúdo                                                        |
| --------------------------------------------------------- | --------------------------------------------------------------- |
| [Arquitetura](docs/arquitetura.md)                        | Serviços, persistência, filas, agendamentos, API e segurança    |
| [Situação da implementação](docs/implementacao.md)        | Funcionalidades disponíveis, limites e pendências               |
| [Frontend](frontend/README.md)                            | Desenvolvimento, componentes, cálculos e verificações do painel |
| [Correções e validações](docs/plano-correcoes-revisao.md) | Registro da revisão, dashboard e atualização dos containers     |
| [Requisitos originais](docs/requisitos-originais.md)      | Referência histórica; o escopo pessoal atual prevalece          |

## Funcionalidades do painel

| Tela            | O que oferece                                                                                                                            |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Visão geral     | Patrimônio em BRL, custo informado, resultado, variação diária e cobertura dos dados; seis gráficos e consulta interativa nos históricos |
| Meus ativos     | Cadastro, edição, listas, quantidade, preço médio e importação B3 `.xlsx`/`.csv`; até 50 ativos pela API                                 |
| Meus alertas    | Preço acima/abaixo, alta/queda diária, oscilação absoluta e extremos de 52 semanas; pausa e rearme                                       |
| Proventos       | Eventos, datas com/ex/pagamento, fontes e atualização manual                                                                             |
| Documentos e IA | Importação de texto/PDF, notícias por RSS e resumos com evidências literais                                                              |
| Fila & Recursos | Tarefas de IA, pausa, prioridade, cancelamento, nova tentativa e limites de recursos                                                     |
| Relatórios      | Diário, semanal, mensal e sob demanda; leitura e download em texto                                                                       |
| Histórico       | Notificações, tentativas e situações de entrega; reenvio manual                                                                          |
| Tesouro Direto  | Taxas e preços da última data-base do CSV oficial                                                                                        |
| Configurações   | Perfil, preferências, Telegram, fontes e gateway de IA                                                                                   |

As capturas em [docs/screenshots](docs/screenshots) são referências de versões anteriores. Os gráficos e controles atuais são descritos abaixo.

### Indicadores e gráficos da carteira

A dashboard mostra evolução patrimonial/resultado, alocação por classe, impacto diário por ativo, ganhos/perdas, histórico individual e concentração nas maiores posições. É responsiva; os históricos permitem consultar valores com o mouse ou pelo controle de teclado.

- **Patrimônio:** soma das posições com quantidade positiva, valor válido e cotação em BRL. Ativos sem cotação em reais ficam fora do total e aparecem na cobertura dos dados.
- **Custo e resultado:** consideram somente posições cotadas com preço médio positivo. Custo ausente não vira lucro; o percentual usa o custo conhecido dessas posições.
- **Variação diária:** para cada posição, o patrimônio anterior é estimado por `valor_atual / (1 + variação_percentual / 100)`. A variação consolidada usa a soma desses valores anteriores, não a média simples dos percentuais. Variações ausentes ou menores ou iguais a -100% são excluídas.
- **Alocação e concentração:** usam o patrimônio cotado em BRL como denominador. A concentração soma os pesos dos três maiores ativos disponíveis; não é uma classificação de risco.
- **Evolução histórica:** aplica quantidades e custos atuais às cotações históricas. Recupera a última cotação anterior à janela e omite dias incompletos. O resultado histórico exige custo informado nas posições cotadas.

Proventos, taxas, aportes, retiradas, posições encerradas e elegibilidade a pagamentos não são incorporados como retorno total. Dashboard, relatório textual e snapshot da API têm apresentações próprias; não trate seus resultados como demonstração contábil ou fiscal.

### Importação B3

A importação aceita posição de custódia e extrato de movimentação da Área do Investidor, por arquivo de até 10 MB.

| Arquivo      | Quantidade                                                                                      | Preço médio                                                                                                                   |
| ------------ | ----------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Custódia     | Atualiza a posição encontrada                                                                   | Preserva o custo existente; preço de fechamento não é custo de aquisição. Novos ativos ficam com custo zero até preenchimento |
| Movimentação | Consolida compras, vendas e movimentos reconhecidos; zera ativos existentes totalmente vendidos | Calcula custo ponderado; atualizar custo existente é uma opção desmarcada por padrão                                          |

Envie o histórico completo de movimentações. Um extrato parcial não reconstrói saldos anteriores. Ativos ausentes do arquivo não são excluídos automaticamente; posições zeradas que ainda não existiam não são cadastradas apenas por terem movimentação passada.

A CLI também aceita `.xlsx`/`.csv`:

```bash
cd backend
uv run python -m app.cli import-b3 /caminho/movimentacao.xlsx
# Para atualizar custo conhecido dos ativos existentes:
uv run python -m app.cli import-b3 /caminho/movimentacao.xlsx --update-price
```

O limite de 50 ativos é validado pela API; o comando de importação da CLI não aplica esse limite.

## Instalação com Docker

Requisitos: Docker Engine/Desktop ativo, Compose v2 e Python 3 para o assistente de terminal.

Na raiz:

```bash
python3 scripts/setup.py
# Mesmo assistente:
python3 scripts/setup_wizard.py
```

O assistente verifica o ambiente, solicita e-mail/senha, configura infraestrutura e integrações opcionais, grava `.env` com permissão `600` e oferece iniciar o Compose. Pode consultar Telegram, brapi e gateways locais quando essas verificações forem escolhidas. `--check-only` executa apenas o diagnóstico; `--quick` usa o fluxo reduzido. Em reconfigurações, guarde o `.env.bak` como segredo e não o versione.

Para iniciar manualmente:

```bash
docker compose up -d --build --wait
```

Abra [http://localhost:8000](http://localhost:8000). A API aplica as migrations antes de iniciar. PostgreSQL e Redis não publicam portas no host; somente a API publica `127.0.0.1:8000`. O bot é opcional e não inicia sem o perfil `telegram`.

### Primeiro acesso pelo navegador

Também é possível preparar somente a infraestrutura a partir de `.env.example`, definir uma senha PostgreSQL forte localmente e iniciar o Compose. Se não existir proprietário e `OWNER_PASSWORD` estiver vazio, o painel mostra o assistente web e cria o acesso inicial. Se a senha de bootstrap estiver definida no ambiente, o proprietário é criado no início da API.

Depois do primeiro acesso, os testes públicos do setup são bloqueados. Use os testes autenticados em **Configurações**. Alterar `OWNER_PASSWORD` no `.env` não troca a senha de um proprietário existente; use o perfil no painel ou o reset no terminal.

### Docker Desktop e contextos

Se `docker compose` apontar para um socket indisponível por causa de `DOCKER_HOST`, confira os contextos e use o contexto que contém os containers do projeto:

```bash
docker context ls
docker --context desktop-linux compose ps --all
```

`desktop-linux` é o contexto do Docker Desktop verificado nesta instalação. Não é necessário alterar o contexto global. Nos comandos seguintes, substitua `docker compose` por `docker --context desktop-linux compose` quando precisar desse contexto.

### Rebuild preservando os dados

Na raiz, reconstrua a imagem compartilhada antes de interromper os serviços:

```bash
docker compose build api
docker compose stop worker beat
docker compose up -d --no-build --force-recreate --wait --wait-timeout 180 api worker beat
docker compose ps --all
docker compose exec -T api alembic current
docker compose exec -T worker celery -A app.tasks:celery inspect ping --timeout 10
```

A API aplica as migrations; worker e beat aguardam sua saúde. Os volumes `postgres-data`, `redis-data` e `beat-data` são preservados. Esse procedimento mantém o bot opcional fora da recriação. Se ele já estiver em uso, pare-o antes da atualização e recrie-o depois com `docker compose --profile telegram up -d --no-build --force-recreate bot`. Evite `down -v`, que remove os volumes.

## Configurações e integrações

Integrações salvas no painel ficam em `system_settings` e prevalecem sobre os valores equivalentes do ambiente. Cada formulário envia somente sua seção; campos de segredo em branco mantêm o valor existente. O painel informa se um segredo está configurado, sem devolvê-lo em `GET /api/integrations`.

Infraestrutura, origem/cookie, demonstração e lista de origens de IA autorizadas continuam no ambiente. A configuração de ambiente é carregada por processo; alterações nela exigem reinício/recriação dos processos envolvidos.

| Variável                                                     | Finalidade                                                                                 |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------ |
| `POSTGRES_PASSWORD`                                          | Obrigatória no Compose; defina localmente antes de iniciar                                 |
| `DATABASE_URL`, `REDIS_URL`                                  | Banco e broker. O Compose substitui pelos endereços internos                               |
| `APP_ORIGIN`                                                 | Origem exata permitida nas mutações, padrão `http://localhost:8000`                        |
| `COOKIE_SECURE`                                              | `false` em localhost HTTP; `true` em uma instalação com HTTPS                              |
| `TIMEZONE`                                                   | Fuso do beat, padrão `America/Sao_Paulo`; o proprietário tem preferências de fuso próprias |
| `OWNER_EMAIL`, `OWNER_PASSWORD`                              | Bootstrap opcional, somente enquanto não existir proprietário                              |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_BOT_USERNAME`                | Valores iniciais opcionais; podem ser configurados pelo painel                             |
| `BRAPI_TOKEN`                                                | Integração opcional; cobertura/cotas dependem do provedor                                  |
| `POLL_SECONDS`                                               | Intervalo inicial de cotações, padrão 120 s, mínimo 30 s                                   |
| `AI_PROVIDER`                                                | `lmstudio` (padrão) ou `ollama`; sem fallback automático                                   |
| `LM_STUDIO_BASE_URL`, `LM_STUDIO_MODEL`, `LM_STUDIO_API_KEY` | Servidor, modelo exato e autenticação opcional do LM Studio                                |
| `OLLAMA_URL`, `OLLAMA_MODEL`                                 | Instância e modelo instalado do Ollama                                                     |
| `AI_TIMEOUT_SECONDS`                                         | Prazo inicial do gateway, padrão 180 s; combinado com o limite da fila                     |
| `AI_ALLOWED_ORIGINS`                                         | Origens extras de gateways autorizados, separadas por vírgula, sem caminho                 |
| `DEMO_MODE`                                                  | Na API/worker, exemplos locais; bloqueia despacho, coleta e testes de integração reais     |

### Telegram

1. Crie um bot dedicado em [@BotFather](https://t.me/BotFather).
2. Salve token e username em **Configurações**. O teste de token chama `getMe`; não envia mensagem.
3. Inicie o processo do bot; se trocou o token de um bot já iniciado, recrie esse processo:

   ```bash
   docker compose --profile telegram up -d --no-build --force-recreate bot
   ```

4. Use **Conectar Telegram**, abra o link e toque em **Iniciar**. O código vale 15 minutos e tem uso único.
5. **Enviar teste** coloca uma mensagem real na fila e segue pausa, silêncio e limite por hora. Consulte o histórico.

O bot lê o token ao iniciar, usa long polling e não remove webhook existente: se houver um, a inicialização é interrompida. Mantenha uma instância do bot. Apenas o chat privado vinculado acessa a carteira.

Comandos: `/cotacao PETR4`, `/carteira`, `/proventos`, `/tesouro`, `/resumo`, `/alertas`, `/pausar`, `/retomar` e `/sair`. O último remove o vínculo, preservando carteira e histórico.

### Fontes de mercado

Sem token brapi, os coletores usam consultas abertas para ações, FIIs, ETFs e BDRs brasileiros. Com token, podem usar a brapi, com fallback para fontes abertas. Notícias vêm de busca Google News RSS por ativo; não há coleta automática de documentos CVM. Cadastro de cripto, câmbio e exterior não significa cobertura por um coletor.

O Tesouro usa CSV oficial consultado às 10h10 e 15h10 no fuso do beat; consulte a data-base. O painel não oferece cotações ou notícias com garantia de tempo real.

### IA local

No painel, selecione provedor, URL, ID exato do modelo e, se necessário, chave do LM Studio. URLs usuais:

| Provedor  | Desenvolvimento no host    | API/worker no Docker Desktop          |
| --------- | -------------------------- | ------------------------------------- |
| LM Studio | `http://localhost:1235/v1` | `http://host.docker.internal:1235/v1` |
| Ollama    | `http://localhost:11434`   | `http://host.docker.internal:11434`   |

Use a porta real configurada no servidor. As origens locais padrão autorizam LM Studio nas portas 1234/1235 e Ollama em 11434, nos hosts `localhost`, `127.0.0.1`, `[::1]` e `host.docker.internal`. As origens definidas no ambiente para os gateways também são autorizadas. Para outro servidor sob seu controle, configure `AI_ALLOWED_ORIGINS` e recrie API/worker. URLs aceitam HTTP(S), sem credenciais, query ou fragmento; caminho vazio ou `/v1` no LM Studio e vazio no Ollama. Não são seguidos redirecionamentos nem proxies de ambiente.

**Testar conexão** consulta modelos, sem enviar documentos ou gerar texto; não garante carregamento do modelo nem suporte à saída estruturada. Resumos usam JSON validado e evidências literais do texto; isso não garante a correção semântica das conclusões. PDF protegido ou sem texto precisa de tratamento externo; não há OCR. O limite de upload é 10 MB, extraindo até 80 páginas com sinalização de conteúdo incompleto.

No assistente CLI, **Desativar IA** deixa ambos os modelos vazios. Se já houver configuração no banco, ela continua prevalecendo sobre o `.env`.

### Fila & Recursos

A fila de processamento de IA é distinta da fila de notificações Telegram.

| Controle              | Comportamento                                                                             |
| --------------------- | ----------------------------------------------------------------------------------------- |
| Pausar IA             | Suspende novos processamentos; não interrompe uma requisição já iniciada                  |
| Priorizar             | Aumenta a prioridade de uma tarefa; o despacho considera prioridade e antiguidade         |
| Cancelar              | Impede recriação automática; resultado de execução em curso é descartado                  |
| Nova tentativa        | Recoloca tarefa falha/cancelada na fila explicitamente                                    |
| Despachar             | Executa no máximo uma tarefa elegível por chamada; aguarda a conclusão                    |
| Concorrência de IA    | Teto compartilhado entre executores, padrão 1; não cria novos processos no worker         |
| Concorrência de APIs  | Limita coletores simultâneos de cotações, eventos, notícias e Tesouro; padrão 2           |
| Timeout de IA         | Menor prazo entre gateway e fila; fila inicia em 120 s                                    |
| Intervalo de cotações | Mesma configuração em Fontes e Fila; aplicada sem reiniciar o beat, com resolução de 10 s |

Slots são adquiridos atomicamente no banco. No cancelamento em curso, o slot continua ocupado até a requisição terminar/expirar. A desconexão não garante que o servidor de IA interrompa sua computação. Reservas abandonadas expiram; a de coletor tem prazo de uma hora. Coletores usam slots, mas não geram atualmente um histórico de tarefas `api` na fila; exemplos dessa categoria na demonstração são ilustrativos.

## Desenvolvimento e demonstração

Requisitos: Python 3.12 ou 3.13, uv, Node.js 22.13+ e npm.

```bash
python3 scripts/setup.py  # escolha o ambiente local
cd frontend
npm ci
npm run build
cd ../backend
uv sync --frozen --python 3.12
uv run alembic upgrade head
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Para tarefas locais, disponibilize Redis em `REDIS_URL` e execute, em terminais separados dentro de `backend/`:

```bash
uv run celery -A app.tasks:celery worker --loglevel=INFO --concurrency=1
uv run celery -A app.tasks:celery beat --loglevel=INFO
uv run python -m app.bot
```

Mantenha um beat e um bot por instalação. No macOS, o worker pode usar `--pool=solo` no desenvolvimento. Para hot reload, use `npm run dev` no frontend e configure `APP_ORIGIN=http://localhost:5173` no backend. O Redis do Compose não publica porta no host; a execução local precisa de uma instância acessível.

Demonstração isolada, depois de compilar o painel, dentro de `backend/`:

```bash
DATABASE_URL=sqlite:///./data/demo.db uv run alembic upgrade head
DATABASE_URL=sqlite:///./data/demo.db DEMO_MODE=true OWNER_PASSWORD='' TELEGRAM_BOT_TOKEN='' uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Entre com `demo@example.com` / `demonstracao-local`. Use um banco exclusivo de demonstração. Exemplos ficam identificados; a demonstração não deve ser exposta na internet.

## Verificações e API

```bash
cd frontend
npm ci
npm run check
cd ../backend
uv sync --frozen --python 3.12
uv run pytest -q
```

Os testes usam dados fictícios, SQLite temporário e mocks de rede. Não exigem arquivos pessoais em Downloads nem fazem envio Telegram ou chamadas pagas. O check do frontend verifica formatação, testes, lint e build. Não há medição publicada de cobertura de código.

Documentação interativa: [OpenAPI](http://localhost:8000/docs). Faça login no mesmo navegador para rotas protegidas. Mutações em `/api/` exigem `Origin` igual a `APP_ORIGIN`; clientes próprios também precisam enviar o cookie de sessão. `/health` verifica API e conexão com o banco; não atesta saúde de fontes, worker, beat ou bot.

## Operação e recuperação

```bash
docker compose logs --tail=100 api worker beat
docker compose --profile telegram logs --tail=100 bot
docker compose exec api python -m app.cli reset-password
bash scripts/backup.sh
bash scripts/restore.sh backups/arquivo.dump
```

O reset de senha no terminal revoga todas as sessões. O restore substitui o banco e exige digitar `RESTAURAR`. Se o ambiente usa Docker Desktop com outro socket em `DOCKER_HOST`, execute os scripts com o contexto explícito:

```bash
env -u DOCKER_HOST DOCKER_CONTEXT=desktop-linux bash scripts/backup.sh
# Somente quando realmente precisar restaurar:
env -u DOCKER_HOST DOCKER_CONTEXT=desktop-linux bash scripts/restore.sh backups/arquivo.dump
```

Backups são manuais e contêm dados financeiros, configurações e credenciais de integrações. Proteja também `.env` e `.env.bak`. Agendamento, criptografia e ensaio de restauração ficam a cargo da operação. Após restaurar um backup antigo, aplique as migrations antes de retomar o uso.

Notificações têm tentativas e retentativas com backoff. Timeout de leitura pode ocorrer após o Telegram receber a mensagem: o estado fica `uncertain` e requer conferência antes de reenvio. Não há garantia de entrega exatamente uma vez. A aplicação registra resposta de envio, não confirmação de leitura pelo destinatário.

Cotações são mantidas por 400 dias. Eventos, documentos e logs não têm expurgo automático. Relatórios completos ficam no painel; mensagens Telegram são limitadas a 4.000 caracteres. A implantação padrão é local; acesso externo exige HTTPS, proxy, origem e cookies configurados para esse ambiente.
