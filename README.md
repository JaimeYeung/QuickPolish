# QuickPolish

Writing in English takes extra effort when it's not your first language. You know what you want to say, but getting it to sound right takes time. And fixing it usually means jumping to another app, copy-pasting, then switching back.

QuickPolish cuts out all of that. Select any text, press a hotkey, and get a polished version in seconds without leaving what you're working on. Works in any macOS app: Gmail, Notion, Slack, Messages, anywhere.

## Demo

1. Select text in any app
2. Press **Control + G**
3. A preview window appears with three modes:
   - **Natural**: casual, like texting a friend
   - **Professional**: for work emails and formal communication
   - **Shorter**: same meaning, fewer words
4. Optionally edit the preview text directly (use **Shift+Enter** for a newline)
5. Press **Tab** to switch modes, **Enter** to replace, **Esc** to cancel

Supports English, Chinese, and Chinglish input. Always outputs natural American English.

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
