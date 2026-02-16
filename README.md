# data-driven

Aprender análisis de datos orientado a un **motor de promociones** en una plataforma de apuestas. El objetivo es construir dashboards en Databricks y scripts de análisis.

## Modelo de datos

```
users              → Base de usuarios (segmento, país, registro)
promotions         → Catálogo de promos (tipo, reglas, recurrencia)
funnel             → Funnel por usuario×promo (eligible → opt-in → participate → win → redeem)
bets               → Historial de apuestas (orgánicas + promo)
daily_activity     → Actividad diaria por usuario (activo, stake, productos)
```

## Quick start (Databricks)

1. Conecta este repo a tu workspace de Databricks (Repos > Add Repo)
2. Abre `notebooks/00_generate_data.py` y ejecuta las celdas en orden
3. Las 5 tablas se crean automáticamente en Spark
4. Abre las queries de `analysis/` y ejecútalas

### Alternativa: ejecución local

```bash
pip install -r requirements.txt
python scripts/generate_data.py                  # 2000 usuarios, 12 semanas
python scripts/generate_data.py --users 10000    # más usuarios
```

## Queries de análisis

| Archivo | Descripción |
|---------|-------------|
| `analysis/00_load_data.sql` | Carga CSVs en tablas de Databricks |
| `analysis/01_funnel_analysis.sql` | Funnel de conversión por tipo de promo y segmento |
| `analysis/02_cohort_analysis.sql` | Cohortes semanales y matriz de retención |
| `analysis/03_promo_vs_no_promo.sql` | Comparativa promo users vs no-promo: active days, stake, retención, productos |
| `analysis/04_temp_tables_tutorial.sql` | Tutorial paso a paso: crear temp views combinando tablas |

## Métricas clave

- **Active days**: días activos por usuario
- **Stake**: volumen de apuestas
- **Retention**: retención semanal
- **Product diversity**: número de productos consumidos (sports, casino, live, etc.)
- **Funnel conversion**: tasas de conversión en cada paso del funnel
- **Promo uplift**: incremento en métricas cuando el usuario participa en promos
