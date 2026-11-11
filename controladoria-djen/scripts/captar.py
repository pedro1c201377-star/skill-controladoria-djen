"""Captação incremental de publicações do DJEN (comunicaapi.pje.jus.br) por OAB.

Lê a configuração de config.json na mesma pasta deste script (criado por configurar.py):
    {"oab": "123456", "uf": "mg", "nome_completo": "NOME COMPLETO DO ADVOGADO"}

Uso:
    python captar.py              # busca desde a última captação (na 1ª vez, últimos 7 dias)
    python captar.py --dias 7     # força a janela dos últimos N dias

Saídas (pasta dados/ ao lado deste script):
    publicacoes.jsonl   publicações aceitas, uma por linha, com texto completo e partes
    descartadas.jsonl   descartadas pelo filtro anti-homônimo
    publicacoes.csv     planilha resumida (abre no Excel)
    estado.json         última data captada e ids já vistos (evita duplicar)
    ultima_execucao.json  ids novos da última execução (para a triagem de prazos)
"""
import argparse
import csv
import json
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

API = "https://comunicaapi.pje.jus.br/api/v1/comunicacao"
ITENS_POR_PAGINA = 100
ESPERA_429 = 60
DIAS_PRIMEIRA_CAPTACAO = 7

BASE = Path(__file__).resolve().parent
CONFIG = BASE / "config.json"
DADOS = BASE / "dados"
ESTADO = DADOS / "estado.json"
ACEITAS = DADOS / "publicacoes.jsonl"
DESCARTADAS = DADOS / "descartadas.jsonl"
CSV = DADOS / "publicacoes.csv"
ULTIMA = DADOS / "ultima_execucao.json"


def normalizar(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.upper().split())


def carregar_config() -> dict:
    if not CONFIG.exists():
        sys.exit("config.json não encontrado. Rode antes: python configurar.py --oab NUMERO --uf UF")
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    cfg["oab"] = str(cfg["oab"]).strip().lstrip("0")
    cfg["uf"] = str(cfg["uf"]).strip().lower()
    cfg["nome_completo"] = (cfg.get("nome_completo") or "").strip()
    return cfg


def carregar_estado() -> dict:
    if ESTADO.exists():
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    return {"ultima_data": None, "ids_vistos": []}


def salvar_json(caminho: Path, dados) -> None:
    tmp = caminho.with_suffix(".tmp")
    tmp.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(caminho)


def buscar_pagina(cfg: dict, inicio: str, fim: str, pagina: int) -> dict:
    params = {
        "numeroOab": cfg["oab"],
        "ufOab": cfg["uf"],  # a API aceita a UF em minúsculo
        "dataDisponibilizacaoInicio": inicio,
        "dataDisponibilizacaoFim": fim,
        "pagina": pagina,
        "itensPorPagina": ITENS_POR_PAGINA,
    }
    url = API + "?" + urllib.parse.urlencode(params)
    tentativas = 0
    while True:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "controladoria-djen/1.0", "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"  HTTP 429 (limite de requisições). Aguardando {ESPERA_429}s e continuando...")
                time.sleep(ESPERA_429)
                continue
            tentativas += 1
            if tentativas > 3 or e.code < 500:
                raise
            time.sleep(5 * tentativas)
        except (urllib.error.URLError, TimeoutError):
            tentativas += 1
            if tentativas > 3:
                raise
            time.sleep(5 * tentativas)


def classificar(item: dict, cfg: dict) -> tuple[bool, str]:
    """Filtro anti-homônimo: aceita se o texto traz o nome completo ou o número da OAB;
    se o texto não traz (listas de distribuição, intimações curtas), aceita quando a lista
    estruturada de advogados da própria comunicação tem a mesma OAB e UF."""
    texto = normalizar(item.get("texto", ""))
    if cfg["nome_completo"] and normalizar(cfg["nome_completo"]) in texto:
        return True, "nome completo no texto"
    if cfg["oab"] in texto.replace(".", ""):
        return True, "OAB no texto"
    for d in item.get("destinatarioadvogados") or []:
        adv = d.get("advogado") or {}
        if str(adv.get("numero_oab", "")).lstrip("0") == cfg["oab"] and str(adv.get("uf_oab", "")).lower() == cfg["uf"]:
            return True, "OAB/UF na lista de advogados da comunicação"
    return False, "nem nome completo nem OAB/UF"


def registro(item: dict, motivo: str) -> dict:
    advs = []
    for d in item.get("destinatarioadvogados") or []:
        a = d.get("advogado") or {}
        advs.append(f"{a.get('nome')} OAB {a.get('numero_oab')}/{a.get('uf_oab')}")
    return {
        "id": item.get("id"),
        "processo": item.get("numeroprocessocommascara") or item.get("numero_processo"),
        "tribunal": item.get("siglaTribunal"),
        "orgao": item.get("nomeOrgao"),
        "data_disponibilizacao": item.get("data_disponibilizacao"),
        "tipo_ato": item.get("tipoComunicacao"),
        "tipo_documento": item.get("tipoDocumento"),
        "classe": item.get("nomeClasse"),
        "polo_ativo": [d.get("nome") for d in item.get("destinatarios") or [] if d.get("polo") == "A"],
        "polo_passivo": [d.get("nome") for d in item.get("destinatarios") or [] if d.get("polo") == "P"],
        "advogados": advs,
        "link": item.get("link"),
        "texto": item.get("texto"),
        "criterio": motivo,
        "captado_em": datetime.now().isoformat(timespec="seconds"),
    }


def anexar(caminho: Path, regs: list) -> None:
    with caminho.open("a", encoding="utf-8") as f:
        for r in regs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def gerar_csv() -> None:
    if not ACEITAS.exists():
        return
    linhas = [json.loads(l) for l in ACEITAS.read_text(encoding="utf-8").splitlines() if l.strip()]
    linhas.sort(key=lambda r: (r.get("data_disponibilizacao") or "", r.get("id") or 0), reverse=True)
    campos = ["data_disponibilizacao", "tribunal", "processo", "polo_ativo", "polo_passivo", "orgao", "tipo_ato", "classe", "criterio", "link", "texto"]
    for r in linhas:
        for k in ("polo_ativo", "polo_passivo"):
            r[k] = " / ".join(r.get(k) or [])
    with CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos, delimiter=";", extrasaction="ignore")
        w.writeheader()
        w.writerows(linhas)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dias", type=int, help="buscar os últimos N dias")
    args = ap.parse_args()

    cfg = carregar_config()
    DADOS.mkdir(exist_ok=True)
    estado = carregar_estado()
    vistos = set(estado["ids_vistos"])
    hoje = date.today()

    if args.dias:
        inicio = hoje - timedelta(days=args.dias)
    elif estado["ultima_data"]:
        inicio = date.fromisoformat(estado["ultima_data"])  # repete o último dia; o dedupe evita duplicar
    else:
        inicio = hoje - timedelta(days=DIAS_PRIMEIRA_CAPTACAO)

    print(f"Buscando OAB {cfg['oab']}/{cfg['uf'].upper()} de {inicio} a {hoje}...")
    aceitas, descartadas, repetidas, total, pagina = [], [], 0, 0, 1
    while True:
        dados = buscar_pagina(cfg, inicio.isoformat(), hoje.isoformat(), pagina)
        itens = dados.get("items") or []
        total = dados.get("count", total) or 0
        for item in itens:
            if item.get("id") in vistos:
                repetidas += 1
                continue
            vistos.add(item.get("id"))
            ok, motivo = classificar(item, cfg)
            (aceitas if ok else descartadas).append(registro(item, motivo))
        if not itens or pagina * ITENS_POR_PAGINA >= total:
            break
        pagina += 1

    anexar(ACEITAS, aceitas)
    anexar(DESCARTADAS, descartadas)
    gerar_csv()
    estado.update({
        "ultima_data": max(filter(None, [estado["ultima_data"], hoje.isoformat()])),
        "ids_vistos": sorted(vistos),
        "ultima_execucao": datetime.now().isoformat(timespec="seconds"),
    })
    salvar_json(ESTADO, estado)
    salvar_json(ULTIMA, {"executado_em": estado["ultima_execucao"], "ids_novos": [r["id"] for r in aceitas]})

    print(f"Total na API: {total} | novas aceitas: {len(aceitas)} | descartadas (homônimo): {len(descartadas)} | já captadas antes: {repetidas}")
    for r in sorted(aceitas, key=lambda r: r["data_disponibilizacao"] or "", reverse=True):
        print(f"  {r['data_disponibilizacao']} | {r['tribunal']} | {r['processo']} | {r['tipo_ato']} | {r['orgao']} | {r['criterio']}")


if __name__ == "__main__":
    main()
