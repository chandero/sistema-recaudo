#!/usr/bin/env python3
"""Create default workflow transitions on production without touching states."""
import json, requests, urllib3, sys
urllib3.disable_warnings()

BASE = "https://giron.cyberrit.tiksgroup.co/api/v1"

# Login
login_r = requests.post(f"{BASE}/auth/login", json={"email": "admin@sistema-cobro.com", "password": "admin123"}, verify=False)
if login_r.status_code != 200:
    print(f"Login failed: {login_r.text}")
    sys.exit(1)
token = login_r.json()["access_token"]
H = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# Get active states
states = requests.get(f"{BASE}/workflows/states/", headers=H, verify=False).json()
code_to_id = {s["code"]: s["id"] for s in states if s["is_active"]}
print(f"Active states: {len(code_to_id)}")

# Get existing transitions
existing = requests.get(f"{BASE}/workflows/transitions/", headers=H, verify=False).json()
existing_pairs = {(t["source_state_id"], t["target_state_id"]) for t in existing}
print(f"Existing transitions: {len(existing)}")

# Default transitions (source_code, target_code, name)
TRANSITIONS = [
    ("CARTERA_CARGADA", "OBLIGACION_VALIDADA", "Validar obligación"),
    ("OBLIGACION_VALIDADA", "PENDIENTE_ASIGNACION_RESOLUCION", "Asignar resolución"),
    ("PENDIENTE_ASIGNACION_RESOLUCION", "RESOLUCION_RADICADOS_ASIGNADOS", "Radicar resolución"),
    ("RESOLUCION_RADICADOS_ASIGNADOS", "DOCUMENTO_NOTIFICACION_GENERADO", "Generar documento"),
    ("DOCUMENTO_NOTIFICACION_GENERADO", "NOTIFICACION_ENVIADA", "Enviar notificación"),
    ("NOTIFICACION_ENVIADA", "ESPERANDO_RESULTADO_NOTIFICACION", "Esperar resultado"),
    ("ESPERANDO_RESULTADO_NOTIFICACION", "NOTIFICACION_ENTREGADA", "Entregada"),
    ("ESPERANDO_RESULTADO_NOTIFICACION", "NOTIFICACION_DEVUELTA", "Devuelta"),
    ("NOTIFICACION_DEVUELTA", "REINTENTO_NOTIFICACION", "Reintentar"),
    ("REINTENTO_NOTIFICACION", "NOTIFICACION_ENVIADA", "Reenviar notificación"),
    ("NOTIFICACION_ENTREGADA", "ESPERANDO_PAGO_VOLUNTARIO", "Esperar pago"),
    ("ESPERANDO_PAGO_VOLUNTARIO", "COBRO_PERSUASIVO", "Iniciar cobro persuasivo"),
    ("ESPERANDO_PAGO_VOLUNTARIO", "PAGADO", "Pago voluntario"),
    ("COBRO_PERSUASIVO", "ACUERDO_DE_PAGO", "Proponer acuerdo"),
    ("COBRO_PERSUASIVO", "PAGADO", "Pago en cobro persuasivo"),
    ("ACUERDO_DE_PAGO", "SEGUIMIENTO_ACUERDO", "Iniciar seguimiento"),
    ("SEGUIMIENTO_ACUERDO", "PAGADO", "Cumplió acuerdo"),
    ("SEGUIMIENTO_ACUERDO", "ACUERDO_INCUMPLIDO", "Incumplimiento"),
    ("ACUERDO_INCUMPLIDO", "COBRO_PREJURIDICO", "Escalar a prejurídico"),
    ("COBRO_PERSUASIVO", "COBRO_PREJURIDICO", "Escalar a prejurídico"),
    ("COBRO_PREJURIDICO", "COBRO_COACTIVO", "Escalar a coactivo"),
    ("COBRO_PREJURIDICO", "PAGADO", "Pago en prejurídico"),
    ("COBRO_COACTIVO", "PAGADO", "Pago en coactivo"),
    ("COBRO_COACTIVO", "INCOBRABLE", "Declarar incobrable"),
    ("COBRO_PREJURIDICO", "ARCHIVADO", "Archivar proceso"),
]

created = 0
skipped = 0
errors = 0

for src_code, tgt_code, name in TRANSITIONS:
    src_id = code_to_id.get(src_code)
    tgt_id = code_to_id.get(tgt_code)
    if not src_id or not tgt_id:
        print(f"  SKIP (missing state): {src_code} -> {tgt_code}")
        skipped += 1
        continue
    if (src_id, tgt_id) in existing_pairs:
        print(f"  EXISTS: {src_code} -> {tgt_code}")
        skipped += 1
        continue
    data = {
        "source_state_id": src_id,
        "target_state_id": tgt_id,
        "name": name,
        "is_automatic": False,
        "is_active": True,
    }
    r = requests.post(f"{BASE}/workflows/transitions/", headers=H, json=data, verify=False)
    if r.status_code in (200, 201):
        print(f"  OK: {src_code} -> {tgt_code} ({name})")
        created += 1
    else:
        print(f"  ERROR: {src_code} -> {tgt_code}: {r.status_code} {r.text}")
        errors += 1

print(f"\nDone: {created} created, {skipped} skipped, {errors} errors")
