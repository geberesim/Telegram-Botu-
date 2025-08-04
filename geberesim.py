import random
import string
import requests
import re
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

BOT_TOKEN = "8481492288:AAG85uduQh-cH7Q-kbQ2n7vugmBiHpTOMM0"
WEATHER_API_KEY = "1d51fdab67c840faab9123016250408"

def normalize(word):
    return word.lower().translate(str.maketrans("çğıöşü", "cgiosu"))

with open("turkce_kelimeler.txt", "r", encoding="utf-8") as f:
    WORDS = [normalize(line.strip()) for line in f if len(line.strip()) >= 3]

active_letters = []
valid_words = []

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Merhaba! 👋\nYardım için /help yazabilirsin."
    )

# /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛠️ Kullanılabilir komutlar:\n"
        "/start - Botu başlat\n"
        "/help - Yardım komutları\n"
        "/kelimeoyunu - 5 rastgele harf verir ve kelime oyunu başlatır\n"
        "/tahmin <kelime> - Tahminde bulun\n"
        "/cevap - Geçerli kelimeleri listeler\n\n"
        "Hava durumu için şu şekilde yaz:\n"
        "- bugün hava nasıl ankara\n"
        "- bugün hava nasıl izmir 3 günlük"
    )

# /kelimeoyunu
async def kelime_oyunu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global active_letters, valid_words

    for _ in range(20):
        letters = random.sample(string.ascii_lowercase, 5)
        possible_words = [
            w for w in WORDS if set(w).issubset(set(letters)) and len(w) >= 3
        ]
        if possible_words:
            active_letters = letters
            valid_words = possible_words
            await update.message.reply_text(
                f"🧠 Harfler: {' '.join(letters)}\n"
                f"{len(valid_words)} geçerli kelime var. /tahmin <kelime>"
            )
            return
    await update.message.reply_text("⚠️ Uygun harf bulunamadı. Tekrar deneyin.")

# /tahmin
async def tahmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not active_letters:
        await update.message.reply_text("Önce /kelimeoyunu başlatmalısın.")
        return
    if not context.args:
        await update.message.reply_text("Örnek kullanım: /tahmin masa")
        return

    guess = normalize(context.args[0])
    if guess in valid_words:
        await update.message.reply_text(f"✅ Doğru: {guess}")
    else:
        await update.message.reply_text(f"❌ Yanlış: {guess}")

# /cevap
async def cevap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not valid_words:
        await update.message.reply_text("Kelime oyunu başlatılmadı.")
    else:
        await update.message.reply_text("📜 Geçerli kelimeler:\n" + ", ".join(valid_words))

# Hava durumu ve tahmin
async def handle_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    if "hava" in text:
        match = re.search(r"bugün hava nasıl\s*(.*?)\s*(\d+)?\s*günlük?", text)
        city = match.group(1).strip() if match else ""
        days = int(match.group(2)) if match and match.group(2) else 1

        if not city:
            await update.message.reply_text("Lütfen şehir adını da yaz: 'bugün hava nasıl İzmir'")
            return
        if days > 7:
            await update.message.reply_text("Maksimum 7 günlük tahmin alınabilir.")
            return

        base_url = "http://api.weatherapi.com/v1/"
        try:
            if days == 1:
                url = base_url + "current.json"
                params = {"key": WEATHER_API_KEY, "q": city, "lang": "tr"}
                r = requests.get(url, params=params)
                data = r.json()

                if "error" in data:
                    await update.message.reply_text(f"Şehir bulunamadı: {city}")
                    return

                loc = data["location"]
                current = data["current"]
                await update.message.reply_text(
                    f"📍 {loc['name']}, {loc['region']}, {loc['country']}\n"
                    f"🌡️ Sıcaklık: {current['temp_c']}°C\n"
                    f"🤒 Hissedilen: {current['feelslike_c']}°C\n"
                    f"🌤️ Hava: {current['condition']['text']}\n"
                    f"💧 Nem: %{current['humidity']}\n"
                    f"💨 Rüzgar: {current['wind_kph']} km/s\n"
                    f"☁️ Bulut: %{current['cloud']}\n"
                    f"🔭 Görüş: {current['vis_km']} km\n"
                    f"🌞 UV: {current['uv']}"
                )
            else:
                url = base_url + "forecast.json"
                params = {"key": WEATHER_API_KEY, "q": city, "days": days, "lang": "tr"}
                r = requests.get(url, params=params)
                data = r.json()

                if "error" in data:
                    await update.message.reply_text(f"Şehir bulunamadı: {city}")
                    return

                forecast_text = f"📍 {data['location']['name']}, {data['location']['region']}, {data['location']['country']}\n\n"
                for day in data['forecast']['forecastday']:
                    forecast_text += (
                        f"📅 {day['date']}\n"
                        f"🌡️ Max: {day['day']['maxtemp_c']}°C / Min: {day['day']['mintemp_c']}°C\n"
                        f"🌤️ {day['day']['condition']['text']}\n"
                        f"💧 Nem: %{day['day']['avghumidity']}\n"
                        f"☀️ UV: {day['day']['uv']}\n\n"
                    )
                await update.message.reply_text(forecast_text.strip())
        except Exception as e:
            print("Hata:", e)
            await update.message.reply_text("🌐 Hava durumu alınamadı.")
    else:
        await update.message.reply_text("Komutu anlayamadım. Yardım için /help yazabilirsin.")

# Geçersiz komutlar
async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Komutu anlayamadım. Yardım için /help yazabilirsin.")

# Botu çalıştır
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("kelimeoyunu", kelime_oyunu))
    app.add_handler(CommandHandler("tahmin", tahmin))
    app.add_handler(CommandHandler("cevap", cevap))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_weather))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    print("✅ Bot çalışıyor...")
    app.run_polling()
