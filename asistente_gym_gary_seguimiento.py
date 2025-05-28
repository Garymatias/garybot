
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from openai import OpenAI
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio
import pytz
import json
import os
from datetime import datetime

# === CLAVES DE ACCESO ===
TELEGRAM_TOKEN = "7919047017:AAHHPTuzC6gHBD8gY4BldjUpTvauoQ4qTf8"
OPENAI_KEY = "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"

client = OpenAI(api_key=OPENAI_KEY)
CHAT_ID_FILE = "chat_id_gary.json"
LOG_FILE = "registro_gym_gary.json"

def guardar_chat_id(chat_id):
    with open(CHAT_ID_FILE, "w") as f:
        json.dump({"chat_id": chat_id}, f)

def cargar_chat_id():
    if os.path.exists(CHAT_ID_FILE):
        with open(CHAT_ID_FILE, "r") as f:
            return json.load(f).get("chat_id")
    return None

def registrar_asistencia(fui):
    hoy = datetime.now(pytz.timezone("America/Santiago")).strftime("%Y-%m-%d")
    registro = {}
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            registro = json.load(f)
    registro[hoy] = "fui" if fui else "nofui"
    with open(LOG_FILE, "w") as f:
        json.dump(registro, f)

def leer_asistencia_ayer():
    ayer = datetime.now(pytz.timezone("America/Santiago")).date().fromordinal(datetime.now(pytz.timezone("America/Santiago")).date().toordinal() - 1)
    fecha = ayer.strftime("%Y-%m-%d")
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            registro = json.load(f)
            return registro.get(fecha)
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    guardar_chat_id(update.effective_chat.id)
    await update.message.reply_text("✅ Gary, ya estás registrado. Recibirás tu motivación a las 6:30 AM. Usa /fui o /nofui para registrar tu progreso.")

async def fui(update: Update, context: ContextTypes.DEFAULT_TYPE):
    registrar_asistencia(True)
    await update.message.reply_text("💪 ¡Bien, Gary! Registro guardado. Hoy cumpliste.")

async def nofui(update: Update, context: ContextTypes.DEFAULT_TYPE):
    registrar_asistencia(False)
    await update.message.reply_text("😞 Registro guardado, Gary. Mañana vamos con todo.")

def mensaje_motivacional(app):
    chat_id = cargar_chat_id()
    if not chat_id:
        return

    resultado = leer_asistencia_ayer()
    estilo = "duro" if resultado == "nofui" else "orgullo" if resultado == "fui" else "normal"

    prompt = {
        "duro": "Gary no fue ayer al gimnasio. Hoy necesitas levantarlo con toda tu energía. Sé directo, militar, y muéstrale las consecuencias de fallar. Sin groserías explícitas.",
        "orgullo": "Gary sí fue ayer al gimnasio. Felicítalo con intensidad, hazle sentir que está en el camino correcto. Dale fuerza para seguir.",
        "normal": "Hoy es un nuevo día. No sabemos si Gary fue ayer. Motívalo como si hoy fuera el primer día del resto de su vida."
    }

    respuesta = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Eres un coach militar que motiva con intensidad, sin groserías pero con fuerza."},
            {"role": "user", "content": prompt[estilo]}
        ]
    )

    texto = respuesta.choices[0].message.content
    asyncio.run(app.bot.send_message(chat_id=chat_id, text=texto))

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("fui", fui))
    app.add_handler(CommandHandler("nofui", nofui))

    santiago = pytz.timezone("America/Santiago")
    scheduler = BackgroundScheduler(timezone=santiago)
    scheduler.add_job(lambda: mensaje_motivacional(app), CronTrigger(hour=6, minute=30))
    scheduler.start()

    print("✅ Bot con seguimiento diario activo.")
    app.run_polling()
