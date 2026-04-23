# QuickPolish — Design Spec
Date: 2026-04-21

## Overview

QuickPolish is a lightweight macOS background app that corrects grammar and rewrites selected text using the OpenAI API. The user selects text in any app, presses a global hotkey, and a preview window appears with the corrected result. The user confirms with Enter or cancels with Esc.

---

## User Flow

1. User selects text in any macOS app (email, Notion, browser, etc.)
2. User presses **⌃G** (Control + G)
3. App simulates Cmd+C to copy selected text
4. Three parallel OpenAI API requests are sent (Natural, Professional, Shorter)
5. Preview window appears (~1–2 seconds) showing the Natural result by default
6. User optionally presses **Tab** to cycle through modes: Natural → Professional → Shorter → Natural
7. User optionally edits the preview text directly in the window. Per-mode edits are preserved when cycling with Tab. **Shift+Enter** inserts a newline inside the editor.
8. User presses **Enter** to accept → app writes result to clipboard → simulates Cmd+V to replace original text
9. Or presses **Esc** to cancel → window closes, original text unchanged

---

## Preview Window

Small floating window, always on top, centered on screen:

```
┌─────────────────────────────────┐
│  ✦ QuickPolish                  │
├─────────────────────────────────┤
│  I think this approach works    │
│  well for our use case.         │
├─────────────────────────────────┤
│  [Natural]  Professional  Shorter│
├─────────────────────────────────┤
│  ↩ Replace  ⇧↩ Newline  Tab  Esc│
└─────────────────────────────────┘
```

- Current mode shown in brackets
- Tab cycles modes instantly (all 3 results pre-fetched in parallel)
- Text area is an editable multi-line field once results arrive; edits made in one mode persist when cycling with Tab
- Shift+Enter inserts a newline inside the editor; plain Enter always means "accept and paste"
- Loading spinner shown while API requests are in flight

---

## Rewrite Modes

| Mode | Prompt instruction |
|------|-------------------|
| **Natural** | Understand the intended meaning and express it the way you'd say it to a friend — casual, chill, natural American English. Not a grammar fix, not a translation. Think: how would a native speaker say this in a text message? |
| **Professional** | Understand the intended meaning and express it for a professional email context — especially interview-related or formal replies. Sound like a confident, competent human. Be direct and warm, not stiff. Avoid all AI filler ("I hope this email finds you well", "please don't hesitate", "as per my previous email", "I wanted to reach out"). |
| **Shorter** | Understand the intended meaning, express it in natural American English, then cut it down. Remove redundancy without losing the point. Keep the appropriate register (casual stays casual, formal stays formal). |

### Shared constraints across all modes
- Output is always in English, regardless of input language.
- Input may be Chinese, English, or a mix of both (Chinglish). Always output natural American English.
- Do not translate literally. Understand the intended meaning and express it the way a native American English speaker would naturally say it.
- Do not sound like an AI assistant. The output should feel like it was written by a real person who writes well.
- Do not add words or phrases that weren't implied by the original.
- Do not use em dashes (—) or en dashes (–). They are a strong AI signal. Use commas, periods, or parentheses instead. Regular hyphens in compound words like "well-known" are fine. The rewriter also strips any stray em/en dashes from model output as a safety net.

---

## Architecture

Single Python process, runs in the background as a macOS menubar app.

```
pynput          — global hotkey listener (⌃G, via keyboard.HotKey + Listener)
pyperclip       — read/write clipboard
osascript       — simulate Cmd+C and Cmd+V keystrokes
openai          — OpenAI API (gpt-4o, 3 parallel async requests)
tkinter         — floating preview window
rumps            — macOS menubar icon and menu
```

### Component breakdown

- **hotkey_listener.py** — registers global ⌃G hotkey, triggers the pipeline
- **text_grabber.py** — simulates Cmd+C, reads clipboard, returns selected text
- **rewriter.py** — sends 3 async OpenAI requests, strips AI-style em/en dashes from the output, returns dict of {mode: result}
- **preview_window.py** — tkinter floating window with an editable text area; handles Tab (switch mode, preserves per-mode edits), Enter (accept), Shift+Enter (newline), Esc (cancel)
- **replacer.py** — writes result to clipboard, reactivates the original app, simulates Cmd+V
- **menubar.py** — rumps menubar icon, settings (hotkey, API key), quit

---

## Error Handling

- No text selected → do nothing (or brief system beep)
- OpenAI API error → show error message in preview window, do not replace text
- Network timeout (>8s) → show timeout message, allow retry or cancel
- Missing API key → show setup instructions in menubar

---

## Configuration

Stored in `~/.quickpolish/config.json`:
- `openai_api_key` — OpenAI API key
- `hotkey` — default `ctrl+g`
- `model` — default `gpt-4o`

---

## macOS Permissions Required

- **Accessibility** — to simulate Cmd+C and Cmd+V keystrokes
- User prompted on first launch with instructions

---

## Out of Scope (MVP)

- Custom prompt editing
- History of past corrections
- Support for languages other than English
- Distributing as a signed .app bundle
