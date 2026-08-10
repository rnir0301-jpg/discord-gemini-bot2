import os
from threading import Thread
from flask import Flask
import discord
from google import genai

# Render休眠防止用のWebサーバー
app = Flask('')
@app.route('/')
def home():
    return "Bot is active!"

def run_web():
    # Renderが割り当てるPORT番号を使用（デフォルトは10000）
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# Discord Bot設定
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

ai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

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
                res = ai_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=clean_text
                )
                await message.channel.send(res.text)
            except Exception as e:
                await message.channel.send("エラーが発生しました。")
                print(e)

if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
