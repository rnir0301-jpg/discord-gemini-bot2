import os
from threading import Thread
from flask import Flask
import discord
from google import genai

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

# Gemini APIクライアントの初期化
ai_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # BotへのメンションまたはDMに反応
    if bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        clean_text = message.content.replace(f"<@{bot.user.id}>", "").strip()
        
        async with message.channel.typing():
            try:
                # モデル名を gemini-2.5-flash に指定
                res = ai_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=clean_text
                )
                await message.channel.send(res.text)
            except Exception as e:
                await message.channel.send(f"エラーが発生しました: {e}")
                print(e)

if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.run(os.environ.get("DISCORD_TOKEN"))
