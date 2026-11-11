# Controladoria DJEN, skill para o Claude e o Codex

Skill para o **Claude** (Claude Code e app desktop) e para o **Codex** (OpenAI) que faz a controladoria de prazos de advogados a partir do **DJEN**, o Diário de Justiça Eletrônico Nacional do CNJ.

## O que faz

- **Captação pela OAB** na API pública `comunicaapi.pje.jus.br`. A busca é incremental (desde a última captação), percorre todas as páginas, não duplica publicações e, se a API limitar as requisições (HTTP 429), espera 1 minuto e continua.
- **Filtro anti-homônimo.** Mantém só o que traz o nome completo do advogado ou o número da OAB, ou o que tem a OAB/UF na lista de advogados da própria comunicação.
- **Triagem de prazos.** Monta uma tabela com processo, partes, tipo de ato, o que foi determinado, prazo em dias úteis com fundamento, vencimento e providência sugerida. A contagem segue a Lei 11.419/2006, art. 4º, §§ 3º e 4º, e o CPC, arts. 219, 220 e 224. Os itens que vencem em até 3 dias úteis recebem 🔴 e aparecem primeiro. Quando o texto não traz o prazo, está truncado ou sob sigilo, a tabela diz **VERIFICAR MANUALMENTE**. A skill nunca inventa prazo.
- **Agendamento.** Cria duas captações automáticas nos dias úteis, às 07h e às 17h, com o resumo do dia.

> ⚠️ A triagem é automática e serve de apoio. Ela **não substitui a conferência do advogado** nos autos e no calendário do tribunal.

## Como instalar

**Opção 1, pedindo ao Claude.** No Claude Code ou no app desktop, diga:

> Instale a skill do repositório https://github.com/pedro1c201377-star/skill-controladoria-djen e configure para mim.

**Opção 2, manual.** Baixe o repositório e copie a pasta `controladoria-djen` para a pasta de skills do Claude:

- Windows: `C:\Users\<seu usuário>\.claude\skills\controladoria-djen`
- Mac/Linux: `~/.claude/skills/controladoria-djen`

Depois diga ao Claude: **"configure a controladoria do DJEN"**.

## Primeira configuração (o Claude conduz)

1. Você informa a OAB e a UF. O nome completo é descoberto nas próprias publicações.
2. O Claude cria a pasta `controladoria-djen` na Área de Trabalho e grava a configuração.
3. O Claude acrescenta os feriados do seu tribunal ao `feriados.txt`. O arquivo já vem com os nacionais.
4. Ele faz um teste com os últimos 7 dias e mostra a tabela de prazos.
5. Ele cria as tarefas `controladoria-djen-manha` e `controladoria-djen-tarde`. Você só aprova o que aparecer na tela.

Requisito: Python 3. Se não estiver instalado, o Claude instala ou explica como instalar.

## Versão para o Codex (OpenAI)

A pasta `codex/controladoria-djen` traz a mesma skill adaptada para o Codex CLI.

**Instalação.** Copie `codex/controladoria-djen` para a pasta de skills do Codex:

- Windows: `C:\Users\<seu usuário>\.agents\skills\controladoria-djen`
- Mac/Linux: `~/.agents/skills/controladoria-djen`

Versões antigas do Codex usavam `~/.codex/skills`. Reinicie o Codex e diga: **"$controladoria-djen configure a controladoria do DJEN"**.

**Agendamento automático.** Na configuração, a skill cria sozinha as tarefas `controladoria-djen-manha` (07h) e `controladoria-djen-tarde` (17h), de segunda a sexta:

- **App desktop do Codex/ChatGPT:** usa as *Scheduled tasks* nativas do app. Para a captação acessar a API do DJEN, libera só o comando de captação fora do sandbox, sem colocar a tarefa em acesso total.
- **Só o Codex CLI:** cria as tarefas no **Agendador de Tarefas do Windows** ou no **crontab** do Mac/Linux. Cada uma roda `codex exec` com a skill.

Nos dois casos, o resumo do dia vai para `relatorios/prazos-AAAA-MM-DD-<turno>.md` e o computador precisa estar ligado no horário.

## Uso diário

As tarefas agendadas entregam o resumo do dia sozinhas, com os urgentes primeiro. Você também pode pedir a qualquer momento: *"capte as publicações do DJEN e faça a triagem de prazos"*.

Seus dados ficam só no seu computador, em `controladoria-djen/dados/`: `publicacoes.csv` (abre no Excel), o texto completo em `publicacoes.jsonl` e os relatórios em `relatorios/`.

## Limitações

- As tarefas agendadas só rodam com o computador ligado e o app do Claude aberto. Se o app estiver fechado no horário, a tarefa roda quando ele for aberto.
- Feriados municipais e suspensões locais só entram na contagem se estiverem no `feriados.txt`.
- Em processos do eproc ou do PJe, a intimação pelo portal pode ter uma data diferente da do DJEN. Confira no sistema.
- A API do DJEN é do CNJ e pode mudar sem aviso.

## Estrutura

```
controladoria-djen/           versão Claude
├── SKILL.md                  instruções para o Claude
├── references/regras-prazos.md
└── scripts/
    ├── configurar.py         cria a pasta de trabalho e o config.json
    ├── captar.py             captação incremental
    └── feriados.txt          feriados nacionais (modelo)
codex/controladoria-djen/     versão Codex (os mesmos arquivos, mais:)
└── scripts/
    ├── agendar.py            cria as tarefas no Agendador do Windows ou no crontab
    └── rodar_agendado.py     execução agendada: pula feriados e chama codex exec
```
