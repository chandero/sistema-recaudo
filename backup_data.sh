#!/bin/bash
#
# Respaldo automático del sistema de recaudo (cyberrit).
#
# QUÉ GUARDA
#   La base SQLite en servicio, las plantillas DOCX, el .env, docker-compose.yml,
#   las migraciones y los scripts del servidor. NO guarda
#   backend/app/uploads/generated: son entregables que vuelven a salir de la base
#   de datos y ya pesan gigabytes.
#
# DÓNDE
#   Local:  /opt/siap/backups_cyberrit
#   Remoto: 84.247.164.191:/opt/giron/siap/backups_cyberrit. El viaje lo hace el
#           rsync que /usr/bin/siap_backup.bash dispara a través de
#           /opt/script_sender.bash sobre /opt/siap. La fuente va sin barra final
#           (rsync -avP /opt/siap destino:/opt/giron), así que el directorio se
#           anida: llega a /opt/giron/siap/... y no a /opt/giron/... Este respaldo
#           vive DENTRO de /opt/siap precisamente para subirse a ese viaje sin
#           tener que inventar otro canal de sincronización.
#   En un directorio propio y no en /opt/siap/backups: la rotación de SIAP elige
#   «la más antigua» con ls | sort -n sobre nombres que empiezan por letra, y un
#   archivo cyberrit_* aparecería primero en ese orden falso. Compartir carpeta
#   era exponer este respaldo al borrado ajeno.
#
# CUÁNDO
#   Cron de root: 03:00 y 15:00. Como máximo se pierde medio día de datos.
#   Conserva las 60 copias recientes, unos 300 MB.
#
# RESTAURACIÓN
#   mkdir -p /restore
#   tar -xzf /opt/siap/backups_cyberrit/cyberrit_<sello>.tar.gz -C /restore
#   sqlite3 /restore/opt/cyberrit/backend/test.db 'PRAGMA integrity_check;'
#   cd /opt/cyberrit && docker compose stop backend
#   cp /restore/opt/cyberrit/backend/test.db /opt/cyberrit/backend/test.db
#   docker compose up -d backend && curl -s localhost:8055/health
#   Las plantillas vuelven a su sitio con:
#   cp -a /restore/opt/cyberrit/backend/app/uploads/templates \
#         /opt/cyberrit/backend/app/uploads/
#
# PRUEBAS
#   DRY_RUN=1         no escribe ni borra nada en el destino; dice qué habría hecho
#   KEEP=2            fuerza la rotación sobre pocas copias
#   SEND_OFFSITE=0    evita el viaje al servidor remoto
#
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/cyberrit}"
BACKUP_DIR="${BACKUP_DIR:-/opt/siap/backups_cyberrit}"
DB="${DB:-$APP_DIR/backend/test.db}"
KEEP="${KEEP:-60}"
SEND_OFFSITE="${SEND_OFFSITE:-1}"
DRY_RUN="${DRY_RUN:-0}"
SENDER="${SENDER:-/opt/script_sender.bash}"
SENDER_ARG="${SENDER_ARG:-giron}"
LOCK="${LOCK:-/run/lock/cyberrit_backup.lock}"

MARCA="$(date +%Y%m%d-%H%M%S)"
NOMBRE="cyberrit_${MARCA}"
PARCIAL=""
SALIDA="$BACKUP_DIR/${NOMBRE}.tar.gz"
REGISTRO="$BACKUP_DIR/${NOMBRE}.txt"
ESTADO="$APP_DIR/backups/.ultimo_respaldo"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/${NOMBRE}.XXXXXX")"
RAIZ="$TMP/raiz/opt/cyberrit"

# Rutas que componen el respaldo. Si alguna falta se registra la omisión en el
# .txt hermano en lugar de interrumpir: un archivo renombrado no debe dejar al
# sistema sin respaldo de la base de datos.
RUTAS=(
    ".env"
    "docker-compose.yml"
    "backend/run_migrations.py"
    "backend/app/uploads/templates"
    "plantillas_nuevas"
    "auditoria"
    "scripts"
    ".last_deployment"
)

log() { printf '[%s] %s\n' "$(date '+%F %T')" "$*"; }
abortar() { log "FALLO: $*"; exit 1; }

limpiar() { rm -rf "$TMP"; }
trap limpiar EXIT

# El .part vive en el directorio final para que el paso a nombre definitivo sea
# un rename dentro del mismo sistema de archivos: así nunca aparece en el
# directorio un tar.gz a medio escribir.
preparar_destino() {
    if [ "$DRY_RUN" = "1" ]; then
        log "SIMULACIÓN: no toca $BACKUP_DIR"
        return 0
    fi
    mkdir -p "$BACKUP_DIR"
    chmod 700 "$BACKUP_DIR"
    PARCIAL="$BACKUP_DIR/.${NOMBRE}.tar.gz.part"
}

# Copia consistente sin detener la aplicación. cp sobre el archivo vivo puede
# capturar una escritura a medias; la API de backup de SQLite congela el estado
# de la transacción. Si la base está ocupada se reintenta tres veces.
hacer_snapshot() {
    local intento
    for intento in 1 2 3; do
        if sqlite3 "$DB" ".backup '$RAIZ/backend/test.db'" 2>"$TMP/error.txt"; then
            return 0
        fi
        log "intento $intento de snapshot falló: $(tr -d '\n' <"$TMP/error.txt")"
        [ "$intento" -lt 3 ] || return 1
        sleep 10
    done
}

# Un respaldo corrupto consume el cupo de la rotación y da falsa tranquilidad,
# así que la validación es previa a publicar cualquier archivo.
verificar_snapshot() {
    local resultado
    resultado="$(sqlite3 "$RAIZ/backend/test.db" 'PRAGMA integrity_check;')"
    [ "$resultado" = "ok" ] || abortar "integrity_check devolvió: $resultado"
    log "base verificada: integrity_check ok"
}

# Volteo del snapshot y de las rutas de configuración a un árbol que reproduce
# la ubicación real. Empaquetar desde ese árbol evita las exclusiones de tar, que
# son frágiles: lo que no se copia es lo que nunca se puso adentro.
armar_area() {
    mkdir -p "$RAIZ/backend/app/uploads"
    local ruta
    for ruta in "${RUTAS[@]}"; do
        if [ -e "$APP_DIR/$ruta" ]; then
            mkdir -p "$RAIZ/$(dirname "$ruta")"
            cp -a "$APP_DIR/$ruta" "$RAIZ/$ruta"
            OMITIDAS_INCLUIDAS+=" $ruta"
        else
            OMITIDAS+=" $ruta"
            log "AVISO: no existe $APP_DIR/$ruta, se omite del respaldo"
        fi
    done
    # Los nginx_*.conf del servidor cambian de nombre con cada ajuste; se toman todos.
    local conf
    for conf in "$APP_DIR"/nginx_*.conf; do
        [ -e "$conf" ] || continue
        cp -a "$conf" "$RAIZ/"
        OMITIDAS_INCLUIDAS+=" $(basename "$conf")"
    done
}

empaquetar() {
    tar -czf "$PARCIAL" -C "$TMP/raiz" opt/cyberrit
    chmod 600 "$PARCIAL"
    log "archivo armado: $(du -h "$PARCIAL" | cut -f1)"
}

recuento_filas() {
    local base="$1" tabla total=""
    for tabla in tenants users clients obligations cobro_processes generated_documents; do
        if [ "$(sqlite3 "$base" "select count(*) from sqlite_master where type='table' and name='$tabla';")" = "1" ]; then
            total+="$tabla=$(sqlite3 "$base" "select count(*) from $tabla;") "
        fi
    done
    printf '%s\n' "${total% }"
}

publicar() {
    mv "$PARCIAL" "$SALIDA"
    ln -sfn "$(basename "$SALIDA")" "$BACKUP_DIR/cyberrit_ultimo.tar.gz"
    local tamano filas
    tamano="$(du -h "$SALIDA" | cut -f1)"
    filas="$(recuento_filas "$RAIZ/backend/test.db")"
    {
        printf 'Archivo: %s\n' "$SALIDA"
        printf 'Peso: %s\n' "$tamano"
        printf 'Filas: %s\n' "$filas"
        printf 'Incluidas:%s\n' "$OMITIDAS_INCLUIDAS"
        printf 'Omitidas:%s\n' "${OMITIDAS:- ninguna}"
        printf 'Resultado: éxito\n'
    } >"$REGISTRO"
    chmod 600 "$REGISTRO"
    log "publicado $SALIDA ($tamano)"
}

# Rotación por nombre: el sello va al inicio y con ceros a la izquierda, así que
# el orden alfabético coincide con el cronológico. Solo mira cyberrit_*.tar.gz,
# nunca nada de SIAP, y se lleva el .txt y el .part huérfanos del mismo sello.
rotar() {
    local excedentes archivo base
    # Un .part abandonado es residuo de una ejecución interrumpida. Envejece un
    # día y se borra, porque si no el directorio se llena de archivos invisibles
    # que nadie cuenta como copia pero que ocupan espacio.
    if [ "$DRY_RUN" != "1" ]; then
        find "$BACKUP_DIR" -maxdepth 1 -name '.cyberrit_*.part' -mtime +1 -delete 2>/dev/null || true
    fi
    excedentes="$(find "$BACKUP_DIR" -maxdepth 1 -name 'cyberrit_*.tar.gz' \
        ! -name 'cyberrit_ultimo.tar.gz' -printf '%f\n' 2>/dev/null \
        | sort | head -n -"$KEEP" || true)"
    if [ -z "$excedentes" ]; then
        log "rotación: hay menos de $KEEP copias, no se borra nada"
        return 0
    fi
    while IFS= read -r archivo; do
        [ -n "$archivo" ] || continue
        base="${archivo%.tar.gz}"
        if [ "$DRY_RUN" = "1" ]; then
            log "SIMULACIÓN: borraría $base.tar.gz y su registro"
            continue
        fi
        rm -f "$BACKUP_DIR/$base.tar.gz" "$BACKUP_DIR/$base.txt" "$BACKUP_DIR/.$base.tar.gz.part"
        log "rotación: eliminado $base.tar.gz"
    done <<<"$excedentes"
}

avisar_remoto() {
    if [ "$SEND_OFFSITE" != "1" ]; then
        log "sync remota omitida (SEND_OFFSITE=$SEND_OFFSITE)"
        return 0
    fi
    if [ "$DRY_RUN" = "1" ]; then
        log "SIMULACIÓN: invocaría $SENDER $SENDER_ARG"
        return 0
    fi
    if [ ! -x "$SENDER" ]; then
        log "AVISO: no existe $SENDER; el respaldo queda solo en este servidor"
        return 0
    fi
    # || true deliberado: si el rsync al remoto falla, el respaldo local ya está
    # escrito y no debe registrarse la ejecución como rota.
    local inicio
    inicio="$(date +%s)"
    if timeout 3600 "$SENDER" "$SENDER_ARG" >/dev/null 2>&1; then
        log "sync remota lista en $(( $(date +%s) - inicio ))s"
    else
        log "AVISO: la sync remota falló o agotó el tiempo; el respaldo local sigue válido"
    fi
}

registrar_estado() {
    local tamano="n/d"
    [ -n "$SALIDA" ] && [ -f "$SALIDA" ] && tamano="$(du -h "$SALIDA" | cut -f1)"
    mkdir -p "$APP_DIR/backups"
    {
        printf 'fecha=%s\n' "$(date '+%F %T')"
        printf 'archivo=%s\n' "$SALIDA"
        printf 'tamano=%s\n' "$tamano"
        printf 'copias=%s\n' "$(find "$BACKUP_DIR" -maxdepth 1 -name 'cyberrit_*.tar.gz' ! -name 'cyberrit_ultimo.tar.gz' 2>/dev/null | wc -l)"
        printf 'limite=%s\n' "$KEEP"
        printf 'omitidas=%s\n' "${OMITIDAS:- ninguna}"
        printf 'simulacion=%s\n' "$DRY_RUN"
        printf 'resultado=éxito\n'
    } >"$ESTADO"
}

[ -f "$DB" ] || abortar "no encuentro la base de datos en $DB"
command -v sqlite3 >/dev/null || abortar "sqlite3 no está instalado en el host"

# El directorio del candado depende del sistema; si no está, el respaldo no puede
# negarse a correr, así que se refugia en /tmp.
[ -d "$(dirname "$LOCK")" ] || LOCK="${TMPDIR:-/tmp}/cyberrit_backup.lock"
exec 9>"$LOCK"
flock -n 9 || abortar "otra ejecución del respaldo está en curso"

log "inicio del respaldo de $APP_DIR (simulación=$DRY_RUN)"
OMITIDAS=""
OMITIDAS_INCLUIDAS=""

mkdir -p "$RAIZ/backend"
preparar_destino
if [ "$DRY_RUN" = "1" ]; then
    mkdir -p "$BACKUP_DIR"
fi
PARCIAL="${PARCIAL:-$TMP/$NOMBRE.tar.gz}"

hacer_snapshot || abortar "no se pudo obtener un snapshot consistente de $DB"
verificar_snapshot
armar_area
empaquetar
[ "$DRY_RUN" = "1" ] || publicar
rotar
avisar_remoto
[ "$DRY_RUN" = "1" ] || registrar_estado
log "fin del respaldo"
