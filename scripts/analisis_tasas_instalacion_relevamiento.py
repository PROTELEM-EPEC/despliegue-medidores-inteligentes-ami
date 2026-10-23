"""
Análisis de tasas: Instalación MI (Nov-2025..Abr-2026) y Relevamiento Zona A (georef.relevamiento, SET '1000-%').
Salida: data/tasas_instalacion_relevamiento.json + CSVs mensuales.
"""
import os, sys, json, oracledb, pandas as pd, warnings
from dotenv import load_dotenv

warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 200)
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

load_dotenv(r"D:\Proyectos\.env")
load_dotenv(r"D:\Proyectos\antigravity-agents-repository\.env")
try:
    oracledb.init_oracle_client(lib_dir=os.environ.get("OR_INSTANT_CLIENT", r"C:\app\client\product\19.0.0\client_2\bin"))
except Exception:
    pass
dsn = oracledb.makedsn(host=os.environ["OR_HOST"], port=int(os.environ.get("OR_PORT", 1521)), service_name=os.environ["OR_SERVICE_NAME"])
conn = oracledb.connect(user=os.environ["OR_USER"], password=os.environ["OR_PASS"], dsn=dsn)

# 1) Instalaciones MI (CLOU / NSEN) por mes y zona comercial
inst = pd.read_sql("""
SELECT TO_CHAR(e.eqp_fecha_instal,'YYYY-MM') mes,
       CASE WHEN suc.zon_codigo = 'A' THEN 'ZONA_A' ELSE 'INTERIOR' END region,
       st.ste_marca marca,
       COUNT(DISTINCT e.srv_codigo) n
FROM xxsigec.equipos e
JOIN xxsigec.stock_equipos st ON st.ste_numero = e.ste_numero AND st.ste_tipo = e.ste_tipo
JOIN xxsigec.servicios s      ON s.srv_codigo = e.srv_codigo
JOIN xxsigec.sucursales suc   ON suc.scf_codigo = s.scf_codigo
WHERE e.ste_tipo = 'M'
  AND st.ste_marca IN ('CLOU','NSEN')
  AND e.eqp_fecha_instal >= DATE '2025-11-01' AND e.eqp_fecha_instal < DATE '2026-05-01'
GROUP BY TO_CHAR(e.eqp_fecha_instal,'YYYY-MM'),
         CASE WHEN suc.zon_codigo = 'A' THEN 'ZONA_A' ELSE 'INTERIOR' END, st.ste_marca
ORDER BY 1,2,3""", conn)
inst.columns = [c.lower() for c in inst.columns]
pv_inst = inst.pivot_table(index="mes", columns="region", values="n", aggfunc="sum", fill_value=0)
pv_inst["TOTAL"] = pv_inst.sum(axis=1)
print("=== 1. Instalaciones MI (CLOU+NSEN) por mes ===")
print(pv_inst)
print("\nPor marca:\n", inst.pivot_table(index="mes", columns="marca", values="n", aggfunc="sum", fill_value=0))

# 2) Relevamiento Zona A (SET '1000-%') por mes - COUNT(DISTINCT rel_medidor_id)
rel = pd.read_sql("""
SELECT TO_CHAR(rel_fecha_alta,'YYYY-MM') mes,
       COUNT(rel_medidor_id) n_registros,
       COUNT(DISTINCT rel_medidor_id) n_medidores
FROM georef.relevamiento
WHERE rel_subestacion LIKE '1000-%'
GROUP BY TO_CHAR(rel_fecha_alta,'YYYY-MM')
ORDER BY 1""", conn)
rel.columns = [c.lower() for c in rel.columns]
print("\n=== 2. Relevamiento Zona A por mes (SET 1000-*) ===")
print(rel)

# 3) Backlog: medidores relevados en Zona A cuyo suministro hoy NO es telemedible (frente disponible para instalar)
backlog = pd.read_sql("""
SELECT CASE WHEN s.srv_telemedible IN ('SI','SN') THEN 'YA_MI' ELSE 'PENDIENTE_INSTALAR' END estado,
       COUNT(DISTINCT r.rel_medidor_id) n
FROM georef.relevamiento r
LEFT JOIN xxsigec.servicios s ON s.srv_codigo = r.rel_suministro
WHERE r.rel_subestacion LIKE '1000-%'
GROUP BY CASE WHEN s.srv_telemedible IN ('SI','SN') THEN 'YA_MI' ELSE 'PENDIENTE_INSTALAR' END""", conn)
backlog.columns = [c.lower() for c in backlog.columns]
print("\n=== 3. Estado de lo relevado en Zona A ===")
print(backlog)

# Persistencia
inst.to_csv(os.path.join(OUT, "instalaciones_mi_mensual_2025-11_2026-04.csv"), index=False, encoding="utf-8-sig")
rel.to_csv(os.path.join(OUT, "relevamiento_zona_a_mensual.csv"), index=False, encoding="utf-8-sig")
json.dump({
    "instalaciones_mensual": pv_inst.reset_index().to_dict(orient="records"),
    "relevamiento_mensual": rel.to_dict(orient="records"),
    "backlog_relevado_zona_a": backlog.to_dict(orient="records"),
}, open(os.path.join(OUT, "tasas_instalacion_relevamiento.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2, default=str)
conn.close()
print("\nOK -> data/tasas_instalacion_relevamiento.json")
