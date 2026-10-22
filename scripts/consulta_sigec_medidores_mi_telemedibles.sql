-- ==========================================================================================
-- EPEC / PROTELEM - PLAN MAESTRO DE DESPLIEGUE AMI (LICITACIÓN 5573)
-- CONSULTA DE DIAGNÓSTICO HISTÓRICO Y PROSPECTIVO DE MEDIDORES TELEMEDIBLES (MI) EN SIGEC
-- ==========================================================================================
-- Propósito: Agrupar por Zona Comercial (zon_codigo), Distrito/Sucursal (scf_codigo), 
--            Plan de Lectura (grl_codigo) y Marca/Estado de Telemedición (srv_telemedible),
--            contando los suministros activos (srv_estado = 'SN') de Clientes Comunes (gse_grupo = 'CC').
--
-- Interpretación del campo SRV_TELEMEDIBLE:
--   'SI'  => Medidor Inteligente (MI) marca CLOU
--   'SN'  => Medidor Inteligente (MI) marca NANSEN o SANXING
--   Otros => Medidor Convencional NO MI (Electromecánico, Electrónico estándar o NULL)
-- ==========================================================================================

SELECT 
    suc.zon_codigo                                              AS zon_codigo,
    z.zon_descripcion                                           AS zona_descripcion,
    s.scf_codigo                                                AS scf_codigo,
    suc.scf_descripcion                                         AS distrito_sucursal,
    s.grl_codigo                                                AS grl_codigo,
    NVL(s.srv_telemedible, 'NO_MI')                             AS srv_telemedible,
    CASE 
        WHEN s.srv_telemedible = 'SI' THEN 'MI CLOU'
        WHEN s.srv_telemedible = 'SN' THEN 'MI NANSEN / SANXING'
        ELSE 'NO MI (Convencional)'
    END                                                         AS clasificacion_medidor,
    COUNT(s.srv_codigo)                                         AS cantidad_suministros
FROM xxsigec.servicios s
INNER JOIN xxsigec.sucursales suc 
    ON s.scf_codigo = suc.scf_codigo
LEFT JOIN xxsigec.zonas z 
    ON suc.zon_codigo = z.zon_codigo
WHERE s.srv_estado = 'SN'        -- Suministros en Servicio Normal (activos)
  AND s.gse_grupo = 'CC'         -- Clientes Comunes (tarifa residencial y comercial estándar)
GROUP BY 
    suc.zon_codigo,
    z.zon_descripcion,
    s.scf_codigo,
    suc.scf_descripcion,
    s.grl_codigo,
    NVL(s.srv_telemedible, 'NO_MI'),
    CASE 
        WHEN s.srv_telemedible = 'SI' THEN 'MI CLOU'
        WHEN s.srv_telemedible = 'SN' THEN 'MI NANSEN / SANXING'
        ELSE 'NO MI (Convencional)'
    END
ORDER BY 
    suc.zon_codigo,
    s.scf_codigo,
    TO_NUMBER(REGEXP_SUBSTR(s.grl_codigo, '^[0-9]+')),
    s.grl_codigo,
    cantidad_suministros DESC;
