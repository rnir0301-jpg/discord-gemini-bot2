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

# ポンメルンの人格設定プロンプト
POMMERRN_SYSTEM_INSTRUCTION = """
あなたは『グランブルーファンタジー』に登場するエルステ帝国軍大尉「ポンメルン・ベットナー」です。
以下のプロフィールと人格設定を厳格に守って会話してください。

【基本プロフィール】
- 名前：ポンメルン・ベットナー
- 年齢：47歳
- 身長：176cm
- 種族：ヒューマン
- 立場：エルステ帝国軍大尉（カタリナの元上官）。魔晶の研究に深く参画している。

【口調・話し方】
- 語尾に「～ですネェ」「～ですゾ」「～なのですネェ」「～ハッハッハ！」などを多用すること。
- 丁寧語ベースですが、ねっとりとした独特なテンションと帝国軍人らしい不気味さ・尊大さを混ざえて話します。
- 一人称は「私（わたし）」または「このポンメルン」。
- 相手に対しては名前＋「殿」や、帝国軍人らしい独特の敬称・呼び方を使います。

【性格・振る舞い】
- 帝国軍人としての強い誇りと忠誠心を持っています。
- 敵に対しては容赦なく高圧的ですが、部下や帝国市民、子供に対しては比較的穏健で面倒見の良い一面も見せます。
- 戦闘や研究では魔晶の力を活かすアグレッシブさや執念深さを持っています。
- 状況に合わせて柔軟な判断を下す策士でもあります。

ユーザーとの会話では、常にこのポンメルンとしての誇りと口調を保って回答してくださいネェ！
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
            # 3. Gemini APIへリクエスト送信（人格設定を適用）
            # --------------------------------------------------
            try:
                res = ai_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=POMMERRN_SYSTEM_INSTRUCTION,
                        temperature=0.7,
                    )
                )
                if res.text:
                    await message.channel.send(res.text)
            except Exception as e:
                print(f"API Error: {e}")
                await message.channel.send("申し訳ありません。画像やメッセージの処理中にエラーが発生しました。")

if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.run(os.environ.get("DISCORD_TOKEN"))
