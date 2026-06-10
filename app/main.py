from __future__ import annotations

from datetime import date

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.db import init_db
from app.repository import (
    create_account,
    create_server,
    delete_account,
    delete_server,
    get_account,
    get_server,
    list_accounts,
    list_servers,
    mark_paid,
    seed_demo_data,
    update_account,
    update_server,
)
from app.telegram import build_telegram_share_url

app = FastAPI(title=settings.app_name)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.on_event("startup")
def startup() -> None:
    init_db()
    seed_demo_data()


def form_payload(
    hosting_account_id: int,
    name: str,
    provider: str,
    ip_address: str,
    service_id: str,
    amount: float,
    currency: str,
    billing_period_days: int,
    next_payment_date: str,
    payment_url: str,
    panel_url: str,
    notes: str,
) -> dict[str, object]:
    return {
        "hosting_account_id": hosting_account_id or None,
        "name": name.strip(),
        "provider": provider.strip(),
        "ip_address": ip_address.strip(),
        "service_id": service_id.strip(),
        "amount": amount,
        "currency": currency.strip().upper() or "RUB",
        "billing_period_days": billing_period_days,
        "next_payment_date": next_payment_date,
        "payment_url": payment_url.strip(),
        "panel_url": panel_url.strip(),
        "notes": notes.strip(),
    }


def account_payload(
    name: str,
    provider: str,
    login: str,
    auth_secret: str,
    panel_url: str,
    payment_url: str,
    notes: str,
) -> dict[str, object]:
    return {
        "name": name.strip(),
        "provider": provider.strip(),
        "login": login.strip(),
        "auth_secret": auth_secret.strip(),
        "panel_url": panel_url.strip(),
        "payment_url": payment_url.strip(),
        "notes": notes.strip(),
    }


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    servers = list_servers()
    accounts = list_accounts()
    total_monthly = sum(server.amount for server in servers if server.currency == "RUB")
    due_7 = [server for server in servers if server.days_left <= 7]
    overdue = [server for server in servers if server.days_left < 0]
    providers = sorted({server.provider for server in servers})
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "servers": servers,
            "accounts": accounts,
            "providers": providers,
            "today": date.today(),
            "stats": {
                "total": len(servers),
                "due_7": len(due_7),
                "overdue": len(overdue),
                "monthly_rub": total_monthly,
            },
        },
    )


@app.post("/servers")
def add_server(
    hosting_account_id: int = Form(0),
    name: str = Form(...),
    provider: str = Form(...),
    ip_address: str = Form(""),
    service_id: str = Form(""),
    amount: float = Form(0),
    currency: str = Form("RUB"),
    billing_period_days: int = Form(30),
    next_payment_date: str = Form(...),
    payment_url: str = Form(""),
    panel_url: str = Form(""),
    notes: str = Form(""),
) -> RedirectResponse:
    create_server(
        form_payload(
            hosting_account_id,
            name,
            provider,
            ip_address,
            service_id,
            amount,
            currency,
            billing_period_days,
            next_payment_date,
            payment_url,
            panel_url,
            notes,
        )
    )
    return RedirectResponse("/", status_code=303)


@app.get("/servers/{server_id}/edit", response_class=HTMLResponse)
def edit_server(request: Request, server_id: int) -> HTMLResponse:
    server = get_server(server_id)
    if server is None:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        "edit.html",
        {"request": request, "server": server, "accounts": list_accounts()},
    )


@app.post("/servers/{server_id}/edit")
def save_server(
    server_id: int,
    hosting_account_id: int = Form(0),
    name: str = Form(...),
    provider: str = Form(...),
    ip_address: str = Form(""),
    service_id: str = Form(""),
    amount: float = Form(0),
    currency: str = Form("RUB"),
    billing_period_days: int = Form(30),
    next_payment_date: str = Form(...),
    payment_url: str = Form(""),
    panel_url: str = Form(""),
    notes: str = Form(""),
) -> RedirectResponse:
    update_server(
        server_id,
        form_payload(
            hosting_account_id,
            name,
            provider,
            ip_address,
            service_id,
            amount,
            currency,
            billing_period_days,
            next_payment_date,
            payment_url,
            panel_url,
            notes,
        ),
    )
    return RedirectResponse("/", status_code=303)


@app.post("/servers/{server_id}/paid")
def paid(server_id: int) -> RedirectResponse:
    mark_paid(server_id)
    return RedirectResponse("/", status_code=303)


@app.post("/servers/{server_id}/delete")
def remove_server(server_id: int) -> RedirectResponse:
    delete_server(server_id)
    return RedirectResponse("/", status_code=303)


@app.get("/accounts", response_class=HTMLResponse)
def accounts_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "accounts.html",
        {"request": request, "accounts": list_accounts()},
    )


@app.post("/accounts")
def add_account(
    name: str = Form(...),
    provider: str = Form(...),
    login: str = Form(""),
    auth_secret: str = Form(""),
    panel_url: str = Form(""),
    payment_url: str = Form(""),
    notes: str = Form(""),
) -> RedirectResponse:
    create_account(account_payload(name, provider, login, auth_secret, panel_url, payment_url, notes))
    return RedirectResponse("/accounts", status_code=303)


@app.get("/accounts/{account_id}/edit", response_class=HTMLResponse)
def edit_account(request: Request, account_id: int) -> HTMLResponse:
    account = get_account(account_id)
    if account is None:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        "account_edit.html",
        {"request": request, "account": account},
    )


@app.post("/accounts/{account_id}/edit")
def save_account(
    account_id: int,
    name: str = Form(...),
    provider: str = Form(...),
    login: str = Form(""),
    auth_secret: str = Form(""),
    panel_url: str = Form(""),
    payment_url: str = Form(""),
    notes: str = Form(""),
) -> RedirectResponse:
    update_account(
        account_id,
        account_payload(name, provider, login, auth_secret, panel_url, payment_url, notes),
    )
    return RedirectResponse("/accounts", status_code=303)


@app.post("/accounts/{account_id}/delete")
def remove_account(account_id: int) -> RedirectResponse:
    delete_account(account_id)
    return RedirectResponse("/accounts", status_code=303)


@app.get("/servers/{server_id}/pay", response_class=HTMLResponse)
def pay_page(request: Request, server_id: int) -> HTMLResponse:
    server = get_server(server_id)
    if server is None:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        "pay.html",
        {
            "request": request,
            "server": server,
            "telegram_share_url": build_telegram_share_url(server),
        },
    )
