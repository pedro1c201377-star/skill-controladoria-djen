---
name: controladoria-djen
description: Controladoria de prazos para advogados a partir do DJEN (Diário de Justiça Eletrônico Nacional, comunicaapi.pje.jus.br). Capta as publicações e intimações pela OAB de forma incremental, sem duplicar e com filtro anti-homônimo, lê cada uma e entrega a tabela de prazos (partes, ato, determinação, prazo em dias úteis com fundamento, vencimento, providência, alerta 🔴 do que vence em até 3 dias úteis). Também agenda a captação às 07h e às 17h. Use quando o advogado pedir para configurar ou rodar a captação do DJEN, buscar intimações pela OAB, fazer triagem ou controladoria de prazos, montar o resumo do dia, ou instalar e começar a usar esta skill.
---

# Controladoria DJEN (Codex)

Esta skill transforma o Codex no controlador de prazos de um advogado. Ela capta as publicações do DJEN pela OAB, separa o que é novo, lê cada texto e entrega uma tabela de prazos com os urgentes primeiro. Tudo roda no computador do advogado: os dados dele ficam na pasta de trabalho e nunca vão para esta skill nem para o repositório dela.

A tabela é apoio. Um prazo inventado pode custar uma causa, então a regra de ouro é: na dúvida, **VERIFICAR MANUALMENTE**.

Os scripts citados abaixo ficam na pasta `scripts/` desta skill. O caminho dela aparece na lista de skills do Codex.

## Qual fluxo seguir

1. Se a instrução trouxer "Pasta de trabalho: ...", use essa pasta. Esse é o caso da execução agendada.
2. Se não trouxer, procure uma pasta já configurada (com `config.json` e `captar.py`) em `~/Desktop/controladoria-djen`, `~/Área de Trabalho/controladoria-djen` e `~/controladoria-djen`.
3. **Não achou:** siga a "Primeira configuração".
4. **Achou:** siga a "Captação e triagem".

## Primeira configuração

Faça você mesmo tudo o que puder e só peça ao advogado o que só ele sabe ou só ele pode aprovar. Comece mostrando o roteiro:

> Vou deixar sua controladoria pronta em 5 passos: (1) seus dados de OAB, (2) a pasta e a configuração, (3) um teste com os últimos 7 dias, (4) a tabela de prazos desse teste e (5) a captação automática às 07h e às 17h nos dias úteis. Só preciso que você me informe o número da OAB e a UF e que aprove os comandos quando eu pedir.

A configuração precisa de acesso à internet (API do DJEN) e de permissão para gravar fora da pasta atual (na Área de Trabalho e no agendador do sistema). Se o sandbox bloquear um comando, peça aprovação ao advogado para aquele comando. Não desligue o sandbox por conta própria.

**Passo 1, dados.** Pergunte só o número da OAB e a UF, por exemplo "123456/MG". O nome completo o script descobre nas publicações.

**Passo 2, pasta e configuração.** Confira se o Python 3 está instalado (`python --version` ou `py --version`). Se não estiver, instale-o você mesmo (`winget install Python.Python.3.12` no Windows, `brew install python` no Mac) ou diga ao advogado exatamente o que instalar. Depois rode:

```bash
python "<pasta-desta-skill>/scripts/configurar.py" --oab <NUMERO> --uf <uf>
```

O script cria a pasta de trabalho (por padrão `Desktop/controladoria-djen`), copia `captar.py`, `rodar_agendado.py`, `feriados.txt` e `regras-prazos.md` e grava o `config.json` com o nome completo encontrado na API. Mostre o nome ao advogado e peça só uma confirmação. Se o nome vier vazio, pergunte o nome completo e rode de novo com `--nome "NOME COMPLETO"`. O nome serve para o filtro anti-homônimo.

**Passo 3, feriados.** O `feriados.txt` vem só com os feriados nacionais. Pergunte em qual tribunal e em quais comarcas o advogado mais atua. Procure o calendário oficial de feriados e suspensões desse tribunal no ano corrente e acrescente as datas ao arquivo, sempre citando a fonte. Se não achar uma fonte oficial, não chute: avise o advogado.

**Passo 4, teste.** Rode `python captar.py --dias 7` dentro da pasta de trabalho. Em seguida faça a "Captação e triagem" (a partir do item 3) sobre as publicações captadas. Informe também quantas foram descartadas como homônimo.

**Passo 5, agendamento.** Crie as duas tarefas você mesmo, sem pedir que o advogado faça nada além de aprovar o que aparecer. Antes, verifique qual caminho está disponível nesta sessão e siga o primeiro que funcionar.

*Caminho A, agendamento nativo do Codex (preferido).* O app desktop (Codex/ChatGPT) tem "Scheduled tasks", e o próprio agente consegue criá-las a partir da conversa. Confira se você tem uma ferramenta ou um comando de tarefas agendadas disponível. Na dúvida, consulte a documentação atual do Codex sobre scheduled tasks/automations. Se tiver, crie:
- `controladoria-djen-manha`: `RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR;BYHOUR=7;BYMINUTE=0`
- `controladoria-djen-tarde`: `RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR;BYHOUR=17;BYMINUTE=0`

Em cada uma, use a pasta de trabalho como projeto (sem worktree, para os dados ficarem na própria pasta), faça cada execução começar uma conversa nova e use esta instrução:

```
Use a skill $controladoria-djen. Capte as publicações do DJEN desde a última captação, faça a triagem de prazos e me entregue o resumo do dia, urgentes primeiro. Pasta de trabalho: <PASTA>. Turno: manha. Se hoje estiver em feriados.txt, não rode e apenas avise.
```

As tarefas agendadas rodam sem supervisão, no sandbox padrão do advogado e sem pedir aprovação. No modo `workspace-write`, a rede fica bloqueada, e a captação precisa da API do DJEN. Para resolver, libere só o comando de captação. Se a versão do Codex aceitar "rules", crie uma regra que permita `python captar.py` fora do sandbox, conferindo a sintaxe na documentação atual. Se não aceitar, ative `[sandbox_workspace_write] network_access = true` em `~/.codex/config.toml`, avisando o advogado. Não ponha a tarefa em "Full access". Depois, dispare uma execução de teste ("Run now", se houver) e confira se o relatório saiu.

*Caminho B, agendador do sistema (Codex CLI ou sem agendamento nativo).* Rode:

```bash
python "<pasta-desta-skill>/scripts/agendar.py" --pasta "<PASTA>"
```

Isso cria as mesmas duas tarefas, de segunda a sexta, no Agendador de Tarefas do Windows ou no crontab do Mac/Linux. Cada execução roda `rodar_agendado.py`, que:
- pula os dias de `feriados.txt`;
- chama `codex exec` com esta skill, no sandbox `workspace-write`, com rede liberada só para essa execução;
- salva o resumo em `relatorios/prazos-AAAA-MM-DD-<turno>.md`.

Para conferir sem esperar o horário, rode uma vez `python rodar_agendado.py --turno manha` na pasta de trabalho. Esse caminho exige o Codex CLI instalado e logado. Se ele não estiver, instale você mesmo (`npm install -g @openai/codex`) e peça ao advogado apenas o `codex login`.

Use um caminho só, para não captar em dobro. Ao final, diga ao advogado qual foi usado e explique:
- o computador precisa estar ligado no horário, e no caminho A o app também precisa estar aberto;
- o resumo do dia fica na pasta `relatorios` (no caminho A, também na aba Scheduled do app);
- como remover as tarefas: pela aba Scheduled no caminho A, ou com `agendar.py --pasta "<PASTA>" --remover` no caminho B.

Termine com um resumo do que ficou pronto e do que ainda depende dele.

## Captação e triagem

1. Na pasta de trabalho, rode `python captar.py`. O script busca desde a última captação, pagina, não duplica (guarda os ids) e, se receber HTTP 429, espera 60 s e continua. Os ids novos ficam em `dados/ultima_execucao.json` e os registros completos em `dados/publicacoes.jsonl`, com processo, tribunal, órgão, data, tipo de ato, partes, advogados e texto completo.
2. Se a rede estiver bloqueada pelo sandbox, diga isso com clareza. Não invente resultado.
3. Leia `regras-prazos.md` da pasta de trabalho (ou `references/regras-prazos.md` desta skill) e aplique as regras: a contagem pela Lei 11.419/2006, art. 4º, §§ 3º e 4º, e pelo CPC, arts. 219, 220 e 224, a origem do prazo, VERIFICAR MANUALMENTE, os 🔴 e as colunas da tabela.
4. Leia o texto completo de cada publicação nova, sem o HTML. Para cada uma, entenda o que foi determinado, para quem foi e se há prazo para o cliente.
5. Entregue o resumo do dia em Markdown:
   - uma linha de abertura com quantas publicações são novas, quantas são 🔴 e qual é o próximo vencimento;
   - a tabela, com os urgentes primeiro;
   - o que não foi possível confirmar;
   - o aviso de que a triagem não substitui a conferência do advogado.
6. Numa execução interativa, salve também em `relatorios/prazos-AAAA-MM-DD-<turno>.md`. Na agendada, o `rodar_agendado.py` já grava a sua resposta final nesse arquivo, então a resposta final deve ser o próprio resumo.

Se não houver publicação nova, diga isso em uma linha.

## Cuidados

- Os dados do advogado (OAB, nome, processos, partes) ficam só na pasta de trabalho dele. Não os copie para a pasta desta skill nem para nenhum outro lugar.
- Mantenha sempre o filtro anti-homônimo. Na primeira captação, ou se o filtro descartar muitas publicações, mostre alguns exemplos de `dados/descartadas.jsonl` para o advogado confirmar.
- A API do DJEN é pública e não exige login. Não peça senha nem certificado.
