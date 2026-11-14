# Situação da implementação

Atualizado em 14/11/2026 a partir do código e das verificações desta revisão. A [ERS original](requisitos-originais.md) é uma referência histórica; a decisão de uso pessoal prevalece sobre requisitos comerciais. Instalação e comandos estão no [README](../README.md), e os fluxos técnicos em [Arquitetura](arquitetura.md).

## Decisões em vigor

- Um proprietário, sem cadastro público comercial, clientes, cobrança, RBAC ou execução de ordens.
- React 19/Vite com CSS próprio; API FastAPI, SQLAlchemy e Alembic; PostgreSQL no Compose e SQLite no desenvolvimento/testes.
- Redis como broker/locks; um worker Celery com concorrência 1 e um beat. Bot aiogram opcional, em long polling.
- Configuração inicial pelo assistente CLI ou web. Integrações persistidas no banco prevalecem sobre os valores equivalentes do `.env`.
- LM Studio ou Ollama sob controle do proprietário; JSON estruturado e evidência literal, sem fallback automático de provedor.
- Fontes abertas para o mercado brasileiro, brapi opcional, Google News RSS e CSV oficial do Tesouro. Disponibilidade/cobertura não são garantidas.

## Funcionalidades e requisitos

| Requisito / área                        | Situação                              | Implementação e limite                                                                                                                                                                                                                                              |
| --------------------------------------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| RF-01 · autenticação                    | Adaptado ao uso pessoal               | Setup web/CLI ou bootstrap por ambiente; e-mail/senha, PBKDF2, sessão HttpOnly de 12 h, logout e limite de tentativas. Perfil permite alterar e-mail/senha; reset no terminal revoga sessões                                                                        |
| RF-01 · Telegram e preferências         | Implementado                          | Código de vínculo por 15 min e uso único; chat privado, fuso, pausa, silêncio e frequência. Teste de token consulta `getMe`; teste de envio é uma mensagem real enfileirada                                                                                         |
| RF-02 · ativos e carteira               | Implementado com limites              | CRUD, listas, classes, quantidades/custo e consulta no bot. API limita a 50 ativos; CLI de importação não aplica esse limite. Classes de cripto/câmbio/exterior não têm cobertura equivalente                                                                       |
| Importação B3                           | Implementado com limites              | Custódia e movimentação `.xlsx`/`.csv`. Custódia preserva custo; extrato calcula preço médio ponderado e zera ativos existentes vendidos. Histórico parcial e movimentos não reconhecidos exigem conferência; não é escrituração fiscal                             |
| Dashboard                               | Implementado                          | Quatro indicadores monetários, contagens/cobertura e seis gráficos: evolução, alocação, impacto diário, resultado, cotação individual e concentração. BRL e custo conhecido são filtrados; históricos por mouse/teclado. Sem retorno total/benchmark                |
| ALT-01/02 · alta/queda diária           | Implementado                          | Usa a variação percentual diária da fonte; não mede variação entre dois ticks locais                                                                                                                                                                                |
| ALT-03 · preço-alvo                     | Implementado                          | Acima/abaixo, com disparo se a condição já estiver satisfeita; rearme após cotação posterior fora da condição                                                                                                                                                       |
| ALT-04/05 · extremos de 52 semanas      | Implementado com limite               | Depende de faixas fornecidas pela fonte; sem reconstrução independente ou garantia de ajuste por eventos                                                                                                                                                            |
| ALT-06 · oscilação anormal              | Parcial                               | Limite absoluto da variação diária; não é um modelo estatístico de volatilidade                                                                                                                                                                                     |
| ALT-07/08/09 · proventos e datas        | Implementado com integração a validar | Consulta aberta/brapi e importação manual, lembretes, revisão/cancelamento por identificador e fontes. Cobertura/datas e elegibilidade aos pagamentos precisam de conferência                                                                                       |
| ALT-10/11/12 · documentos e subscrições | Parcial                               | Texto/PDF/evento importado pode gerar notificação; notícias por RSS. Não há coletor de documentos oficiais CVM/B3                                                                                                                                                   |
| ALT-13 · taxa do Tesouro cruza limite   | Pendente                              | Coleta e tela de taxas por data-base disponíveis; regra de cruzamento por título ausente                                                                                                                                                                            |
| ALT-14 · índices/câmbio                 | Parcial                               | Índices aceitos pelas fontes usam regras existentes. Cadastro não implica coletor de câmbio, cripto ou índices internacionais                                                                                                                                       |
| RF-03 · deduplicação e entrega          | Implementado com limites do canal     | Evento único, rearme, fila persistente, silêncio, pausa, frequência, backoff de conexão/429 e conferência de resultados incertos. Sem entrega exatamente uma vez ou recibo de leitura                                                                               |
| RF-04 · eventos corporativos            | Parcial                               | Modelo/importação de dividendos, JCP, rendimentos, amortização, desdobramento, grupamento e subscrição. Coletor normaliza eventos em dinheiro; não ajusta automaticamente as posições existentes a cada evento coletado                                             |
| RF-05 · IA                              | Parcial                               | Texto/PDF, LM Studio/Ollama, fatos/evidências, interpretações, riscos, ausências e contexto anterior. Até 10 MB/80 páginas extraídas; sinaliza truncamento. Contexto de até 35 mil caracteres atuais e 12 mil anteriores. Sem OCR ou avaliação semântica automática |
| Fila & Recursos                         | Implementado com limites              | Pausa, prioridade, cancelamento, nova tentativa e despacho de IA. Índice parcial e slots/token protegem concorrência. Um trabalho por despacho; aumentar teto não aumenta processos do worker                                                                       |
| RF-06 · relatórios                      | Parcial                               | Diário/semanal/mensal/sob demanda, snapshot atual, janela de preços por ativo e próximos pagamentos. Não reconstrói posição passada, retorno total ou fluxo de caixa; sem benchmark/explicação por IA                                                               |
| RF-07 · bot                             | Implementado                          | Comandos e menu, leitura pelo chat vinculado, pausa/retomada e desvinculação. Bot opcional; token lido ao iniciar. Fonte do documento por link, sem arquivo PDF enviado                                                                                             |
| RF-08 · painel                          | Implementado                          | Visão geral, ativos, regras, eventos, documentos, fila, relatórios, histórico, Tesouro e configurações. Filtros/paginação sobre o lote carregado do endpoint                                                                                                        |
| RF-09 · administração comercial         | Fora do escopo                        | Sem clientes, planos, assinatura ou métricas comerciais                                                                                                                                                                                                             |

Na importação de movimentações, desdobros/grupamentos reconhecidos são processados no próprio extrato. Isso não equivale a ajustar posições automaticamente com os eventos obtidos pelo coletor de proventos. Identificadores derivados de eventos podem exigir reconciliação se a fonte corrigir datas utilizadas na composição da chave.

## Configuração, recursos e segurança

| Área                        | O que existe                                                                                             | Limite / pendência                                                                                                    |
| --------------------------- | -------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Configurações               | `system_settings`, formulários por seção, segredos omitidos na leitura, preservação de campos ausentes   | Banco e backups contêm segredos de integração em texto; não há criptografia de aplicação desses campos                |
| Setup                       | Criação inicial de proprietário e sessão; testes públicos fechados após configuração                     | Implantação continua privada/local; setup público não substitui desenho de provisionamento para internet              |
| Gateways de IA              | Origens autorizadas, URL HTTP(S) validada, sem redirects/proxy de ambiente, prazo total de requisição    | Origens adicionais requerem configuração no servidor; desconexão não obriga o modelo remoto a parar                   |
| Concorrência                | `resource_leases` no banco, aquisição condicional de tarefas e token de execução                         | Tetos de IA/coletores não criam executores. Reserva de coletor expira em uma hora em caso de abandono                 |
| Cancelamento e falhas de IA | Resultado antigo descartado; cancelamento persistido no documento; nova tentativa explícita              | Cancelar uma requisição em curso mantém slot até retorno/timeout; não há retries automáticos de IA por `max_attempts` |
| Frequência                  | Intervalo de cotações compartilhado por Fontes/Fila; verificação a cada 10 s, atualização manual forçada | Worker único pode atrasar a agenda; frequência do painel é outra, nominalmente 30 s                                   |
| Segurança de acesso         | Sessão opaca/hash, PBKDF2, validação de origem/host, headers e chat privado                              | HTTPS/proxy, proteção de borda, revisão para exposição pública e carga não validados                                  |
| Persistência                | Migrations, PostgreSQL/SQLite, filas no banco, Redis AOF e volumes                                       | Não há prova de recuperação completa apenas por healthcheck/migration aplicada                                        |
| Privacidade                 | Sem analytics; demonstração isolada; sem armazenamento do binário PDF                                    | Exportação/exclusão integral e política operacional de retenção ainda pendentes                                       |
| Disponibilidade             | Locks, estados persistentes, retentativas de entrega e diagnóstico                                       | Sem SLO de disponibilidade/latência, medição de memória ou heartbeat contínuo de todos os processos                   |
| Backups                     | Scripts `pg_dump`/`pg_restore`, permissões restritas e confirmação de restore                            | Agendamento, criptografia e ensaio de restauração continuam operacionais/manuais                                      |
| Observabilidade             | `/health`, estados de fontes, auditoria, histórico e ping Celery                                         | `/health` só verifica API/banco; não valida fontes, bot ou agenda fim a fim                                           |
| Fontes                      | Consultas abertas/brapi, RSS por ativo e CSV Tesouro                                                     | Validar cobertura, limites, datas, contratos e disponibilidade; CVM, câmbio/cripto/exterior pendentes                 |

## Evidências da revisão de 14/11/2026

| Verificação             | Resultado observado                                                                                                                                              |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Backend                 | 103 testes aprovados, incluindo concorrência SQLite, cancelamento, deadline, configuração, importação e migration; um aviso de depreciação do TestClient/HTTPX   |
| Frontend                | 33 testes aprovados; formatação, ESLint e build concluídos, incluindo regras de cálculo e estados vazios                                                         |
| Migração isolada        | Upgrade, consolidação de tarefas duplicadas, downgrade e novo upgrade em SQLite temporário                                                                       |
| Navegador               | Demonstração com dados fictícios em desktop e largura de 390 px; filtros, seleção de período/ativo e teclado nos gráficos; sem erro/warning de console observado |
| Rebuild Docker Desktop  | Imagem recompilada; API, worker e beat recriados; PostgreSQL e Redis preservados                                                                                 |
| Verificação operacional | API saudável, dashboard compilada presente na imagem, worker com `pong`, beat em execução e Alembic `d3e4f5a6b7c8 (head)` em PostgreSQL                          |

Essas evidências não constituem teste de carga, medição de cobertura de código, ensaio de restauração ou validação de envios reais e provedores pagos. As verificações de código usaram mocks/dados fictícios; a atualização operacional confirmou startup e schema, sem teste manual de entrega Telegram.

## Pendências concretas

1. Validar fontes e entregas reais de forma controlada na instalação do proprietário, sem assumir que os testes simulados cobrem o comportamento de cada provedor.
2. Implementar coleta de documentos CVM com identidade/correção de origem; manter notícias RSS como fluxo separado.
3. Acrescentar regras por título do Tesouro e conectores de câmbio/cripto/exterior quando necessários.
4. Definir calendário B3, retorno total e ledger de operações caso se deseje reconstrução patrimonial real.
5. Operar backups agendados, testar restauração em ambiente separado e monitorar processos.
6. Evoluir paginação de servidor e contratos de saída conforme o volume e as necessidades observadas.
