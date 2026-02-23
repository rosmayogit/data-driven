"""
Tests unitarios — Lógica de campañas del BonusEngine
=====================================================

¿Qué es un test unitario en Python?
-------------------------------------
Un test unitario es una función que:
  1. Prepara unos datos de entrada (ARRANGE)
  2. Ejecuta la función que queremos probar (ACT)
  3. Comprueba que el resultado es el esperado (ASSERT)

Si la comprobación falla → pytest reporta el error y nos dice
exactamente qué salió mal y dónde.

Cómo ejecutarlos:
  pytest tests/                    # todos los tests
  pytest tests/ -v                 # verbose (muestra cada test)
  pytest tests/ -k "test_cohort"   # solo los que contengan "test_cohort"

Convenciones:
  - Archivos de test: test_*.py o *_test.py
  - Funciones de test: def test_*()
  - Clases de test: class Test* (opcional, para agrupar)
"""

import pytest
from datetime import date, timedelta


# ============================================================
# FUNCIONES DE DOMINIO — lo que testeamos
# ============================================================
# En un proyecto real estas funciones vivirían en módulos
# propios (p.ej. src/campaign_utils.py). Aquí las definimos
# inline para que el ejemplo sea autocontenido.

def classify_campaign_duration(duration_days: int) -> str:
    """
    Clasifica una campaña según su duración.
    Misma lógica que la view v_campaign_types del notebook SQL.
    """
    if duration_days <= 7:
        return "Semanal"
    elif duration_days <= 14:
        return "Quincenal"
    elif duration_days <= 31:
        return "Mensual"
    else:
        return "Otro"


def calculate_redemption_rate(rewards_issued: int, rewards_redeemed: int) -> float:
    """
    Calcula el % de recompensas canjeadas sobre las emitidas.
    Devuelve 0.0 si no se emitió ninguna (evita división por cero).
    """
    if rewards_issued == 0:
        return 0.0
    return round(rewards_redeemed / rewards_issued * 100, 1)


def is_new_promo_user(user_id: int, promo_id: int, user_history: list[dict]) -> bool:
    """
    Devuelve True si esta es la PRIMERA promoción del usuario.
    Equivale a la lógica S2 del notebook.

    user_history: lista de dicts con {"user_id", "promo_id", "optin_date"}
    """
    # Filtramos el historial de este usuario, ordenado por fecha
    user_promos = sorted(
        [h for h in user_history if h["user_id"] == user_id],
        key=lambda x: x["optin_date"],
    )
    if not user_promos:
        return False
    return user_promos[0]["promo_id"] == promo_id


def calculate_arpu_uplift(ggr_before: float, ggr_after: float) -> float:
    """
    Uplift de ARPU = GGR después - GGR antes de la primera promo.
    Positivo = usuario generó más revenue después de participar.
    """
    return round(ggr_after - ggr_before, 2)


# ============================================================
# TESTS — classify_campaign_duration
# ============================================================

class TestClassifyCampaignDuration:
    """
    Agrupamos los tests de una misma función en una clase.
    Esto es opcional pero ayuda a organizar tests relacionados.
    """

    def test_7_dias_es_semanal(self):
        assert classify_campaign_duration(7) == "Semanal"

    def test_1_dia_es_semanal(self):
        assert classify_campaign_duration(1) == "Semanal"

    def test_8_dias_es_quincenal(self):
        assert classify_campaign_duration(8) == "Quincenal"

    def test_14_dias_es_quincenal(self):
        assert classify_campaign_duration(14) == "Quincenal"

    def test_15_dias_es_mensual(self):
        assert classify_campaign_duration(15) == "Mensual"

    def test_31_dias_es_mensual(self):
        assert classify_campaign_duration(31) == "Mensual"

    def test_32_dias_es_otro(self):
        assert classify_campaign_duration(32) == "Otro"

    def test_90_dias_es_otro(self):
        assert classify_campaign_duration(90) == "Otro"


# ============================================================
# TESTS — calculate_redemption_rate
# ============================================================

class TestRedemptionRate:

    def test_tasa_canje_basica(self):
        # 8 de 10 recompensas canjeadas = 80%
        assert calculate_redemption_rate(10, 8) == 80.0

    def test_tasa_canje_completa(self):
        # Todas canjeadas = 100%
        assert calculate_redemption_rate(5, 5) == 100.0

    def test_tasa_canje_cero(self):
        # Ninguna canjeada = 0%
        assert calculate_redemption_rate(100, 0) == 0.0

    def test_sin_recompensas_emitidas_devuelve_cero(self):
        # Evitar división por cero — caso edge importante
        assert calculate_redemption_rate(0, 0) == 0.0

    def test_resultado_redondeado_a_1_decimal(self):
        # 1 de 3 = 33.333... → debe redondear a 33.3
        assert calculate_redemption_rate(3, 1) == 33.3


# ============================================================
# TESTS — is_new_promo_user
# ============================================================

class TestIsNewPromoUser:

    def test_primera_promo_del_usuario_es_nuevo(self):
        """Si esta es su primera promo, el usuario es 'nuevo'."""
        historial = [
            {"user_id": 1, "promo_id": 101, "optin_date": date(2025, 9, 1)},
        ]
        assert is_new_promo_user(user_id=1, promo_id=101, user_history=historial) is True

    def test_segunda_promo_no_es_nuevo(self):
        """Si ya participó antes, no es 'nuevo' en la segunda."""
        historial = [
            {"user_id": 1, "promo_id": 100, "optin_date": date(2025, 8, 1)},
            {"user_id": 1, "promo_id": 101, "optin_date": date(2025, 9, 1)},
        ]
        # La primera fue la 100, así que en la 101 ya no es nuevo
        assert is_new_promo_user(user_id=1, promo_id=101, user_history=historial) is False

    def test_usuario_sin_historial_devuelve_false(self):
        """Usuario que no existe en el historial."""
        assert is_new_promo_user(user_id=999, promo_id=101, user_history=[]) is False

    def test_orden_cronologico_correcto(self):
        """El historial desordenado por fecha debe ordenarse bien."""
        historial = [
            {"user_id": 2, "promo_id": 200, "optin_date": date(2025, 10, 1)},  # más reciente
            {"user_id": 2, "promo_id": 199, "optin_date": date(2025, 8, 1)},  # primera real
        ]
        # La primera cronológicamente es la 199
        assert is_new_promo_user(user_id=2, promo_id=199, user_history=historial) is True
        assert is_new_promo_user(user_id=2, promo_id=200, user_history=historial) is False


# ============================================================
# TESTS — calculate_arpu_uplift
# ============================================================

class TestArpuUplift:

    def test_uplift_positivo(self):
        """El usuario generó más revenue después de la promo."""
        assert calculate_arpu_uplift(ggr_before=100.0, ggr_after=150.0) == 50.0

    def test_uplift_negativo(self):
        """El usuario generó menos revenue después de la promo."""
        assert calculate_arpu_uplift(ggr_before=100.0, ggr_after=80.0) == -20.0

    def test_uplift_cero(self):
        """Sin cambio en revenue."""
        assert calculate_arpu_uplift(ggr_before=100.0, ggr_after=100.0) == 0.0

    def test_uplift_redondeado(self):
        """El resultado se redondea a 2 decimales."""
        assert calculate_arpu_uplift(ggr_before=10.0, ggr_after=10.333) == 0.33

    def test_usuario_inactivo_antes(self):
        """Usuario que no apostó antes de la promo (GGR=0 antes)."""
        assert calculate_arpu_uplift(ggr_before=0.0, ggr_after=45.50) == 45.5


# ============================================================
# USO DE FIXTURES — compartir datos entre tests
# ============================================================
# Un fixture es un dato o estado que varios tests comparten.
# pytest los inyecta automáticamente como parámetros.

@pytest.fixture
def historial_multiusuario():
    """Fixture: historial compartido para varios tests."""
    return [
        {"user_id": 1, "promo_id": 101, "optin_date": date(2025, 9, 1)},
        {"user_id": 1, "promo_id": 102, "optin_date": date(2025, 10, 1)},
        {"user_id": 2, "promo_id": 101, "optin_date": date(2025, 9, 15)},
    ]


def test_usuario_1_nuevo_en_101(historial_multiusuario):
    assert is_new_promo_user(1, 101, historial_multiusuario) is True


def test_usuario_1_no_nuevo_en_102(historial_multiusuario):
    assert is_new_promo_user(1, 102, historial_multiusuario) is False  # noqa: E501


def test_usuario_2_nuevo_en_101(historial_multiusuario):
    assert is_new_promo_user(2, 101, historial_multiusuario) is True


# ============================================================
# USO DE PARAMETRIZE — el mismo test con múltiples inputs
# ============================================================
# En vez de escribir 5 funciones iguales cambiando solo los datos,
# usamos @pytest.mark.parametrize para probar varios casos a la vez.

@pytest.mark.parametrize("duration_days, expected_type", [
    (1,   "Semanal"),
    (7,   "Semanal"),
    (8,   "Quincenal"),
    (14,  "Quincenal"),
    (15,  "Mensual"),
    (31,  "Mensual"),
    (32,  "Otro"),
    (365, "Otro"),
])
def test_clasificacion_campaña_parametrizado(duration_days, expected_type):
    """
    Un solo test que se ejecuta 8 veces con distintos inputs.
    Si algún caso falla, pytest dice exactamente cuál.
    """
    assert classify_campaign_duration(duration_days) == expected_type
