"""
Simulación de equilibrio Relevamiento vs Instalación vs Stock (Zona A) - Licitación 5573.
Supuestos (ver informe):
  * Ritmo de instalación = promedio Zona A Nov-2025..Abr-2026 (SIGEC EQUIPOS, marcas CLOU+NSEN).
  * Ritmo de relevamiento = promedio Zona A mismo período (georef.relevamiento, SET '1000-%', DISTINCT rel_medidor_id).
  * Backlog inicial = relevados Zona A cuyo suministro hoy no es telemedible (snapshot 23/10/2026).
  * Stock = entregas publicadas (fecha Disp. con VP 20d) netas del cupo Interior y del 10% de reserva.
  * La instalación con stock de la licitación arranca con la primera disponibilidad (Feb-2027).
"""
import os, sys, json
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(BASE, "data", "tasas_instalacion_relevamiento.json"), encoding="utf-8"))

inst = pd.DataFrame(d["instalaciones_mensual"])
rel = pd.DataFrame(d["relevamiento_mensual"])
VENTANA = ["2025-11", "2025-12", "2026-01", "2026-02", "2026-03", "2026-04"]
TASA_INST = inst[inst["mes"].isin(VENTANA)]["ZONA_A"].mean()
TASA_REL = rel[rel["mes"].isin(VENTANA)]["n_medidores"].mean()
TASA_REL_RECIENTE = rel[rel["mes"].isin(["2026-05", "2026-06", "2026-07", "2026-08", "2026-09"])]["n_medidores"].mean()
BACKLOG0 = next(x["n"] for x in d["backlog_relevado_zona_a"] if x["estado"] == "PENDIENTE_INSTALAR")
RESERVA = 0.10
DEADLINE_MO = pd.Period("2028-01", "M")  # Plazo mano de obra OP 27132/27134 (25-01-2028)

# Entregas -> cupo Zona A (bruto), restando cupos Interior: SF 28k (S-E1/E2 prorrata), RC 13k (S-E4), VM 6k (S-E5), VA 800 (C-E3)
entregas = [
    ("Sanxing E1", "2027-02", 34000, 34000 - round(28000 * 34000 / 65000)),
    ("Sanxing E2", "2027-03", 31000, 31000 - round(28000 * 31000 / 65000)),
    ("CLOU E1",    "2027-03", 42000, 42000),
    ("Sanxing E3", "2027-04", 45000, 45000),
    ("Sanxing E4", "2027-05", 45000, 45000 - 13000),
    ("Sanxing E5", "2027-06", 45000, 45000 - 6000),
    ("CLOU E2",    "2027-09", 41500, 41500),
    ("CLOU E3",    "2027-10", 41500, 41500 - 800),
    ("CLOU E4",    "2027-12", 75000, 75000),
]
ent = pd.DataFrame(entregas, columns=["lote", "mes", "bruto", "zona_a_bruto"])
ent["zona_a_neto"] = (ent["zona_a_bruto"] * (1 - RESERVA)).round().astype(int)
META = int(ent["zona_a_neto"].sum())


def simular(tasa_inst, tasa_rel, etiqueta, hasta="2031-12"):
    meses = pd.period_range("2026-11", hasta, freq="M")
    stock_in = ent.groupby("mes")["zona_a_neto"].sum().to_dict()
    backlog, stock, inst_acum, rows = BACKLOG0, 0, 0, []
    for m in meses:
        k = str(m)
        stock += stock_in.get(k, 0)
        backlog += tasa_rel
        cap = tasa_inst if m >= pd.Period("2027-02", "M") else 0
        pend_meta = META - inst_acum
        instalado = min(cap, stock, backlog, pend_meta)
        limit = ("META" if instalado == pend_meta and pend_meta > 0 else
                 "SIN_ACTIVIDAD" if cap == 0 else
                 "STOCK" if instalado == stock and stock < cap else
                 "RELEVAMIENTO" if instalado == backlog and backlog < cap else "MANO_OBRA")
        stock -= instalado; backlog -= instalado; inst_acum += instalado
        rows.append(dict(escenario=etiqueta, mes=k, stock_ingresa=stock_in.get(k, 0), instalado=round(instalado),
                         instalado_acum=round(inst_acum), stock_ocioso=round(stock), backlog_relevado=round(backlog),
                         restriccion=limit))
        if inst_acum >= META:
            break
    return pd.DataFrame(rows)


# Ritmo requerido para cumplir el plazo de mano de obra (Feb-2027..Ene-2028 = 12 meses)
meses_plazo = (DEADLINE_MO - pd.Period("2027-02", "M")).n + 1
tasa_req = META / meses_plazo
rel_req = max(0, (META - BACKLOG0) / meses_plazo)

esc = {
    "A_ritmo_historico": simular(TASA_INST, TASA_REL, "A: Ritmo histórico (inst. y relev. Nov25-Abr26)"),
    "B_relev_reciente": simular(TASA_INST, TASA_REL_RECIENTE, "B: Inst. histórica + relev. reciente (May-Sep26)"),
    "C_ritmo_requerido": simular(tasa_req, rel_req, "C: Ritmo requerido para cerrar en Ene-2028", hasta="2028-12"),
}

print(f"Tasa instalación Zona A (Nov25-Abr26): {TASA_INST:,.0f}/mes")
print(f"Tasa relevamiento Zona A (Nov25-Abr26): {TASA_REL:,.0f}/mes | reciente May-Sep26: {TASA_REL_RECIENTE:,.0f}/mes")
print(f"Backlog relevado pendiente: {BACKLOG0:,} | Meta Zona A neta (90%): {META:,}")
print(f"Ritmo requerido p/ Ene-2028: inst {tasa_req:,.0f}/mes, relev {rel_req:,.0f}/mes")
print(ent)
for k, df in esc.items():
    fin = df.iloc[-1]
    print(f"\n=== {df['escenario'].iloc[0]} -> fin {fin['mes']} | acum {fin['instalado_acum']:,} ===")
    print(df.to_string(index=False))

pd.concat(esc.values()).to_csv(os.path.join(BASE, "data", "simulacion_equilibrio_zona_a.csv"), index=False, encoding="utf-8-sig")
json.dump(dict(tasa_instalacion_zona_a=round(TASA_INST), tasa_relevamiento_zona_a=round(TASA_REL),
               tasa_relevamiento_reciente=round(TASA_REL_RECIENTE), backlog_inicial=BACKLOG0, meta_zona_a_neta=META,
               tasa_instalacion_requerida=round(tasa_req), tasa_relevamiento_requerida=round(rel_req),
               entregas=ent.to_dict(orient="records"),
               fin_escenarios={k: v.iloc[-1].to_dict() for k, v in esc.items()}),
          open(os.path.join(BASE, "data", "simulacion_equilibrio_zona_a.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2, default=str)
