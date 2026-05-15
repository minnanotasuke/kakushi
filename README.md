# kakushi 隠し

**Japanese PII masking for LLM pipelines.** Strip personal names, company names, phone numbers, emails, amounts, and my-numbers from Japanese business text before it leaves your server. Restore them in the model reply.

[Live demo on HuggingFace Spaces](https://huggingface.co/spaces/choudai/kakushi) · [日本語の説明](README_ja.md)

---

## Why

You want to send a Japanese email, meeting note, or invoice to OpenAI / Anthropic / Gemini for summarisation, rewriting, or QA. The text contains customer names (`田中太郎`), company names (`株式会社山田商事`), deal amounts (`¥1,500,000`), and contact details. You don't want those bytes leaving your server.

kakushi gives you a three-line workaround.

```python
from kakushi import mask, unmask

masked, mapping = mask(
    "田中太郎様、株式会社山田商事の件で¥1,500,000の見積書を tanaka@example.co.jp にお送りします",
    dictionary={"株式会社山田商事": "取引先A"},   # optional — pin sensitive names
)
# masked  → "<PERSON_1>様、取引先Aの件で<AMOUNT_1>の見積書を <EMAIL_1> にお送りします"
# mapping → in-memory only. Never persisted.

reply = call_openai(masked)                   # your LLM call here
final = unmask(reply, mapping)                # placeholders → originals
```

## Install

```bash
pip install kakushi          # regex layer only — fast, no model download
pip install kakushi[ner]     # + GiNZA Japanese NER (person / org / location)
```

## What gets caught

Three layers, lowest priority first.

1. **GiNZA NER** — `PERSON`, `ORG`, `LOCATION` from the Japanese spaCy pipeline.
2. **Regex** — phone, postal code, email, my-number, yen amount, IPv4, driver's license, credit card, URL, contract / order numbers, **and Japanese company names** with `株式会社` / `合同会社` / `(株)` markers.
3. **Company dictionary** *(optional)* — `{"株式会社山田商事": "取引先A"}`. Highest priority. The value can be `None`, in which case kakushi auto-assigns `<COMPANY_DICT_N>`.

Overlapping spans are resolved with priority `dict > regex > NER`, with the longer span winning at the same priority.

## Recall on synthetic corpus (100 cases, NER on)

| Entity | Recall |
|---|---|
| AMOUNT | **100%** |
| EMAIL | **100%** |
| PERSON | **100%** |
| PHONE | **100%** |
| ORG | **92%** |
| LOCATION | 60.9% |
| **Overall** | **95.7%** |

Reproduce with `python scripts/eval.py --n 100`.

## Known limitations

- **Hiragana-leading company names** (`株式会社さくら通信`, `合同会社みどり`) are missed by the regex because including hiragana in the body would destroy the particle boundary. Register them via the company dictionary.
- **Compound place names** like `京都府京都市` are sometimes split by GiNZA.
- **My-number checksums** are not validated yet. Any 12-digit `dddd-dddd-dddd` pattern is matched.
- The `mapping` returned from `mask()` is **in-memory only**. Do not serialize it, log it, or write it to disk. It contains the originals you just removed.

## Try it without writing code

The [HuggingFace Space](https://huggingface.co/spaces/choudai/kakushi) lets you paste any Japanese text, optionally provide a company dictionary, and see exactly what would be sent to the LLM. Nothing is logged.

## Project layout

```
kakushi/
├── src/kakushi/
│   ├── normalizer.py     # NFKC + context-aware hyphen folding
│   ├── patterns.py       # 12 regex patterns (PII + Japanese company names)
│   ├── ner.py            # GiNZA wrapper (lazy load, optional)
│   ├── resolver.py       # span overlap resolution
│   ├── masker.py         # mask() / unmask() / company dictionary
│   ├── synth.py          # synthetic business-text generator
│   └── types.py          # EntityType, Match
├── tests/                # 70 cases, all green
├── scripts/eval.py       # recall measurement on synthetic corpus
├── examples/openai_demo.py
└── space/                # HuggingFace Space app (Gradio)
```

## License

MIT.
