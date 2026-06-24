# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased] — форк mpanius/Server-billing

Фиксы развёртывания в LXC на Proxmox VE (Proxmox 9 / Ubuntu 24.04 / privileged CT).

### Fixed

- **`install.sh`:** добавлен `python3-cryptography` в `install_packages` — без него wrap master-ключа (`app/key_wrap.py` → `cryptography.fernet`) падал с `ModuleNotFoundError` на шаге записи секретов.
- **`scripts/proxmox-lxc-deploy.sh`:** Docker-in-LXC apparmor — на хосте в конфиг CT добавляется `lxc.apparmor.profile: unconfined`, внутри CT удаляется пакет `apparmor` (тянется `docker-ce` в Recommends). Иначе `docker build`/`run` падают с `apparmor failed to apply profile … attr/apparmor/exec`.
- **`scripts/proxmox-lxc-deploy.sh`:** `resolve_template` больше не дублирует префикс хранилища (`pveam list` уже отдаёт полный volid `local:vztmpl/…`) — `pct create` падал с `unable to parse directory volume name`.
- **`Caddyfile` + `install.sh`:** доступ в LAN по голому IP. Новый `CADDY_TLS` (default `internal`) выбирает издателя (`internal` self-signed для LAN / email для Let's Encrypt), глобальный `default_sni` позволяет Caddy отдавать сертификат клиентам без TLS SNI (браузеры не шлют SNI для IP-литералов).

### Changed

- `REPO_URL` по умолчанию указывает на форк `mpanius/Server-billing`.

## [1.0.0] - 2026-06-13

First stable release for public self-hosted use.

### Added

- Dashboard for VPS/hosting renewals, payment links, and provider accounts.
- Provider catalog (~36 hosts, ~57 country flags, filters, remote JSON bundle updates).
- BILLmanager-compatible and Web API provider sync (read-only).
- Telegram reminders, encrypted SQLite backups to Telegram, SSL certificate monitoring.
- iCal export for payment calendar, multi-currency support (RUB, USD, EUR, USDT).
- One-command install (`scripts/install.sh`), Docker Compose + Caddy or nginx.
- Security hardening: CSRF, login rate limit, IP allowlist, SSRF protection, Fernet encryption.
- Passphrase-wrapped encryption master key (`encryption.key.wrap`, `SECURITY.md`).
- In-panel updates via updater service, web SSH terminal (disabled by default).

### Security

- Master keys in `secrets/`, not in `.env`.
- Fail-closed auth without session key and admin password hash.
- Column-level Fernet encryption for SSH passwords, API keys, and bot tokens.

[1.0.0]: https://github.com/AlekseyRusaleev/Server-billing/releases/tag/v1.0.0
