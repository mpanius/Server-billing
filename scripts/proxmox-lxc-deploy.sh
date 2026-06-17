#!/usr/bin/env bash
# Server Billing Manager — развёртывание в LXC на Proxmox VE.
#
# Запуск на хосте Proxmox под root (не внутри контейнера):
#   curl -fsSL https://raw.githubusercontent.com/AlekseyRusaleev/Server-billing/main/scripts/proxmox-lxc-deploy.sh -o /tmp/proxmox-lxc-deploy.sh
#   bash /tmp/proxmox-lxc-deploy.sh
#
# Скрипт создаёт LXC с поддержкой Docker (nesting), ставит Docker и клонирует репозиторий.
# Финальная настройка (пароли, HTTPS, compose up) — интерактивно через scripts/install.sh
# внутри контейнера (нужна консоль с TTY).
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/AlekseyRusaleev/Server-billing.git}"
INSTALL_DIR="${INSTALL_DIR:-/opt/server-billing}"
SCRIPT_NAME="$(basename "$0")"

CTID="${CTID:-}"
HOSTNAME="${HOSTNAME:-server-billing}"
STORAGE="${STORAGE:-local-lvm}"
TEMPLATE_STORAGE="${TEMPLATE_STORAGE:-local}"
BRIDGE="${BRIDGE:-vmbr0}"
MEMORY="${MEMORY:-2048}"
SWAP="${SWAP:-512}"
CORES="${CORES:-2}"
DISK_GB="${DISK_GB:-16}"
UNPRIVILEGED="${UNPRIVILEGED:-0}"
IP_MODE="${IP_MODE:-dhcp}"
IP_CIDR="${IP_CIDR:-}"
GATEWAY="${GATEWAY:-}"
DNS="${DNS:-1.1.1.1}"
TEMPLATE="${TEMPLATE:-}"
START_CONTAINER="${START_CONTAINER:-1}"
SKIP_BOOTSTRAP="${SKIP_BOOTSTRAP:-0}"

usage() {
  cat <<EOF
Usage: $SCRIPT_NAME [options]

Создаёт LXC на Proxmox VE и подготавливает Server Billing Manager (Docker + git clone).
Запускайте на узле Proxmox под root.

Options:
  --ctid N              ID контейнера (по умолчанию: следующий свободный >= 100)
  --hostname NAME       Имя хоста внутри CT (default: $HOSTNAME)
  --storage ID          Хранилище rootfs (default: $STORAGE)
  --template-storage ID Хранилище шаблонов (default: $TEMPLATE_STORAGE)
  --template NAME       vztmpl, напр. debian-12-standard_12.7-1_amd64.tar.zst
  --bridge IFACE        Linux bridge (default: $BRIDGE)
  --memory MB           RAM (default: $MEMORY)
  --swap MB             Swap (default: $SWAP)
  --cores N             CPU (default: $CORES)
  --disk GB             Размер диска rootfs в GB (default: $DISK_GB)
  --unprivileged 0|1    0 = privileged (рекомендуется для Docker, default)
  --dhcp                DHCP на \$bridge (default)
  --static IP/CIDR      Статический IP, напр. 192.168.1.50/24
  --gateway IP          Шлюз для --static
  --dns IP              DNS (default: $DNS)
  --skip-bootstrap      Только создать CT, не ставить Docker/git
  --no-start            Не запускать CT после создания
  -h, --help            Эта справка

Переменные окружения: те же имена в UPPER_CASE (CTID, HOSTNAME, ...).

После скрипта войдите в контейнер и завершите установку:
  pct enter CTID
  cd $INSTALL_DIR && bash scripts/install.sh

EOF
}

log() {
  printf '==> %s\n' "$*"
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

require_root() {
  [ "$(id -u)" -eq 0 ] || die "Запустите на хосте Proxmox под root."
}

require_proxmox() {
  command -v pct >/dev/null 2>&1 || die "Команда pct не найдена. Это скрипт для Proxmox VE."
  [ -d /etc/pve ] || die "Каталог /etc/pve не найден. Запускайте на узле Proxmox."
}

next_ctid() {
  local id=100
  while pct status "$id" >/dev/null 2>&1; do
    id=$((id + 1))
  done
  echo "$id"
}

resolve_template() {
  if [ -n "$TEMPLATE" ]; then
    if [ -f "${TEMPLATE_STORAGE}/template/cache/${TEMPLATE}" ]; then
      echo "${TEMPLATE_STORAGE}:vztmpl/${TEMPLATE}"
      return
    fi
    if [ -f "/var/lib/vz/template/cache/${TEMPLATE}" ]; then
      echo "local:vztmpl/${TEMPLATE}"
      return
    fi
    die "Шаблон не найден: ${TEMPLATE}. Загрузите: pveam download ${TEMPLATE_STORAGE} ${TEMPLATE%.tar.zst}"
  fi

  local candidate
  candidate="$(pveam list "$TEMPLATE_STORAGE" 2>/dev/null | awk '/debian-12-standard/ {print $1; exit}')"
  if [ -n "$candidate" ]; then
    echo "${TEMPLATE_STORAGE}:vztmpl/${candidate}"
    return
  fi
  candidate="$(pveam list "$TEMPLATE_STORAGE" 2>/dev/null | awk '/ubuntu-24.04-standard/ {print $1; exit}')"
  if [ -n "$candidate" ]; then
    echo "${TEMPLATE_STORAGE}:vztmpl/${candidate}"
    return
  fi

  log "Шаблон Debian 12 не найден локально, загрузка pveam..."
  pveam update >/dev/null
  local remote version filename
  read -r _ remote version _ <<< "$(pveam available --section system 2>/dev/null | awk '/debian-12-standard/ {print; exit}')"
  [ -n "$remote" ] || die "Не удалось найти debian-12-standard в pveam available."
  filename="${remote}_${version}_amd64.tar.zst"
  pveam download "$TEMPLATE_STORAGE" "$filename"
  echo "${TEMPLATE_STORAGE}:vztmpl/${filename}"
}

build_net0() {
  if [ "$IP_MODE" = "dhcp" ]; then
    echo "name=eth0,bridge=${BRIDGE},ip=dhcp"
    return
  fi
  [ -n "$IP_CIDR" ] || die "Для статического IP укажите --static CIDR"
  [ -n "$GATEWAY" ] || die "Для статического IP укажите --gateway"
  echo "name=eth0,bridge=${BRIDGE},ip=${IP_CIDR},gw=${GATEWAY}"
}

pct_exec_retry() {
  local attempt=1
  local max=30
  while [ "$attempt" -le "$max" ]; do
    if pct exec "$CTID" -- "$@"; then
      return 0
    fi
    sleep 2
    attempt=$((attempt + 1))
  done
  die "pct exec не удался после ${max} попыток (CTID=${CTID})."
}

bootstrap_container() {
  log "Установка пакетов и Docker в CT ${CTID}..."
  pct_exec_retry bash -c '
    set -euo pipefail
    export DEBIAN_FRONTEND=noninteractive
    if command -v apt-get >/dev/null 2>&1; then
      apt-get update
      apt-get install -y ca-certificates curl git openssh-client python3
    elif command -v dnf >/dev/null 2>&1; then
      dnf install -y ca-certificates curl git openssh-clients python3
    else
      echo "Unsupported OS inside CT" >&2
      exit 1
    fi
    if ! command -v docker >/dev/null 2>&1; then
      curl -fsSL https://get.docker.com | sh
    fi
    systemctl enable --now docker 2>/dev/null || service docker start 2>/dev/null || true
  '

  log "Клонирование репозитория в ${INSTALL_DIR}..."
  pct_exec_retry bash -c "
    set -euo pipefail
    if [ -d '${INSTALL_DIR}/.git' ]; then
      git -C '${INSTALL_DIR}' pull --ff-only
    else
      mkdir -p '$(dirname "${INSTALL_DIR}")'
      git clone '${REPO_URL}' '${INSTALL_DIR}'
    fi
  "
}

print_finish() {
  local ip_hint=""
  if [ "$IP_MODE" = "dhcp" ]; then
    ip_hint="$(pct exec "$CTID" -- hostname -I 2>/dev/null | awk '{print $1}' || true)"
  else
    ip_hint="${IP_CIDR%%/*}"
  fi

  cat <<EOF

Готово: LXC CTID=${CTID} (${HOSTNAME})

Следующий шаг — интерактивная установка панели (пароли, HTTPS, docker compose):

  pct enter ${CTID}
  cd ${INSTALL_DIR} && bash scripts/install.sh

После install.sh панель будет доступна по BASE_URL из .env
(обычно https://PUBLIC_IP.sslip.io или ваш домен).

Проброс портов 80/443 с хоста Proxmox на CT не нужен, если панель открываете
по IP контейнера${ip_hint:+ ($ip_hint)}. Если CT в NAT — настройте DNAT 80/443
на Proxmox или выдайте CT публичный IP.

Обновление из веб-панели: после install.sh пересоберите updater один раз:
  docker compose -f docker-compose.prod.yml up -d --build updater

EOF
}

parse_args() {
  while [ $# -gt 0 ]; do
    case "$1" in
      --ctid) CTID="$2"; shift 2 ;;
      --hostname) HOSTNAME="$2"; shift 2 ;;
      --storage) STORAGE="$2"; shift 2 ;;
      --template-storage) TEMPLATE_STORAGE="$2"; shift 2 ;;
      --template) TEMPLATE="$2"; shift 2 ;;
      --bridge) BRIDGE="$2"; shift 2 ;;
      --memory) MEMORY="$2"; shift 2 ;;
      --swap) SWAP="$2"; shift 2 ;;
      --cores) CORES="$2"; shift 2 ;;
      --disk) DISK_GB="$2"; shift 2 ;;
      --unprivileged) UNPRIVILEGED="$2"; shift 2 ;;
      --dhcp) IP_MODE="dhcp"; shift ;;
      --static) IP_MODE="static"; IP_CIDR="$2"; shift 2 ;;
      --gateway) GATEWAY="$2"; shift 2 ;;
      --dns) DNS="$2"; shift 2 ;;
      --skip-bootstrap) SKIP_BOOTSTRAP=1; shift ;;
      --no-start) START_CONTAINER=0; shift ;;
      -h|--help) usage; exit 0 ;;
      *) die "Неизвестный аргумент: $1 (см. --help)" ;;
    esac
  done
}

main() {
  parse_args "$@"
  require_root
  require_proxmox

  [ -n "$CTID" ] || CTID="$(next_ctid)"
  if pct status "$CTID" >/dev/null 2>&1; then
    die "CTID ${CTID} уже существует. Укажите другой --ctid."
  fi

  local ostemplate net0 rootfs
  ostemplate="$(resolve_template)"
  net0="$(build_net0)"
  rootfs="${STORAGE}:${DISK_GB}"

  log "Создание LXC ${CTID} (${HOSTNAME})..."
  log "  template: ${ostemplate}"
  log "  rootfs:   ${rootfs}"
  log "  net0:     ${net0}"
  log "  unprivileged: ${UNPRIVILEGED}"

  pct create "$CTID" "$ostemplate" \
    --hostname "$HOSTNAME" \
    --memory "$MEMORY" \
    --swap "$SWAP" \
    --cores "$CORES" \
    --rootfs "$rootfs" \
    --net0 "$net0" \
    --nameserver "$DNS" \
    --unprivileged "$UNPRIVILEGED" \
    --features nesting=1,keyctl=1 \
    --onboot 1 \
    --start 0

  if [ "$UNPRIVILEGED" = "0" ]; then
    log "Privileged CT: Docker в LXC поддерживается через nesting=1."
  else
    log "Unprivileged CT: если Docker не стартует, пересоздайте CT с --unprivileged 0."
  fi

  if [ "$START_CONTAINER" = "1" ]; then
    log "Запуск CT ${CTID}..."
    pct start "$CTID"
    sleep 3
  fi

  if [ "$SKIP_BOOTSTRAP" = "0" ] && [ "$START_CONTAINER" = "1" ]; then
    bootstrap_container
  fi

  print_finish
}

main "$@"
