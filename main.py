import os
from threading import Thread
from flask import Flask
import discord
from google import genai

app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

ai_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        async with message.channel.typing():
            # 1. チャンネルの直近10件のメッセージを取得
            messages = []
            async for msg in message.channel.history(limit=10, oldest_first=True):
                # 空のメッセージやシステムメッセージは除外
                if not msg.content:
                    continue
                
                # 送信者（Botかユーザーか）に応じてロールを振り分け
                role = "model" if msg.author == bot.user else "user"
                clean_content = msg.content.replace(f"<@{bot.user.id}>", "").strip()
                
                messages.append({
                    "role": role,
                    "parts": [{"text": f"{msg.author.display_name}: {clean_content}"}]
                })

            try:
                # 2. 履歴を含めた contents をGeminiに送信
                res = ai_client.models.generate_content(
                    model="gemini-3.5-flash-lite",
                    contents=messages
                )
                if res.text:
                    await message.channel.send(res.text)
            except Exception as e:
                print(f"API Error: {e}")
                await message.channel.send("エラーが発生しました。")

if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.run(os.environ.get("DISCORD_TOKEN"))
