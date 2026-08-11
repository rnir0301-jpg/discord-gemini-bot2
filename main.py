import os
import io
from threading import Thread
from flask import Flask
import discord
from google import genai
from google.genai import types

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

# --------------------------------------------------
# システムプロンプト（Botの全体的な設定・指示）
# --------------------------------------------------
SYSTEM_INSTRUCTION = """
あなたはDiscordサーバーの親しみやすく優秀なAIアシスタント「gemi-bot」です。

【基本ルール】
・丁寧で分かりやすい言葉遣いで回答してください。
・画像が添付された場合は、何が写っているかを分析・観察し、質問に答えたり感想を述べてください。
・回答は簡潔かつ的確にまとめ、長くなりすぎないように配慮してください。
"""

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    # Bot自身のメッセージには反応しない
    if message.author == bot.user:
        return

    # メンションされた場合、またはDMの場合のみ応答
    if bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        async with message.channel.typing():
            contents = []

            # 1. 直近のメッセージ履歴を取得（文脈の理解）
            async for msg in message.channel.history(limit=5, oldest_first=True):
                if msg.id == message.id:
                    continue

                clean_msg = msg.content.replace(f"<@{bot.user.id}>", "").strip()
                if clean_msg:
                    speaker = "Bot" if msg.author == bot.user else msg.author.display_name
                    contents.append(f"{speaker}: {clean_msg}")

            # 2. 今回送信されたメッセージと添付画像の処理
            current_text = message.content.replace(f"<@{bot.user.id}>", "").strip()
            
            # 画像が添付されている場合
            if message.attachments:
                for attachment in message.attachments:
                    if attachment.content_type and attachment.content_type.startswith('image/'):
                        image_bytes = await attachment.read()
                        
                        image_part = types.Part.from_bytes(
                            data=image_bytes,
                            mime_type=attachment.content_type
                        )
                        contents.append(image_part)

            # テキストプロンプトの補填
            if not current_text and message.attachments:
                current_text = "この画像について教えてください。"
            
            if current_text:
                user_prompt = f"{message.author.display_name}: {current_text}"
                contents.append(user_prompt)

            if not contents:
                return

            # 3. Gemini APIへリクエスト送信（システムプロンプトを適用）
            try:
                res = ai_client.models.generate_content(
                    model="gemini-3.5-flash-lite",
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION
                    )
                )
                if res.text:
                    await message.channel.send(res.text)
            except Exception as e:
                print(f"API Error: {e}")
                await message.channel.send("申し訳ありません、エラーが発生しました。しばらく経ってから再度お試しください。")

if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.run(os.environ.get("DISCORD_TOKEN"))
