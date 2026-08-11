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

# Discord Bot設定（メッセージコンテンツの読み取り権限が必要）
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
    # Bot自身のメッセージには反応しない
    if message.author == bot.user:
        return

    # メンションされた場合、またはDMの場合のみ応答
    if bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        # 入力中アニメーション（「...を入力中」）を表示
        async with message.channel.typing():
            contents = []

            # --------------------------------------------------
            # 1. 直近のメッセージ履歴を取得（文脈の理解）
            # --------------------------------------------------
            # 直近5件の履歴を取得
            async for msg in message.channel.history(limit=5, oldest_first=True):
                # 今送信された最後のメッセージ自体は後で画像処理とともに個別処理するためスキップ
                if msg.id == message.id:
                    continue

                clean_msg = msg.content.replace(f"<@{bot.user.id}>", "").strip()
                if clean_msg:
                    speaker = "Bot" if msg.author == bot.user else msg.author.display_name
                    contents.append(f"{speaker}: {clean_msg}")

            # --------------------------------------------------
            # 2. 今回送信されたメッセージと添付画像の処理
            # --------------------------------------------------
            current_text = message.content.replace(f"<@{bot.user.id}>", "").strip()
            
            # 画像が添付されている場合
            if message.attachments:
                for attachment in message.attachments:
                    # 画像ファイル（png, jpg, webpなど）かチェック
                    if attachment.content_type and attachment.content_type.startswith('image/'):
                        image_bytes = await attachment.read()
                        
                        # Gemini APIに渡す画像オブジェクトを作成
                        image_part = types.Part.from_bytes(
                            data=image_bytes,
                            mime_type=attachment.content_type
                        )
                        contents.append(image_part)

            # テキストプロンプトを追加（入力が空の場合はデフォルト指示を補填）
            if not current_text and message.attachments:
                current_text = "添付された画像について感想や説明をお願いします。"
            
            if current_text:
                user_prompt = f"{message.author.display_name}: {current_text}"
                contents.append(user_prompt)

            # 処理する要素が無い場合は終了
            if not contents:
                return

            # --------------------------------------------------
            # 3. Gemini APIへリクエスト送信
            # --------------------------------------------------
            try:
                res = ai_client.models.generate_content(
                    model="gemini-3.5-flash-lite",
                    contents=contents
                )
                if res.text:
                    await message.channel.send(res.text)
            except Exception as e:
                print(f"API Error: {e}")
                await message.channel.send("申し訳ありません。画像やメッセージの処理中にエラーが発生しました。")

if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.run(os.environ.get("DISCORD_TOKEN"))
