"""Configura a controladoria DJEN para um advogado.

Cria a pasta de trabalho, copia os scripts, descobre o nome completo do advogado
nos dados da própria API (pela OAB/UF) e grava config.json.

Uso:
    python configurar.py --oab 123456 --uf mg [--nome "NOME COMPLETO"] [--pasta CAMINHO]

Pasta padrão: ~/Desktop/controladoria-djen (ou ~/controladoria-djen se não houver Desktop).
Saída: imprime um JSON com pasta, nome encontrado, candidatos e quantas publicações a API achou.
"""
import argparse
import json
import shutil
import sys
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

API = "https://comunicaapi.pje.jus.br/api/v1/comunicacao"
AQUI = Path(__file__).resolve().parent
UFS = {"ac", "al", "ap", "am", "ba", "ce", "df", "es", "go", "ma", "mt", "ms", "mg", "pa", "pb", "pr",
       "pe", "pi", "rj", "rn", "rs", "ro", "rr", "sc", "sp", "se", "to"}


def pasta_padrao() -> Path:
    home = Path.home()
    for nome in ("Desktop", "Área de Trabalho", "OneDrive/Desktop", "OneDrive/Área de Trabalho"):
        if (home / nome).is_dir():
            return home / nome / "controladoria-djen"
    return home / "controladoria-djen"


def candidatos_nome(oab: str, uf: str, dias: int = 60) -> tuple[Counter, int]:
    fim = date.today()
    params = {
        "numeroOab": oab, "ufOab": uf,
        "dataDisponibilizacaoInicio": (fim - timedelta(days=dias)).isoformat(),
        "dataDisponibilizacaoFim": fim.isoformat(),
        "pagina": 1, "itensPorPagina": 100,
    }
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params),
                                 headers={"User-Agent": "controladoria-djen/1.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        dados = json.loads(r.read().decode("utf-8"))
    nomes = Counter()
    for item in dados.get("items") or []:
        for d in item.get("destinatarioadvogados") or []:
            a = d.get("advogado") or {}
            if str(a.get("numero_oab", "")).lstrip("0") == oab and str(a.get("uf_oab", "")).lower() == uf:
                nomes[(a.get("nome") or "").strip().upper()] += 1
    return nomes, dados.get("count", 0)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--oab", required=True, help="número da OAB, só dígitos")
    ap.add_argument("--uf", required=True, help="UF da OAB, ex.: mg")
    ap.add_argument("--nome", help="nome completo como aparece nas publicações (opcional: é descoberto pela API)")
    ap.add_argument("--pasta", help="pasta de trabalho")
    args = ap.parse_args()

    oab = "".join(c for c in args.oab if c.isdigit()).lstrip("0")
    uf = args.uf.strip().lower()
    if not oab:
        sys.exit("OAB inválida: informe só os números.")
    if uf not in UFS:
        sys.exit(f"UF inválida: {args.uf}")

    pasta = Path(args.pasta).expanduser() if args.pasta else pasta_padrao()
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "dados").mkdir(exist_ok=True)
    (pasta / "relatorios").mkdir(exist_ok=True)
    shutil.copy2(AQUI / "captar.py", pasta / "captar.py")
    if not (pasta / "feriados.txt").exists():
        shutil.copy2(AQUI / "feriados.txt", pasta / "feriados.txt")
    regras = AQUI.parent / "references" / "regras-prazos.md"
    if regras.exists():
        shutil.copy2(regras, pasta / "regras-prazos.md")

    nomes, total = candidatos_nome(oab, uf)
    nome = (args.nome or "").strip().upper()
    if not nome and nomes:
        nome = nomes.most_common(1)[0][0]

    cfg = {"oab": oab, "uf": uf, "nome_completo": nome}
    (pasta / "config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")

    print(json.dumps({
        "pasta": str(pasta),
        "nome_completo": nome or None,
        "candidatos_na_api": dict(nomes.most_common()),
        "publicacoes_ultimos_60_dias": total,
        "aviso": None if nome else "Nome completo não encontrado na API: pergunte ao advogado e rode de novo com --nome.",
    }, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
