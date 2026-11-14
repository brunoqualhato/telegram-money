# Escopo e situação da implementação inicial

Base: [ERS fornecida](requisitos-originais.md). A confirmação de **uso pessoal** prevalece sobre as sugestões comerciais. Este projeto não certifica disponibilidade de 99,5%, latência de 30 segundos, atendimento a 1.000 usuários ou conformidade jurídica. Não foram contratados provedores de dados, criadas credenciais, enviados alertas reais ou feita publicação.

## Decisões

- FastAPI + SQLAlchemy + Alembic; PostgreSQL no Compose, SQLite no desenvolvimento/testes.
- React + Vite + CSS próprio. Não há necessidade de SSR, portanto Next.js e Tailwind não foram adicionados.
- Redis + Celery worker/beat; uma instância do worker com concorrência 1, um beat e um bot por instalação pessoal.
- aiogram com long polling para evitar depender de URL pública.
- LM Studio como gateway padrão via `/v1/chat/completions`, JSON schema e token Bearer opcional. Ollama é alternativa explícita. Modelo e servidor fornecidos pelo proprietário; sem fallback de provedor.
- Não há contas de clientes, RBAC, cadastro público, pagamento ou assinatura. Um proprietário é inicializado pela configuração local.
- PDF é extraído e o texto fica no banco; o binário não é armazenado nem encaminhado ao Telegram. Não foi adicionado S3/MinIO sem necessidade de preservar arquivos.
- Sem Prometheus/Grafana nesta etapa. Saúde de fontes, tentativas e auditoria são visíveis na API/painel; logs do worker permitem diagnóstico.

## Requisitos funcionais

| Requisito | Situação | Implementação / limite |
| --- | --- | --- |
| RF-01 · autenticação | Adaptado | Proprietário via `.env`, e-mail/senha, PBKDF2, sessão HttpOnly, expiração, logout, limite de tentativas, reset no terminal. Sem cadastro público, login social ou múltiplos usuários. |
| RF-01 · Telegram e preferências | Implementado | Código de uso único por 15 min, chat privado, fuso, pausa, silêncio e frequência. Interface apenas em pt-BR. |
| RF-02 · acompanhamento | Implementado | CRUD, importação de posição da Área do Investidor B3 (.xlsx/.csv), listas nomeadas, classes, quantidades/custo, preço, variação, máximas/mínimas na API, gráfico e consulta no bot. Cadastro de cripto/moeda permitido, mas sem coletores dessas classes ou exterior. |
| ALT-01/02 · alta/queda | Implementado | Comparação com variação percentual diária informada pelo provedor. |
| ALT-03 · preço-alvo | Implementado | Acima/abaixo com disparo inicial se a condição já estiver atendida. Rearma somente após cotação posterior fora da condição; não há disparo repetido por atualização. |
| ALT-04/05 · 52 semanas | Implementado com limite | Compara preço com faixa de 52 semanas fornecida. Não reconstrói independentemente o histórico nem garante ajuste de eventos corporativos. |
| ALT-06 · oscilação anormal | Parcial | Limite absoluto de variação diária configurado; não é um modelo estatístico de volatilidade. |
| ALT-07/08/09 · proventos e datas | Implementado com integração a validar | brapi e importação manual, aviso de evento relevante, lembretes na véspera, correções e cancelamentos por identificador. Datas reconstruídas por informes são ignoradas. Cobertura depende do plano. |
| ALT-10/11/12 · documentos/subscrições | Parcial | Importação de documento ou evento gera notificação. Não há coleta automática CVM/B3. |
| ALT-13 · taxa do Tesouro cruza limite | Pendente | Consulta e painel de taxas diárias implementados; regra de taxa por título não implementada. |
| ALT-14 · índices/câmbio | Parcial | Índices brasileiros aceitos pela brapi usam as mesmas regras. Câmbio, índices internacionais e cripto sem conector nesta etapa. |
| RF-03 · deduplicação e silêncio | Implementado com limites de canal | Chaves únicas, estado de rearme, fila persistente, retentativas de conexão/429, limite de tentativas, recuperação de envio interrompido. Resultado incerto exige reenvio manual. Não há garantia exactly-once no Telegram. |
| RF-04 · eventos corporativos | Parcial | Modelo/importação para dividendos, JCP, rendimentos, amortização, desdobramento, grupamento e subscrição. Coletor automático cobre eventos em dinheiro normalizáveis; não ajusta posições/custos automaticamente. Identificador derivado sem ID do provedor pode mudar se a própria data-com/aprovação for corrigida; nesses casos é necessária reconciliação. |
| RF-05 · IA | Parcial | Importação de texto/PDF, gateway LM Studio/Ollama, evidência literal validada, fatos/interpretações/riscos/ausências, contexto do documento anterior, sinalização de truncamento. Sem OCR, tabelas estruturadas ou avaliação semântica automática. PDFs até 10 MB/80 páginas; texto de contexto limitado a 35 mil caracteres atuais + 12 mil anteriores. |
| RF-06 · relatórios | Parcial | Diário/semanal/mensal/sob demanda, preços e janela histórica por ativo, snapshot atual da carteira e pagamentos próximos. Sem carteira histórica reconstruída, retorno total, benchmark automático ou explicação gerada por IA dos períodos. Calendário considera dias de semana; feriados B3 pendentes. |
| RF-07 · bot | Implementado | Comandos previstos, inline menu, leitura apenas pelo chat vinculado, pausa/retomada/desvinculação. PDF original disponível via link, sem envio de arquivo. |
| RF-08 · painel | Implementado | Visão geral, ativos, regras, proventos, documentos, relatórios, Tesouro, preferências, fontes e histórico. Responsivo. |
| RF-09 · administração comercial | Fora do escopo pessoal | Sem planos, clientes, cobrança ou estatísticas comerciais. |

## Requisitos não funcionais

| Tema | O que existe | O que falta validar/operar |
| --- | --- | --- |
| Segurança | Senhas derivadas por PBKDF2 com salt; sessão opaca com hash no banco; cookies HttpOnly/SameSite; validação de origem; host permitido; segredos no ambiente; bot restrito ao chat vinculado | HTTPS/proxy no servidor definitivo, revisão específica para exposição pública, testes de carga e limitação de upload na borda |
| Persistência | Migrations, PostgreSQL, fila de notificações no banco, Redis com AOF, volumes Docker | Validar na instalação do usuário; testes atuais usam SQLite |
| Privacidade | Sem analytics; dados locais e Telegram e gateway de IA configurados; `/sair` remove vínculo | Fluxo de exclusão/exportação integral e política de retenção operacional |
| Disponibilidade/latência | Agendamento, locks, retries e registros de fonte | SLOs não medidos; Gerações de IA/coletas longas podem atrasar o worker único; separar filas e workers se necessário |
| Backups | Scripts pg_dump/pg_restore com permissões restritas e confirmação antes de substituir banco | Agendamento diário e ensaio de restauração em ambiente separado |
| Observabilidade | `/health`, status de provedores, histórico de erros/entregas e audit logs | Heartbeats do bot/worker/beat e métricas/alertas externos |
| Fontes | Conectores brapi v2 e CSV Tesouro oficial | Credenciais/cobertura real, compatibilidade do payload contratado, limites e licenças; CVM/notícias/exterior pendentes |

## Próximos passos concretos

1. Ativar o Docker e executar a instalação com as credenciais pessoais; conectar um bot dedicado.
2. Validar cotações e proventos em uma conta brapi, usando poucas posições inicialmente, e ajustar intervalo/cota.
3. Conferir um disparo real, pausa, rearme e histórico; conferir fechamento diário com o worker e beat ativos.
4. Adicionar coleta CVM e de notícias com identidade de documento estável, correções e fonte original.
5. Adicionar regras por título do Tesouro e conectores de câmbio/cripto/exterior.
6. Automatizar backups com teste de restauração, calendário B3 e monitoramento dos processos.
