"""Pruebas de resolución de la base a migrar en producción.

Regresión específica: dentro del contenedor el código se monta en /app y no se
exporta DATABASE_URL, así que la ruta por defecto del servidor no existe. El script
acababa aplicando los ALTER TABLE sobre /opt/riap/db/cartera.db, una base inactiva,
mientras la base real seguía sin las columnas del Auto de Archivo y la Constancia.
"""

import os
import sqlite3
import sys
import types

import run_migrations


def _crear_base(base: str, tablas: dict) -> None:
    """Crea un archivo SQLite con el esquema indicado (nombre -> columnas)."""
    with sqlite3.connect(base) as conexion:
        for tabla, columnas in tablas.items():
            definiciones = ", ".join(f"{columna} TEXT" for columna in columnas)
            conexion.execute(f"CREATE TABLE {tabla} (id INTEGER PRIMARY KEY, {definiciones})")


def _columnas(base: str, tabla: str) -> set:
    with sqlite3.connect(base) as conexion:
        return {fila[1] for fila in conexion.execute(f"PRAGMA table_info({tabla})")}


def _sin_variables_de_entorno(monkeypatch):
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)


def _fijar_configuracion_de_la_aplicacion(monkeypatch, url: str):
    """Sustituye app.core.config por una configuración falsa con la URL dada."""
    modulo = types.ModuleType("app.core.config")
    modulo.settings = types.SimpleNamespace(DATABASE_URL=url)
    monkeypatch.setitem(sys.modules, "app.core.config", modulo)


def test_la_configuracion_de_la_aplicacion_define_la_base_migrable(monkeypatch, tmp_path):
    _sin_variables_de_entorno(monkeypatch)
    _fijar_configuracion_de_la_aplicacion(monkeypatch, "sqlite:///./test.db")
    (tmp_path / "test.db").touch()
    monkeypatch.chdir(tmp_path)

    ruta, origen, estricta = run_migrations.resolver_ruta_bd()

    assert origen == "configuración de la aplicación"
    assert estricta is True
    assert os.path.abspath(ruta) == str(tmp_path / "test.db")


def test_database_url_de_entorno_manda_sobre_la_aplicacion(monkeypatch, tmp_path):
    _sin_variables_de_entorno(monkeypatch)
    _fijar_configuracion_de_la_aplicacion(monkeypatch, "sqlite:///./test.db")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'cartera.db'}")

    ruta, origen, estricta = run_migrations.resolver_ruta_bd()

    assert origen == "DATABASE_URL"
    assert estricta is False
    assert ruta.endswith("cartera.db")


def test_no_migra_la_base_vieja_cuando_falta_la_base_activa(monkeypatch, tmp_path):
    _sin_variables_de_entorno(monkeypatch)
    _fijar_configuracion_de_la_aplicacion(monkeypatch, "sqlite:///./no_existe.db")
    monkeypatch.chdir(tmp_path)

    reliquia = tmp_path / "cartera.db"
    _crear_base(str(reliquia), {"obligations": ["titulo"], "tenants": ["nombre"]})
    monkeypatch.setattr(run_migrations, "RUTAS_ALTERNATIVAS", [str(reliquia)])

    assert run_migrations.main() is False
    assert "paid_date" not in _columnas(str(reliquia), "obligations"), (
        "se alteró la base alternativa cuando la base activa no estaba localizada"
    )


def test_migra_la_base_de_la_aplicacion_y_agrega_las_fechas(monkeypatch, tmp_path):
    _sin_variables_de_entorno(monkeypatch)
    _fijar_configuracion_de_la_aplicacion(monkeypatch, "sqlite:///./test.db")
    base = tmp_path / "test.db"
    _crear_base(
        str(base),
        {"obligations": ["titulo"], "tenants": ["nombre"], "document_templates": ["codigo"]},
    )
    monkeypatch.chdir(tmp_path)

    assert run_migrations.main() is True

    nuevas = _columnas(str(base), "obligations")
    assert {"paid_date", "notification_date", "executory_date"} <= nuevas
