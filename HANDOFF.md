# FOCUS — Developer Handoff

> A practical, code-level handoff for anyone picking up this project. Where the
> `README.md` sells the *vision*, this document explains *how the code actually
> works*, how the pieces talk to each other, the known gotchas, and where to
> start if you want to extend it.

---

## 1. What this app is (in one paragraph)

FOCUS is a **Windows-only desktop application** (Python + PyQt5) that helps you
stay on task. You type a high-level goal ("Write my resume"). A **local LLM via
Ollama** breaks it into 4–6 concrete steps, and for each step predicts which
applications you'd legitimately have open. A small **always-on-top overlay**
shows your plan and current step. A **background thread** polls the Windows
foreground window every 3 seconds; if the active app doesn't match the current
step's allowed apps for ~6 seconds, a **nudge dialog** pops up reminding you what
you should be doing. Switch back to a relevant app and the nudge auto-dismisses.

Everything runs locally — no data leaves the machine. The LLM is the only
external dependency, and it runs on `localhost`.

---

## 2. Architecture at a glance

```
┌─────────────────────────────────────────────────────────────┐
│                          main.py                             │
│  FocusApp (orchestrator)  +  SetupScreen  +  PlanWorker      │
│                                                              │
│   SetupScreen  ──(goal)──►  PlanWorker (QThread)             │
│                                   │                          │
│                                   ▼                          │
│                          planner.generate_plan()  ──► Ollama │
│                                   │  (steps: list[dict])     │
│                                   ▼                          │
│   FocusApp._start_session(goal, steps)                       │
│        ├──► OverlayWindow.set_plan()      (overlay.py)       │
│        └──► WindowMonitor.start()         (monitor.py)       │
│                                                              │
│   Signals wired by FocusApp:                                 │
│     Overlay.step_changed     ─► Monitor.set_current_step     │
│     Monitor.drift_detected   ─► show NudgeDialog (nudge.py)  │
│     Monitor.back_on_track    ─► dismiss NudgeDialog          │
│     Nudge.snoozed            ─► Monitor.snooze               │
│     Nudge.back_on_track      ─► dismiss NudgeDialog          │
└─────────────────────────────────────────────────────────────┘
```

The whole app is event-driven via **Qt signals/slots**. There is no shared
mutable global state — `FocusApp` owns the instances and wires their signals
together.

---

## 3. The data contract: a "step"

This is the single most important data structure. The planner produces, and
every other module consumes, a **list of step dicts**:

```python
[
  {
    "step": "Open Word and write the contact header",   # human-readable text
    "allowed_apps": ["winword", "docs.google", "notion"] # keyword substrings
  },
  ...
]
```

- `step` — string shown in the overlay and nudge.
- `allowed_apps` — list of lowercase substrings. The monitor considers you
  "on task" if **any** of these substrings appears in the active window's
  `title + " " + exe_name` (also lowercased). See `monitor._is_on_task`.

If you change this shape, you must update **planner.py**, **monitor.py**, and
**overlay.py** together.

---

## 4. File-by-file walkthrough

### `main.py` — entry point & orchestration
- **`PlanWorker(QObject)`** — runs `planner.generate_plan(goal)` on a background
  `QThread` so the UI doesn't freeze during the (potentially slow) LLM call.
  Emits `finished(list)` or `error(str)`.
- **`SetupScreen(QWidget)`** — the launch window. Collects the goal, disables
  inputs while planning, spins up `PlanWorker`, and on success emits
  `session_started(goal, steps)` then hides itself.
- **`FocusApp`** — the controller. Owns the overlay, monitor, and the current
  nudge dialog. `setQuitOnLastWindowClosed(False)` so closing the setup screen
  doesn't kill the app while the overlay lives on. `_nudge_open` is a guard flag
  preventing multiple stacked nudges.

### `planner.py` — LLM plan generation
- Talks to **Ollama** at `http://localhost:11434/api/generate` using plain
  `urllib` (no SDK). Model is `llama3.2`, requested with `"format": "json"` and
  `"stream": False`.
- `PROMPT_TEMPLATE` instructs the model to return strict JSON with `steps`,
  each having `step` + `allowed_apps`, and gives category hints (note-taking,
  research, writing, coding) for which app keywords to include.
- `generate_plan(goal)` posts the prompt, parses `result["response"]` as JSON,
  and returns `data["steps"]`. **60-second timeout.**

### `monitor.py` — drift detection
- **`WindowMonitor(QObject)`** runs a daemon `threading.Thread` (not a QThread)
  that loops every `interval` seconds (default 3).
- `_get_active_window_info()` uses `win32gui.GetForegroundWindow()` /
  `GetWindowText()` and `win32process` + `psutil` to get `(title, exe)`,
  both lowercased.
- `_is_on_task()` — always returns `True` for the app's own window
  (`python.exe` or title contains `"focus —"`), otherwise checks the current
  step's `allowed_apps` substrings.
- **Drift logic:** requires **2 consecutive** off-task checks (~6s) before
  firing, and won't re-fire within **30 seconds** (`_last_drift_time`) to avoid
  spam. `snooze(seconds)` sets `_snoozed_until` to skip checks entirely.
- Emits `drift_detected(active_window_title, current_step_text)` and
  `back_on_track()`.

### `overlay.py` — floating progress tracker
- **`OverlayWindow(QWidget)`** — frameless, `WindowStaysOnTopHint`, `Tool`.
  Top-right of the primary screen. Draggable (manual `mousePressEvent` /
  `mouseMoveEvent` / `mouseReleaseEvent` since it's frameless).
- **`StepItem(QWidget)`** — one row per step; shows ✓ (done) / ▶ (current) /
  ○ (pending); clickable to jump to that step.
- `set_plan()`, `_refresh_steps()`, `_advance_step()` ("Mark Step Done"),
  `_on_step_clicked()`. Emits `step_changed(index)` whenever the current step
  changes. `flash_warning()` briefly adds a red border on drift.

### `nudge.py` — the distraction warning
- **`NudgeDialog(QDialog)`** — frameless, stays-on-top, centered upper-quarter
  of the screen. Shows "You should be: <current step>" vs "You're in:
  <active window>" (truncated to 60 chars).
- Buttons: **Get back on track** → emits `back_on_track()` + `accept()`;
  **Snooze 5 min** → emits `snoozed(300)` + `reject()`.

---

## 5. The full runtime flow

1. `python main.py` → `FocusApp` shows `SetupScreen`.
2. User types a goal, hits Enter / "Start Focus Session".
3. `PlanWorker` calls Ollama on a worker thread; UI shows "AI is building your
   plan...".
4. On success → `FocusApp._start_session(goal, steps)`:
   - Creates `OverlayWindow`, calls `set_plan`, shows it.
   - Creates `WindowMonitor(interval=3)`, `set_steps`, starts its thread.
5. As you work, the monitor polls the foreground window every 3s.
6. Drift for ~6s → `drift_detected` → overlay flashes red + `NudgeDialog` shows.
7. Switch back to an allowed app → `back_on_track` → nudge auto-dismisses.
   Or click "Snooze 5 min" → monitor pauses checks for 300s.
8. Click "Mark Step Done →" or click a step row → `step_changed` →
   `Monitor.set_current_step` updates which `allowed_apps` are active.

---

## 6. ⚠️ Known issues / gotchas (read before changing anything)

1. **`requirements.txt` is wrong in two ways:**
   - It lists **`anthropic`**, which is **never imported or used** anywhere.
     The planner uses Ollama over `urllib`. This is a leftover; safe to remove.
   - It **omits `psutil`**, which `monitor.py` imports and *requires*. Installing
     only what's in `requirements.txt` will crash at runtime.
   - **Correct set:** `PyQt5`, `pywin32`, `psutil`. (The README's install
     command — `pip install PyQt5 pywin32 psutil` — is actually correct; the
     file is not. Recommend fixing the file to match.)

2. **No JSON-parse hardening in `planner.py`.** If Ollama returns malformed
   JSON, or isn't running, `generate_plan` raises. The error surfaces in
   `SetupScreen._on_error` as text, which is fine, but there's no retry,
   validation of the `steps`/`allowed_apps` shape, or fallback plan.

3. **Ollama must be running first.** No health check; if `localhost:11434` is
   down you get a connection error after attempting the request.

4. **Own-window detection is fragile.** `_is_on_task` whitelists `python.exe`
   and titles containing `"focus —"`. If you package the app as an `.exe`
   (e.g. PyInstaller) the exe name changes and this check breaks — the app may
   nudge you for using FOCUS itself. Revisit this if you package it.

5. **Cross-thread signal emission.** `WindowMonitor` is a plain `threading.Thread`
   emitting Qt signals. This works because Qt queues signals across threads, but
   be careful adding direct UI calls inside the monitor thread — always go
   through signals.

6. **`MODEL` mismatch risk.** `planner.MODEL = "llama3.2"` must match a model you
   actually pulled (`ollama pull llama3.2`). README says `ollama run llama3.2`.

7. **Single-monitor assumption.** Overlay and nudge position off
   `primaryScreen().geometry()`; multi-monitor placement isn't handled.

8. **No session end / "all done" cleanup.** When the last step is marked done the
   button disables, but the monitor keeps running and there's no way to start a
   new session without restarting the app.

---

## 7. How to run locally

```bash
# 1. Install + start Ollama, then pull the model
ollama pull llama3.2
ollama serve          # (or just have the Ollama app running)

# 2. Python deps (use the corrected set, not requirements.txt as-is)
pip install PyQt5 pywin32 psutil

# 3. Run
python main.py
```

Requires **Windows** (uses `win32gui` / `win32process` via `pywin32`).

---

## 8. Common extension points (quick wins)

| You want to…                        | Change…                                                  |
|-------------------------------------|----------------------------------------------------------|
| Use a different LLM model           | `MODEL` in `planner.py`                                   |
| Change how often it checks          | `interval=` in `FocusApp._start_session` (`main.py`)     |
| Change snooze length                | the `300` in `nudge.py` `_on_snooze` (+ button label)    |
| Change drift sensitivity            | `drift_count >= 2` and the `> 30` cooldown in `monitor.py`|
| Restyle the UI                      | the `setStyleSheet(...)` blocks in each widget file       |
| Add validation/fallback for plans   | wrap parsing in `planner.generate_plan`                   |
| Add a "New session" flow            | re-show `SetupScreen` and tear down overlay/monitor in `main.py` |

---

## 9. Suggested next steps for a new maintainer

1. **Fix `requirements.txt`** (remove `anthropic`, add `psutil`). Lowest-risk,
   highest-value cleanup.
2. **Harden `planner.py`**: validate the returned shape, handle Ollama being
   down with a friendly message, optionally provide a static fallback plan.
3. **Add a session-complete / restart flow** so the app is usable for more than
   one goal per launch.
4. **Fix own-window detection** before any packaging effort.
5. Consider a **config file** (model, interval, snooze, theme) instead of
   editing source.

---

## 10. Project files

| File              | Role                                               |
|-------------------|----------------------------------------------------|
| `main.py`         | Entry point, orchestration, setup screen           |
| `planner.py`      | Ollama LLM call → list of step dicts               |
| `monitor.py`      | Background foreground-window polling & drift logic |
| `overlay.py`      | Always-on-top floating progress tracker            |
| `nudge.py`        | Off-track warning dialog                           |
| `requirements.txt`| Python deps (⚠ see §6.1 — currently inaccurate)    |
| `README.md`       | Product/vision overview                            |
| `HANDOFF.md`      | This document                                      |
