# FOCUS

**Close the Execution Gap. Stop planning. Start doing.**

FOCUS is a Windows desktop application designed to act as your automated Navigator. By combining a local Large Language Model (LLM) with active window monitoring, FOCUS breaks down your high-level goals into actionable steps and gently nudges you back on task if you start to drift.

## 💡 Core Insight: The Navigator vs. The Driver

Getting things done requires two brain modes — but context-switching between them is a massive flow blocker. FOCUS acts as your automated Navigator, so you can just be the Driver.

*   **The Navigator**: Planning, prioritizing, monitoring your progress.
*   **The Driver**: Head down, hands on the wheel, executing.

## 🦹 The Real Villain: The Fake Work Epidemic

The most dangerous distraction isn't social media — it's the work that feels productive but isn't.
*   **It feels like work**: Watching a 45-minute tutorial instead of writing a simple script.
*   **It looks like work**: Productive procrastination gives the dopamine hit of output — with none of the actual results.

## ⚠️ The Problem: The $100 Billion Execution Crisis

*   **Annual Cost**: Lost to distraction and low productivity in the US.
*   **"Fake Work"**: A massive portion of the workday is lost to "work about work" and app-switching.
*   **Flow Recovery**: There is a severe penalty to regain focus after a single distraction.
*   **Market Opportunity**: Projected size of the productivity software market by 2032 is driven by the need for execution automation.

## ⚔️ Competitive Landscape: Where FOCUS Lives

Most tools rely on **Passive Tracking (Autopsy)** and **Rigid Rules (Binary blocking)**. They give you an autopsy on Friday of the time you wasted on Tuesday, using dumb website blockers.

**★ FOCUS** lives in the realm of **Active Coaching (Real-time)** and is **Context-Aware (Intent-based)**. It understands the context of why you have an app open and provides real-time coaching.

## 🌊 The Flow Engine: How FOCUS Triggers Flow

*   **Context Switching**: Saves the 23-minute recovery penalty by intervening the exact second you stray.
*   **Ambiguity Paralysis**: Forces focus on just one thing, killing decision fatigue.
*   **Immediate Feedback**: Real-time course correction creates the feedback loop required for flow state.
*   **Cognitive Offloading**: We monitor, you execute. Self-discipline is automated.

---

## 🚀 Features

*   **AI-Powered Task Planning**: Tell FOCUS what you want to accomplish, and it breaks it down into 4-6 concrete, actionable steps.
*   **Active Context Monitoring**: FOCUS compares what you are currently doing with what applications are expected for your current step.
*   **Smart Nudges**: If you get distracted, FOCUS displays a non-intrusive nudge dialog reminding you of your current step. 
*   **Floating Progress Overlay**: A sleek, minimal, always-on-top overlay keeps your current step visible at all times.

## ⚙️ Under the Hood: Technical Execution

A lightweight, invisible agent. The Python backend polls Windows APIs every 3 seconds, feeds context to a local LLM to evaluate intent, and fires a nudge overlay if you stray. The second you switch back — zero clicks required — the nudge auto-dismisses.

The application is built using Python and PyQt5, split across modular components:
*   **`main.py`**: The entry point. Handles setup and orchestrates communication between monitor, planner, and UI.
*   **`planner.py`**: Communicates with the local Ollama instance to generate the plan and predict allowed apps for each step.
*   **`monitor.py`**: Background thread that checks the active foreground window using `win32gui` and `psutil`.
*   **`overlay.py`**: The floating, frameless progress tracker UI.
*   **`nudge.py`**: The dialog UI for distraction warnings.

## 🛡️ Ethical Alignment: The Zero-Byte Guarantee

**100% Local. 100% Private.**
*   **Zero data leaves your machine**: The LLM runs locally via Ollama — no cloud, ever.
*   **Reads window titles, NOT screen content**: Just the app name — total transparency.
*   **Nudges, not locks**: Serves the user's intent, not an algorithm.

## 🌍 The Impact: Reclaiming Human Potential

*   **The Micro (For the Individual)**: Reclaims 2+ hours of trapped productivity a day, curing the "I was busy all day but got nothing done" burnout.
*   **The Macro (For the Enterprise)**: Transforms teams from endless "planning and researching" to actively shipping and delivering results.
*   **The Moat**: While AI makes idea generation cheaper, focused human execution remains the ultimate bottleneck and competitive advantage.

## 🔮 The Future: From Coach to Master Planner

*   **Calendar & Notes Integration**: Know what's urgent and actively push toward high-leverage tasks.
*   **Urgency & Importance Nudging**: Context-aware prioritization in real time.
*   **Adaptive Task Estimation**: Learns your execution speed over time to help you accurately estimate and conquer your workload.

---

## 📋 Prerequisites & Installation

1.  **Windows OS**: Relies on Windows-specific APIs (`pywin32`).
2.  **Python 3.8+**
3.  **Ollama**: Install and run [Ollama](https://ollama.com/) locally. Pull the model:
    ```bash
    ollama run llama3.2
    ```
4.  **Dependencies**:
    ```bash
    pip install PyQt5 pywin32 psutil
    ```

## 🚀 Usage

1.  Ensure your local Ollama server is running.
2.  Run the application: `python main.py`
3.  **Start a Session**: Type your high-level goal and click "Start Focus Session".
4.  **Work**: The application generates a plan and shows the overlay. If you open an irrelevant app, FOCUS will gently remind you to get back to work. Click "Mark Step Done" as you progress.

## 🎨 Customization
*   **LLM Model**: Change the `MODEL` variable in `planner.py`.
*   **Monitoring Interval**: Change the `interval` parameter in `main.py` (default: 3 seconds).
*   **Snooze Duration**: Change in `nudge.py` (default: 5 minutes).

## 📄 License
This project is open-source and available for personal use and modification.
