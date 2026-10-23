"""
Plan Maestro Contractual de Despliegue AMI (Licitación 5573 / OP 27131-27134):
- Meta: 360.000 medidores inteligentes instalados al 25-01-2028 (12 meses: Feb-2027 a Ene-2028).
- Cupo Zona A: 316.980 medidores (88,05%).
- Cupo Interior: 43.020 medidores (11,95%):
  * Rio Cuarto (completo): 13.000 u.
  * San Francisco: 24.154 u. (proporcional)
  * Villa Maria: 5.176 u. (proporcional)
  * Villa Allende: 690 u. (proporcional)
- Relevamiento: estimado a 360.000 suministros con antelación mínima de 15 días (ejecución 1 mes previo).
"""
import os, sys, json
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DATA = os.path.join(BASE, "data")

meses = ['2027-02', '2027-03', '2027-04', '2027-05', '2027-06', '2027-07',
         '2027-08', '2027-09', '2027-10', '2027-11', '2027-12', '2028-01']

entregas_netas = [
    30600, 65700, 40500, 40500, 40500, 0, 0, 37350, 37350, 0, 67500, 0
]

# Detalle Interior
int_sf = [12500, 11654, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
int_rc = [0, 0, 0, 13000, 0, 0, 0, 0, 0, 0, 0, 0]
int_vm = [0, 0, 0, 0, 5176, 0, 0, 0, 0, 0, 0, 0]
int_va = [0, 0, 0, 0, 0, 0, 0, 0, 690, 0, 0, 0]
int_total = [sf + rc + vm + va for sf, rc, vm, va in zip(int_sf, int_rc, int_vm, int_va)]

# Instalación total mensual (balanceada con stock)
inst_tot = [30000, 30000, 30000, 30000, 30000, 30000, 30000, 30000, 30000, 22500, 33750, 33750]
inst_a = [tot - it for tot, it in zip(inst_tot, int_total)]

# Planes Zona A intervenidos por mes
planes_a_desc = [
    "Plan 18 (Oeste) - Arranque Sanxing",
    "Plan 18 (Cierre) + Plan 6 (Noreste CLOU)",
    "Plan 17 (Centro-Sur Aérea)",
    "Capital Cuencas Densas (Sanxing E4)",
    "Capital Cuencas Densas (Sanxing E5)",
    "Plan 17 Remanente / Otros Planes",
    "Capital Intervención Cuadrillas",
    "Plan 8 (Este CLOU E2)",
    "Plan 12 (Sureste CLOU E3)",
    "Capital Continuidad Cuadrillas",
    "Planes 14 y 15 (Centro GPRS Subterráneo)",
    "Planes 14 y 15 (Cierre Licitación)"
]

# Relevamiento anticipado (1 mes antes): Ene-2027 a Dic-2027
# Ene-2027 releva lo que se instala en Feb-2027 (cumple >= 15 días previos)
meses_rel = ['2027-01'] + meses[:-1]

df_master = []
stk_acum = 0
inst_tot_acum = 0
inst_a_acum = 0
inst_int_acum = 0
rel_tot_acum = 0
rel_a_acum = 0
rel_int_acum = 0

for i in range(12):
    m = meses[i]
    m_rel = meses_rel[i]
    ent = entregas_netas[i]
    stk_acum += ent
    
    i_tot = inst_tot[i]
    i_a = inst_a[i]
    i_int = int_total[i]
    
    inst_tot_acum += i_tot
    inst_a_acum += i_a
    inst_int_acum += i_int
    
    # Relevamiento ejecutado en m_rel para alimentar m
    r_tot = i_tot
    r_a = i_a
    r_int = i_int
    
    rel_tot_acum += r_tot
    rel_a_acum += r_a
    rel_int_acum += r_int
    
    stk_disponible = stk_acum - inst_tot_acum
    
    df_master.append({
        "mes_instalacion": m,
        "mes_relevamiento_previo": m_rel,
        "stock_neto_ingresado": ent,
        "stock_acumulado": stk_acum,
        "instalacion_zona_a": i_a,
        "instalacion_zona_a_acum": inst_a_acum,
        "instalacion_interior": i_int,
        "instalacion_interior_acum": inst_int_acum,
        "instalacion_total_mes": i_tot,
        "instalacion_total_acum": inst_tot_acum,
        "stock_disponible_almacen": stk_disponible,
        "relevamiento_zona_a": r_a,
        "relevamiento_zona_a_acum": rel_a_acum,
        "relevamiento_interior": r_int,
        "relevamiento_interior_acum": rel_int_acum,
        "relevamiento_total_mes": r_tot,
        "relevamiento_total_acum": rel_tot_acum,
        "distrito_interior_activo": ("San Francisco" if int_sf[i] > 0 else 
                                     "Río Cuarto" if int_rc[i] > 0 else 
                                     "Villa María" if int_vm[i] > 0 else 
                                     "Villa Allende" if int_va[i] > 0 else "-"),
        "plan_zona_a_activo": planes_a_desc[i]
    })

master_df = pd.DataFrame(df_master)
csv_path = os.path.join(OUT_DATA, "plan_maestro_despliegue_360k.csv")
json_path = os.path.join(OUT_DATA, "plan_maestro_despliegue_360k.json")

master_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(df_master, f, indent=2, ensure_ascii=False)

print("Master Plan 360k generado exitosamente:")
print(f"  CSV: {csv_path}")
print(f"  JSON: {json_path}")
print("\nResumen Final:")
print(f"  Instalación Total Acumulada: {inst_tot_acum:,} (Zona A: {inst_a_acum:,} | Interior: {inst_int_acum:,})")
print(f"  Relevamiento Total Acumulado: {rel_tot_acum:,} (Zona A: {rel_a_acum:,} | Interior: {rel_int_acum:,})")
print(f"  Stock Final Disponible (Reserva no computada): {stk_disponible:,} (Reserva 10% adicional: 40.000 u.)")
