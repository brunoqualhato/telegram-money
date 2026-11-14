# Levantamento de Requisitos — Plataforma de Alertas Financeiros via Telegram

Documento de requisitos de software (ERS) • Versão 1.0

O objetivo é desenvolver uma plataforma de alertas financeiros utilizando o Telegram como principal canal de comunicação, com monitoramento de ações, fundos imobiliários, dividendos, variações de preços, notícias e relatórios resumidos por inteligência artificial.

A solução terá um painel web para configuração, um backend para monitoramento contínuo do mercado financeiro e um bot do Telegram para distribuir notificações personalizadas.

## 1. Funcionalidades previstas

| Módulo                  | Recursos                                                |
| ----------------------- | ------------------------------------------------------- |
| Cotações                | Ações, FIIs, ETFs, índices e moedas                     |
| Alertas de preço        | Preço-alvo, quedas, altas e variações percentuais       |
| Proventos               | Dividendos, JCP, rendimentos de FIIs e datas relevantes |
| Carteira                | Ativos acompanhados, quantidades e desempenho           |
| Notícias                | Notícias relevantes sobre empresas e mercado            |
| Inteligência artificial | Resumos, explicações e relatórios                       |
| Relatórios              | Diário, semanal, mensal e sob demanda                   |
| Telegram                | Alertas automáticos, comandos e consultas               |
| Painel web              | Dashboard, configurações e histórico                    |
| Administração           | Usuários, planos, fontes de dados e monitoramento       |

## 2. Exemplos das notificações

Bot de alertas financeiros

Telegram

🔴 Alerta de queda · VALE3

Cotação atual: R$ 74,12

Variação do dia: -2,14%

O ativo ultrapassou o limite de queda configurado.

💰 Novo provento · XPML11

Rendimento: R$ 0,92 por cota

Data-com: 14/08

Exemplo ilustrativo de comunicado de provento.

🎯 Preço-alvo atingido · PETR4

Preço-alvo: R$ 40,00

Cotação: R$ 40,12

O ativo atingiu o valor configurado para acompanhamento.

Os valores acima são ilustrativos, não cotações em tempo real.

## 3. Requisitos funcionais detalhados

Referência: funcionalidades e especificações do mercado de alertas financeiros.



### RF-01 — Cadastro e autenticação

- Cadastro com e-mail e senha ou login social.
- Vinculação de conta ao Telegram por código temporário.
- Suporte a múltiplos usuários, cada um com seus ativos.
- Configuração de idioma, fuso horário e preferências.
- Ativação e desativação de notificações.

### RF-02 — Lista de acompanhamento

- Adicionar e remover ativos por ticker.
- Acompanhar ações, FIIs, BDRs, ETFs, índices e criptomoedas.
- Visualizar preço, variação diária, máxima e mínima.
- Organizar ativos em listas personalizadas.
- Consultar ativos diretamente pelo Telegram.

### RF-03 — Alertas automáticos

| ID     | Evento               | Condição                             |
| ------ | -------------------- | ------------------------------------ |
| ALT-01 | Alta percentual      | Ativo sobe acima do limite           |
| ALT-02 | Queda percentual     | Ativo cai abaixo do limite           |
| ALT-03 | Preço-alvo           | Preço cruza o valor configurado      |
| ALT-04 | Máxima de 52 semanas | Nova máxima registrada               |
| ALT-05 | Mínima de 52 semanas | Nova mínima registrada               |
| ALT-06 | Oscilação anormal    | Variação superior ao padrão definido |
| ALT-07 | Provento anunciado   | Novo evento de distribuição          |
| ALT-08 | Data-com             | Aproximação da data de elegibilidade |
| ALT-09 | Pagamento            | Data de pagamento próxima            |
| ALT-10 | Fato relevante       | Novo comunicado publicado            |
| ALT-11 | Relatório gerencial  | Novo relatório de FII                |
| ALT-12 | Subscrição           | Novo evento de subscrição            |
| ALT-13 | Tesouro Direto       | Taxa ultrapassa limite definido      |
| ALT-14 | Índices e câmbio     | Variação atinge limite configurado   |

Regras importantes: não repetir notificações para o mesmo evento, permitir períodos de silêncio, definir frequência máxima e rearmar alertas de preço somente após o retorno à condição normal ou mediante regra configurável.

### RF-04 — Proventos e eventos corporativos

O sistema deverá capturar e normalizar dividendos, JCP, rendimentos, amortizações, desdobramentos, grupamentos e subscrições.

Cada evento terá ticker, valor por unidade, data de anúncio, data-com, data-ex, data de pagamento, fonte e situação. Alterações e cancelamentos deverão gerar atualização, sem duplicar o evento original.

### RF-05 — Inteligência artificial

A IA deverá processar documentos financeiros, especialmente relatórios gerenciais de FIIs e fatos relevantes de empresas.

Os resumos deverão apresentar:

- Principais acontecimentos e indicadores.
- Distribuições anunciadas e datas.
- Variações patrimoniais, vacância e inadimplência quando aplicáveis.
- Riscos e pontos de atenção mencionados.
- Comparação com relatórios anteriores.
- Link para o documento original.

A IA não poderá inventar indicadores ausentes, deverá identificar documentos incompletos e distinguir fatos extraídos de interpretações geradas.

### RF-06 — Relatórios financeiros

O sistema deverá gerar fechamento diário, resumo semanal e relatório mensal, além de relatórios sob demanda.

O fechamento diário poderá incluir IBOV, IFIX, dólar, S&P 500, maiores altas e quedas, desempenho dos ativos acompanhados e acontecimentos relevantes.

O relatório de carteira poderá incluir desempenho consolidado, distribuição por classe de ativos e proventos previstos, desde que o usuário tenha informado quantidades e preços de aquisição.

### RF-07 — Bot Telegram

O bot será interativo e deverá suportar comandos e botões inline.

Simulação de comandos

Protótipo

/cotacao PETR4

/proventos

/carteira

/tesouro

/resumo

/alertas

Resposta simulada do bot

📈 PETR4\
Cotação: R$ 40,12\
Variação: +1,25%\
Horário: 16:45

As respostas são demonstrativas; o bot real consultará os serviços de dados.

### RF-08 — Painel web

O painel deverá permitir visualizar o mercado, configurar alertas, acompanhar proventos, consultar histórico e gerenciar a integração com o Telegram.

### RF-09 — Administração e assinaturas

Para uma versão comercial, prever gerenciamento de planos, limites de ativos, permissões, períodos de teste, cobrança recorrente e estatísticas de utilização.

## 4. Arquitetura técnica recomendada

Arquitetura lógica simplificada. As setas representam fluxos de integração, não conexões diretas entre todos os serviços.

| Camada          | Tecnologia sugerida                    |
| --------------- | -------------------------------------- |
| Frontend        | Next.js, React, Tailwind CSS           |
| Backend         | Python, FastAPI                        |
| Bot             | aiogram (Telegram Bot API)             |
| Banco           | PostgreSQL                             |
| Cache e filas   | Redis                                  |
| Processamento   | Celery + Celery Beat                   |
| IA              | LLM via API ou Ollama local            |
| Documentos      | PyMuPDF, extração de tabelas           |
| Armazenamento   | S3 compatível ou MinIO                 |
| Implantação     | Docker Compose inicialmente            |
| Observabilidade | Prometheus, Grafana, logs estruturados |

O backend deverá compartilhar dados de mercado entre usuários: uma cotação de PETR4 é coletada uma vez e distribuída aos assinantes interessados, em vez de consultar a fonte individualmente para cada usuário.

## 5. Modelo de dados

Estrutura inicial do PostgreSQL:

| Tabela                | Responsabilidade                 |
| --------------------- | -------------------------------- |
| `users`               | Usuários e autenticação          |
| `telegram_accounts`   | Vinculação com chat_id           |
| `assets`              | Cadastro de ativos e tickers     |
| `watchlists`          | Listas personalizadas            |
| `watchlist_assets`    | Ativos de cada lista             |
| `portfolios`          | Carteiras                        |
| `portfolio_positions` | Quantidades e custos             |
| `quotes`              | Histórico de cotações            |
| `alert_rules`         | Condições de disparo             |
| `alert_events`        | Eventos detectados               |
| `notifications`       | Entregas, tentativas e erros     |
| `corporate_actions`   | Proventos e eventos corporativos |
| `documents`           | Relatórios e fatos relevantes    |
| `ai_summaries`        | Resumos e referências            |
| `market_reports`      | Relatórios periódicos            |
| `subscriptions`       | Planos e assinaturas             |
| `audit_logs`          | Auditoria                        |

Criar índices por ativo e horário, chaves de idempotência para eventos, retenção configurável para cotações e controle de acesso por usuário.

## 6. Fontes de dados

A principal dificuldade técnica será obter dados financeiros confiáveis, atualizados e com licença compatível com a finalidade do produto.

| Fonte                                                                         | Utilização                                     |
| ----------------------------------------------------------------------------- | ---------------------------------------------- |
| [B3](https://www.b3.com.br/?utm_source=chatgpt.com)                           | Dados oficiais e eventos do mercado brasileiro |
| [CVM Dados Abertos](https://dados.cvm.gov.br/?utm_source=chatgpt.com)         | Documentos, informes e fatos relevantes        |
| [brapi](https://brapi.dev/?utm_source=chatgpt.com)                            | Cotações e dados de ativos, conforme plano     |
| [Tesouro Direto](https://www.tesourodireto.com.br/?utm_source=chatgpt.com)    | Taxas e preços de títulos públicos             |
| [Banco Central](https://www.bcb.gov.br/?utm_source=chatgpt.com)               | Indicadores econômicos e câmbio                |
| [Telegram Bot API](https://core.telegram.org/bots/api?utm_source=chatgpt.com) | Entrega e interação com usuários               |

Atenção: dados gratuitos não garantem tempo real. Antes de oferecer alertas instantâneos comercialmente, será necessário verificar latência, limites de requisições, cobertura e direitos de redistribuição de cada provedor.

## 7. Requisitos não funcionais

| ID     | Requisito           | Meta inicial                           |
| ------ | ------------------- | -------------------------------------- |
| RNF-01 | Disponibilidade     | 99,5% mensal                           |
| RNF-02 | Latência de alertas | Até 30 s após ingestão do evento       |
| RNF-03 | Escalabilidade      | 1.000 usuários inicialmente            |
| RNF-04 | Segurança           | HTTPS, tokens protegidos e RBAC        |
| RNF-05 | Privacidade         | LGPD e exclusão de dados               |
| RNF-06 | Resiliência         | Retentativas, backoff e fila de falhas |
| RNF-07 | Auditoria           | Registrar fonte e horário dos eventos  |
| RNF-08 | Backup              | Backup diário e testes de restauração  |
| RNF-09 | IA                  | Resumos com referências verificáveis   |

A latência de 30 segundos começa quando o evento chega ao sistema, não necessariamente quando acontece na bolsa.

## 8. Plano de implementação

01

MVP — Alertas e Telegram

3–5 semanas

Cadastro, vinculação do bot, watchlist, cotações, alertas de alta/queda, preço-alvo e fechamento diário.

02

Proventos e documentos

2–4 semanas

Dividendos, JCP, datas, relatórios gerenciais, fatos relevantes e envio de PDFs.

03

Inteligência artificial

2–3 semanas

Extração de documentos, resumos fundamentados, comparações e relatórios semanais.

04

Produto comercial

3–5 semanas

Planos, assinaturas, administração, monitoramento, limites e otimização de custos.

As estimativas são indicativas para desenvolvimento com integrações existentes, sem incluir atrasos na contratação ou licenciamento de dados.

## 9. Critérios de aceite do MVP

O MVP será considerado funcional quando um usuário conseguir criar uma conta, conectar o Telegram, cadastrar ativos, configurar limites, receber alertas sem duplicidade, consultar cotações por comando e receber o fechamento diário. Também deverá ser possível identificar falhas de coleta e reprocessar entregas sem gerar notificações repetidas.

Recomendação de escopo: iniciar com ações e FIIs brasileiros, Telegram e alertas de preço. Em seguida incorporar proventos, documentos e IA. Isso permite validar o produto antes de assumir custos maiores com dados financeiros e processamento de documentos.

Como evolução, o mesmo backend poderá atender Telegram, aplicativo móvel e outros canais, mantendo as regras financeiras independentes do meio de entrega.

Próximo passo: transformar os requisitos em um projeto executável.

Posso estruturar o repositório com backend FastAPI, bot Telegram, PostgreSQL, Redis, Docker Compose, migrations, endpoints e testes iniciais.

&#x20;Criar projeto inicial com código