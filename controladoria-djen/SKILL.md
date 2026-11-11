---
name: controladoria-djen
description: Controladoria de prazos para advogados a partir do DJEN (Diário de Justiça Eletrônico Nacional, comunicaapi.pje.jus.br). Capta as publicações e intimações pela OAB de forma incremental, sem duplicar, com filtro anti-homônimo; lê cada uma e entrega a tabela de prazos (partes, ato, determinação, prazo em dias úteis com fundamento, vencimento, providência, alerta 🔴 do que vence em até 3 dias úteis); e agenda a captação de manhã e à tarde. Use sempre que um advogado pedir para configurar ou rodar a captação do DJEN, buscar publicações ou intimações pela OAB, fazer triagem ou controladoria de prazos, montar o resumo do dia de intimações, ou instalar e começar a usar esta skill, mesmo que não diga "DJEN".
---

# Controladoria DJEN

Esta skill transforma o Claude no controlador de prazos de um advogado. Ela capta as publicações do DJEN pela OAB, separa o que é novo, lê cada texto e entrega uma tabela de prazos com os urgentes primeiro. Tudo roda no computador do advogado: os dados dele ficam na pasta de trabalho e nunca vão para esta skill nem para o repositório dela.

A tabela é apoio. Um prazo inventado pode custar uma causa, então a regra de ouro é: na dúvida, **VERIFICAR MANUALMENTE**.

## Qual fluxo seguir

1. Procure uma pasta de trabalho já configurada (com `config.json` e `captar.py`). Se o advogado não disser onde está, confira `~/Desktop/controladoria-djen`, `~/Área de Trabalho/controladoria-djen` e `~/controladoria-djen`.
2. **Não achou:** siga a "Primeira configuração".
3. **Achou:** siga a "Captação e triagem".

## Primeira configuração

Faça você mesmo tudo o que puder e só peça ao advogado o que só ele sabe ou só ele pode aprovar. Comece mostrando o roteiro curto abaixo, para ele saber o que vai acontecer:

> Vou deixar sua controladoria pronta em 5 passos: (1) seus dados de OAB, (2) a pasta e a configuração, (3) um teste com os últimos 7 dias, (4) a tabela de prazos desse teste e (5) a captação automática às 07h e às 17h nos dias úteis. Só preciso que você me informe o número da OAB e a UF e que aprove o que aparecer na tela.

**Passo 1, dados.** Pergunte só o número da OAB e a UF, por exemplo "123456/MG". Não peça o nome completo: o script descobre esse nome nas publicações. Se o advogado tiver inscrição em mais de uma UF, configure uma pasta para cada uma (`--pasta .../controladoria-djen-sp`).

**Passo 2, pasta e configuração.** Confira se o Python 3 está instalado (`python --version` ou `py --version`). Se não estiver, instale-o você mesmo (`winget install Python.Python.3.12` no Windows, `brew install python` no Mac) e, se não conseguir, diga ao advogado exatamente o que instalar. Depois rode:

```bash
python "<pasta-desta-skill>/scripts/configurar.py" --oab <NUMERO> --uf <uf>
```

O script cria a pasta de trabalho (por padrão `Desktop/controladoria-djen`), copia `captar.py`, `feriados.txt` e `regras-prazos.md` e grava o `config.json` com o nome completo encontrado na API. Mostre o nome ao advogado e peça só uma confirmação ("É assim que seu nome aparece nas publicações?"). Se o nome vier vazio, porque não houve publicações em 60 dias, pergunte o nome completo e rode de novo com `--nome "NOME COMPLETO"`. O nome serve para o filtro anti-homônimo.

**Passo 3, feriados.** O `feriados.txt` vem só com os feriados nacionais. Pergunte em qual tribunal e em quais comarcas o advogado mais atua. Procure na internet o calendário oficial de feriados e suspensões desse tribunal no ano corrente e acrescente as datas que encontrar no arquivo, sempre citando a fonte. Se não achar uma fonte oficial, não chute: avise o advogado.

**Passo 4, teste.** Rode `python captar.py --dias 7` dentro da pasta de trabalho. Em seguida faça a "Captação e triagem" (a partir do item 3) sobre as publicações captadas, para o advogado ver o resultado real. Informe também quantas foram descartadas como homônimo.

**Passo 5, agendamento.** Crie duas tarefas agendadas com a ferramenta de tarefas agendadas do Claude (`create_scheduled_task`), se estiver disponível:

- `controladoria-djen-manha`, cron `0 7 * * 1-5`
- `controladoria-djen-tarde`, cron `0 17 * * 1-5`

Use como instrução de cada uma o texto abaixo, trocando a pasta e o turno:

```
Capte as publicações do DJEN desde a última captação, faça a triagem de prazos e me entregue o resumo do dia, urgentes primeiro.

(Use a skill controladoria-djen. Pasta de trabalho: <PASTA>. Turno: manha. Se hoje estiver em feriados.txt, não rode e apenas avise.)
```

Se a ferramenta não existir ou a criação for bloqueada, passe ao advogado os nomes, os horários e o texto acima para ele criar as tarefas pela aba de tarefas agendadas do app do Claude. Explique três pontos: as tarefas só rodam com o computador ligado e o app aberto, e se o app estiver fechado no horário elas rodam quando ele for aberto; vale clicar em "Run now" uma vez e aprovar o que aparecer, para as próximas execuções não pararem pedindo permissão; e o cron não sabe de feriados, por isso a instrução manda conferir o `feriados.txt`.

Termine com um resumo do que ficou pronto e do que ainda depende dele.

## Captação e triagem

1. Se hoje estiver no `feriados.txt` e a execução for agendada, apenas avise e encerre.
2. Na pasta de trabalho, rode `python captar.py`. O script busca desde a última captação, pagina os resultados, não duplica (guarda os ids) e, se receber HTTP 429, espera 60 s e continua. Os ids novos ficam em `dados/ultima_execucao.json` e os registros completos em `dados/publicacoes.jsonl`, com processo, tribunal, órgão, data, tipo de ato, partes, advogados e texto completo.
3. Leia `regras-prazos.md` da pasta de trabalho (ou `references/regras-prazos.md` desta skill) e aplique as regras. Elas trazem a contagem pela Lei 11.419/2006, art. 4º, §§ 3º e 4º, e pelo CPC, arts. 219, 220 e 224, a origem do prazo, VERIFICAR MANUALMENTE, os 🔴 e as colunas da tabela.
4. Leia o texto completo de cada publicação nova, sem o HTML. Para cada uma, entenda o que foi determinado, para quem foi e se há prazo para o cliente.
5. Entregue o resumo do dia:
   - uma linha de abertura com quantas publicações são novas, quantas são 🔴 e qual é o próximo vencimento;
   - a tabela, com os urgentes primeiro;
   - o que não foi possível confirmar;
   - o aviso de que a triagem não substitui a conferência do advogado.
6. Salve o resumo em `relatorios/prazos-AAAA-MM-DD-<turno>.md` na pasta de trabalho.

Se não houver publicação nova, diga isso em uma linha e salve o relatório mesmo assim, para ficar registrado que a captação rodou.

## Cuidados

- Os dados do advogado (OAB, nome, processos, partes) ficam só na pasta de trabalho dele. Não os copie para a pasta desta skill nem para nenhum outro lugar.
- Mantenha sempre o filtro anti-homônimo. Na primeira captação, ou se o filtro descartar muitas publicações, mostre ao advogado alguns exemplos descartados (`dados/descartadas.jsonl`) para ele confirmar.
- A API é pública e não exige login. Não peça senha nem certificado ao advogado.
