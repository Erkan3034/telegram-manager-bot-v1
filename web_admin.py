
from __future__ import annotations

import os
from typing import Optional

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

from config import settings
from services.supabase_client import SupabaseClient
from services.group_service import GroupService


ADMIN_WEB_SECRET = os.getenv("ADMIN_WEB_SECRET", None)


app = FastAPI(title="Telegram Manager Bot - Admin Web")
templates = Jinja2Templates(directory="templates")

# Services
supa = SupabaseClient()
bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode="HTML"))
groups = GroupService(bot)


def require_secret(request: Request):
    if ADMIN_WEB_SECRET is None:
        # If not set, block web admin for safety
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="ADMIN_WEB_SECRET is not set")
    token = request.query_params.get("token")
    if token != ADMIN_WEB_SECRET:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return True


@app.get("/admin", response_class=HTMLResponse)
async def admin_home(request: Request, _=Depends(require_secret)):
    pending = await supa.list_pending_payments()
    # Enrich with usernames if available (not strictly necessary)
    return templates.TemplateResponse(
        "admin/index.html",
        {
            "request": request,
            "pending": pending,
            "token": request.query_params.get("token"),
        },
    )


@app.post("/admin/approve/{user_id}")
async def approve_user(user_id: int, request: Request, _=Depends(require_secret)):
    await supa.set_payment_status(user_id, "approved")
    await groups.add_user_to_group(user_id)
    await supa.add_member(user_id)
    return RedirectResponse(url=f"/admin?token={request.query_params.get('token')}", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/admin/reject/{user_id}")
async def reject_user(user_id: int, request: Request, _=Depends(require_secret)):
    await supa.set_payment_status(user_id, "rejected")
    try:
        await bot.send_message(chat_id=user_id, text="Ödemeniz maalesef reddedildi. Lütfen dekontu kontrol edip tekrar gönderin.")
    except Exception:
        pass
    return RedirectResponse(url=f"/admin?token={request.query_params.get('token')}", status_code=status.HTTP_303_SEE_OTHER)


