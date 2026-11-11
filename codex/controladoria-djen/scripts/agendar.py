"""Cria (ou remove) as tarefas controladoria-djen-manha (07h) e controladoria-djen-tarde (17h),
de segunda a sexta, no Agendador de Tarefas do Windows ou no crontab (Mac/Linux).

Uso:
    python agendar.py --pasta CAMINHO_DA_PASTA_DE_TRABALHO            # cria
    python agendar.py --pasta CAMINHO --dry-run                       # só mostra os comandos
    python agendar.py --pasta CAMINHO --remover                       # remove
"""
import argparse
import platform
import subprocess
import sys
from pathlib import Path

TAREFAS = {"controladoria-djen-manha": ("manha", "07:00", "0 7"), "controladoria-djen-tarde": ("tarde", "17:00", "0 17")}
MARCA = "# controladoria-djen"


def windows(pasta: Path, dry: bool, remover: bool) -> None:
    py = sys.executable.replace("python.exe", "pythonw.exe") if sys.executable.endswith("python.exe") else sys.executable
    for nome, (turno, hora, _) in TAREFAS.items():
        if remover:
            cmd = ["schtasks", "/Delete", "/TN", nome, "/F"]
        else:
            tr = f'"{py}" "{pasta / "rodar_agendado.py"}" --turno {turno}'
            cmd = ["schtasks", "/Create", "/TN", nome, "/TR", tr, "/SC", "WEEKLY",
                   "/D", "MON,TUE,WED,THU,FRI", "/ST", hora, "/F"]
        print(" ".join(cmd))
        if not dry:
            subprocess.run(cmd, check=True)


def unix(pasta: Path, dry: bool, remover: bool) -> None:
    atual = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
    linhas = [l for l in atual.splitlines() if MARCA not in l]
    if not remover:
        for nome, (turno, _, cron) in TAREFAS.items():
            linhas.append(f'{cron} * * 1-5 cd "{pasta}" && "{sys.executable}" rodar_agendado.py --turno {turno} {MARCA} {nome}')
    novo = "\n".join(linhas) + "\n"
    print(novo)
    if not dry:
        subprocess.run(["crontab", "-"], input=novo, text=True, check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pasta", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--remover", action="store_true")
    args = ap.parse_args()
    pasta = Path(args.pasta).expanduser().resolve()
    if not args.remover and not (pasta / "rodar_agendado.py").exists():
        sys.exit(f"rodar_agendado.py não está em {pasta}. Rode configurar.py antes.")
    (windows if platform.system() == "Windows" else unix)(pasta, args.dry_run, args.remover)
    if not args.dry_run:
        print("Tarefas " + ("removidas." if args.remover else "criadas: controladoria-djen-manha (07h) e controladoria-djen-tarde (17h), seg-sex."))


if __name__ == "__main__":
    main()
