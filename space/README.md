---
title: kakushi
emoji: "\U0001F510"
colorFrom: blue
colorTo: gray
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: mit
short_description: Japanese PII masking for LLM pipelines
---

# kakushi 隠し

ChatGPT・Claude・Gemini に日本語ビジネステキストを送る前に、個人情報を自動マスキングする無料デモです。

- 個人名、社名、電話番号、メールアドレス、金額、マイナンバーなどを自動検出
- 会社辞書を渡すと、自社の取引先名を `取引先A` のような任意の文字列に置き換え
- 入力・マッピングは一切保存されません

ライブラリとしての利用は [github.com/minnanotasuke/kakushi](https://github.com/minnanotasuke/kakushi) を参照してください。
