"""
Pruebas del recorte del prefijo "Importación de cartera - " en el número de las
obligaciones. Se prueba la lógica pura del script: la parte que decide qué se
cambia es la que puede destruir datos si se equivoca.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

from limpia_prefijo_obligaciones import lleva_prefijo, planificar_cambios, recortar_prefijo


def test_recorta_el_prefijo_dejando_solo_el_numero():
    assert recortar_prefijo("Importación de cartera - 231786") == "231786"


def test_deja_intacta_la_descripcion_de_un_concepto_real():
    # El importador nuevo escribe "concepto - número" cuando el archivo trae
    # concepto: ese texto es legítimo y no debe desaparecer.
    assert recortar_prefijo("Alumbrado público - 4471") is None
    assert lleva_prefijo("Alumbrado público - 4471") is False


def test_acepta_las_variantes_de_tilde_espaciado_y_guion():
    for valor in (
        "Importacion de cartera - 4471",
        "IMPORTACIÓN DE CARTERA - 4471",
        "Importación de cartera-4471",
        "  Importación de cartera --  4471  ",
    ):
        assert recortar_prefijo(valor) == "4471", valor


def test_no_devuelve_nada_para_valores_vacios():
    assert recortar_prefijo(None) is None
    assert recortar_prefijo("") is None
    assert lleva_prefijo(None) is False


def test_planifica_los_cambios_y_aisla_las_anomalias():
    filas = [
        (1, "Importación de cartera - 231786"),
        (2, "233241"),
        (3, "Importación de cartera - "),
        (4, "Alumbrado público - 99"),
        (5, None),
    ]

    cambios, anomalias = planificar_cambios(filas)

    # Solo la 1 se reescribe; la 3 quedaría vacía y se reporta sin tocarla.
    assert cambios == [("231786", 1)]
    assert anomalias == [3]


def test_es_idempotente_sobre_las_filas_ya_corregidas():
    cambios, anomalias = planificar_cambios([(1, "231786"), (2, "1478134")])

    assert cambios == []
    assert anomalias == []
