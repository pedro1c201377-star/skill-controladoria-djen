"""Execução agendada da controladoria DJEN pelo Codex.

Chamado pelo Agendador de Tarefas do Windows (ou cron) às 07h e às 17h nos dias úteis.
Se hoje estiver em feriados.txt, não faz nada. Senão, chama `codex exec` com a skill
controladoria-djen e salva o resumo do dia em relatorios/prazos-AAAA-MM-DD-<turno>.md.

Uso:
    python rodar_agendado.py --turno manha
    python rodar_agendado.py --turno tarde --dry-run   # só mostra o comando
"""
import argparse
import shutil
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

PASTA = Path(__file__).resolve().parent
INSTRUCAO = ("Use a skill $controladoria-djen. Capte as publicações do DJEN desde a última captação, "
             "faça a triagem de prazos e me entregue o resumo do dia, urgentes primeiro. "
             "Pasta de trabalho: {pasta}. Turno: {turno}.")


def feriado_hoje() -> bool:
    arq = PASTA / "feriados.txt"
    if not arq.exists():
        return False
    hoje = date.today().isoformat()
    return any(l.strip() == hoje for l in arq.read_text(encoding="utf-8").splitlines())


def log(msg: str) -> None:
    (PASTA / "relatorios").mkdir(exist_ok=True)
    with (PASTA / "relatorios" / "agendamento.log").open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat(timespec='seconds')} {msg}\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--turno", choices=["manha", "tarde"], required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if feriado_hoje():
        log(f"{args.turno}: feriado/suspensão em feriados.txt, não executado")
        print("Hoje está em feriados.txt: captação não executada.")
        return

    codex = shutil.which("codex") or shutil.which("codex.cmd")
    if not codex and not args.dry_run:
        log(f"{args.turno}: comando codex não encontrado no PATH")
        sys.exit("Codex CLI não encontrado. Instale com: npm install -g @openai/codex")

    relatorio = PASTA / "relatorios" / f"prazos-{date.today().isoformat()}-{args.turno}.md"
    cmd = [
        codex or "codex", "exec",
        "--cd", str(PASTA),
        "--skip-git-repo-check",
        "--sandbox", "workspace-write",
        "-c", "sandbox_workspace_write.network_access=true",  # a captação precisa acessar a API do DJEN
        "--output-last-message", str(relatorio),
        INSTRUCAO.format(pasta=PASTA, turno=args.turno),
    ]
    if args.dry_run:
        print(" ".join(f'"{c}"' if " " in c else c for c in cmd))
        return

    (PASTA / "relatorios").mkdir(exist_ok=True)
    r = subprocess.run(cmd, cwd=PASTA)
    log(f"{args.turno}: codex exec terminou com código {r.returncode}; relatório em {relatorio.name}")
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
