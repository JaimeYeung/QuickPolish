# QuickPolish

Fix grammar and rewrite selected text using AI — without leaving your app.

Select any text, press a hotkey, and get a polished version in seconds. Works in any macOS app (Gmail, Notion, Messages, etc.).

## Demo

1. Select text in any app
2. Press **Control + Option + Q**
3. A preview window appears with three modes:
   - **Natural** — casual, like texting a friend
   - **Professional** — for emails and interviews
   - **Shorter** — same meaning, fewer words
4. Press **Tab** to switch modes, **Enter** to replace, **Esc** to cancel

Supports English, Chinese, and Chinglish input — always outputs natural American English.

## Setup

**Requirements:** Python 3.11+, macOS

```bash
git clone https://github.com/JaimeYeung/QuickPolish.git
cd QuickPolish
pip install -r requirements.txt
python main.py
```

On first run, you'll be asked for your OpenAI API key. Get one at [platform.openai.com](https://platform.openai.com).

## Permissions

macOS will ask for **Accessibility** permission on first run. This is required to simulate Cmd+C and Cmd+V.

> System Settings → Privacy & Security → Accessibility → add your Terminal app

## Running in the background

```bash
nohup python main.py > ~/quickpolish.log 2>&1 &
```

To stop:
```bash
pkill -f main.py
```
