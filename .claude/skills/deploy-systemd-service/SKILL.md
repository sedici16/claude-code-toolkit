---
name: deploy-systemd-service
description: Deploy or update a small Python web app (FastAPI/Flask) on a Linux server as a systemd user service behind a Cloudflare Tunnel. Use when the user asks to deploy, redeploy, restart or expose an app on their server.
---

# Deploy a Python app as a systemd user service

Follow these steps in order. Stop and report if any check fails; do not improvise
around a failed check.

## 1. Before touching the server
- Confirm the target: host, app directory, service name and port. Ask if any is unknown.
- Run the app's tests or at least `python -m py_compile` on changed files locally.
- Never copy `.env`, databases or `*.db` unless the user asked for that file explicitly.

## 2. Ship the code
- Copy only source files: `tar czf - <files> | ssh <host> "tar xzf - -C <app_dir>"`.
- Install new dependencies inside the app's venv: `<app_dir>/.venv/bin/pip install -r requirements.txt`.

## 3. Service
- Unit file lives in `~/.config/systemd/user/<name>.service`, bound to `127.0.0.1:<port>`
  (never `0.0.0.0`: public traffic goes through the tunnel only).
- `systemctl --user daemon-reload && systemctl --user restart <name>`.
- Verify: `systemctl --user is-active <name>` and `curl -fsS http://127.0.0.1:<port>/health`.

## 4. Public hostname (only for a new app)
- Back up the tunnel config before editing: `cp /etc/cloudflared/config.yml{,.bak-<name>}`.
- Add the ingress rule **above** the catch-all `http_status:404` rule.
- Validate with `cloudflared tunnel ingress validate`, then restart cloudflared.
- The DNS CNAME is created in the Cloudflare dashboard by the user.

## 5. Report
State what changed, the service status, the health-check result and the public URL.
If a step was skipped, say so.
