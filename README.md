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

## Quick start

```bash
# Instalar dependencias
pip install -r requirements.txt

# Generar datos sintéticos (2000 usuarios, 12 semanas)
python scripts/generate_data.py

# Opciones: más usuarios o más semanas
python scripts/generate_data.py --users 10000 --weeks 26
```

Los CSVs se generan en `data/`. Súbelos a Databricks y usa `analysis/00_load_data.sql` para crear las tablas.

## Queries de análisis

| Archivo | Descripción |
|---------|-------------|
| `analysis/00_load_data.sql` | Carga CSVs en tablas de Databricks |
| `analysis/01_funnel_analysis.sql` | Funnel de conversión por tipo de promo y segmento |
| `analysis/02_cohort_analysis.sql` | Cohortes semanales y matriz de retención |
| `analysis/03_promo_vs_no_promo.sql` | Comparativa promo users vs no-promo: active days, stake, retención, productos |

## Métricas clave

- **Active days**: días activos por usuario
- **Stake**: volumen de apuestas
- **Retention**: retención semanal
- **Product diversity**: número de productos consumidos (sports, casino, live, etc.)
- **Funnel conversion**: tasas de conversión en cada paso del funnel
- **Promo uplift**: incremento en métricas cuando el usuario participa en promos
