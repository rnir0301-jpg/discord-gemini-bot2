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

# Gemini API設定
ai_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    # Bot自身の発言には反応しない
    if message.author == bot.user:
        return

    # メンションまたはDMのときのみ処理
    if bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        clean_text = message.content.replace(f"<@{bot.user.id}>", "").strip()
        
        # 空メッセージの場合は処理しない
        if not clean_text:
            return

        try:
            # 成功が確認できたモデルのみを単一で呼び出す
            res = ai_client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=clean_text
            )
            if res.text:
                await message.channel.send(res.text)
        except Exception as e:
            print(f"API Error: {e}")
            # チャット欄を汚さないよう、エラー時はシンプルなメッセージのみ出力
            await message.channel.send("申し訳ありません。一時的なエラーが発生しました。時間を置いて再度お試しください。")

if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.run(os.environ.get("DISCORD_TOKEN"))
