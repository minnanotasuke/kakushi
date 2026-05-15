"""HuggingFace Space — kakushi 隠し demo.

Lets non-developers paste Japanese business text, optionally provide a
company dictionary, and see exactly what would be sent to an LLM after
masking. Input and mapping live in the Space process memory only —
nothing is persisted to disk, nothing is logged.
"""

import json

import gradio as gr

from kakushi import mask


_EXAMPLE_TEXT = """田中太郎様

いつもお世話になっております。
株式会社山田商事の件で、¥1,500,000の見積書を tanaka@example.co.jp にお送りいたしました。
ご確認のほど、よろしくお願いいたします。

電話: 090-1234-5678
担当: 佐藤花子
"""

_EXAMPLE_DICT = '{"株式会社山田商事": "取引先A"}'


def _parse_dict(raw: str):
    if not raw or not raw.strip():
        return None
    try:
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            return None
        return parsed
    except json.JSONDecodeError:
        return None


def run(text: str, dict_json: str):
    if not text.strip():
        return "", "", ""
    dictionary = _parse_dict(dict_json)
    masked, mapping = mask(text, dictionary=dictionary)
    mapping_lines = [
        f"{ph}  ←  {orig}"
        for ph, orig in mapping.placeholder_to_original.items()
    ]
    mapping_str = "\n".join(mapping_lines) if mapping_lines else "(検出なし)"

    counts: dict = {}
    for ph in mapping.placeholder_to_original:
        if ph.startswith("<") and "_" in ph:
            et = ph.strip("<>").rsplit("_", 1)[0]
        else:
            et = "DICT"
        counts[et] = counts.get(et, 0) + 1
    summary = "  ·  ".join(f"{k}: {v}" for k, v in sorted(counts.items())) or "0件"
    return masked, mapping_str, summary


with gr.Blocks(title="kakushi — 日本語PII マスキング", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # kakushi 隠し
        日本語のビジネステキストを ChatGPT や Claude に送る前に、個人名・社名・電話・メール・金額などの個人情報を自動的にマスキングします。マスク後のテキストだけが API に送信され、原文・マッピングはサーバーに残りません。
        """
    )

    with gr.Row():
        with gr.Column():
            text_in = gr.Textbox(
                label="入力テキスト",
                lines=12,
                value=_EXAMPLE_TEXT,
                placeholder="ここに日本語ビジネステキストを貼り付け",
            )
            dict_in = gr.Textbox(
                label="会社辞書 (任意・JSON 形式)",
                lines=3,
                value=_EXAMPLE_DICT,
                placeholder='例: {"株式会社山田商事": "取引先A"}',
            )
            run_btn = gr.Button("マスキング実行", variant="primary")

        with gr.Column():
            masked_out = gr.Textbox(
                label="マスク後 (LLM に送信される形)",
                lines=12,
                interactive=False,
                show_copy_button=True,
            )
            summary_out = gr.Textbox(
                label="検出されたエンティティ数",
                lines=1,
                interactive=False,
            )
            mapping_out = gr.Textbox(
                label="マッピング (このサーバーのメモリ上のみ・保存されません)",
                lines=8,
                interactive=False,
            )

    gr.Markdown(
        """
        ---
        **保存ポリシー**: 入力テキスト・マスキング結果・マッピングはすべてプロセスメモリ上で処理され、リクエスト完了時点で消去されます。アクセスログ・入力ログは保存しません。

        **ライブラリとして組み込む**: `pip install kakushi[ner]`
        **ソースコード**: [github.com/minnanotasuke/kakushi](https://github.com/minnanotasuke/kakushi)
        """
    )

    run_btn.click(
        run,
        inputs=[text_in, dict_in],
        outputs=[masked_out, mapping_out, summary_out],
    )


if __name__ == "__main__":
    demo.launch()
