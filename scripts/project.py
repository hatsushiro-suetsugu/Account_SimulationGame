from openai import OpenAI
client = OpenAI()

completion = client.chat.completions.create(
  model="gpt-4o-mini",
  messages=[
    {"role": "system", "content": "あなたは宇宙開発ベンチャーのCEOです。現在あなたの企業はシリースAラウンドで資金調達が必要なタイミングに来ています。今VC"},
    {"role": "user", "content": "明日の天下一武道会の意気込みをお願いします！"}
  ]
)

print(completion.choices[0].message)
