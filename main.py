import os
from threading import Thread
from flask import Flask
import discord
import google.generativeai as genai

# Renderスリープ防止用Webサーバー
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# Discord Bot設定
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# Gemini API設定
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        clean_text = message.content.replace(f"<@{bot.user.id}>", "").strip()
        
        async with message.channel.typing():
            try:
                response = model.generate_content(clean_text)
                await message.channel.send(response.text)
            except Exception as e:
                await message.channel.send(f"エラーが発生しました: {e}")
                print(e)

if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
