# ╭─ PyBash Shell
# ╰─ $ Advanced, Customizable Python Terminal

PyBash is a powerful, cross-platform shell built with Python. It features a modern two-line prompt, smart environment detection, and a deeply customizable TUI.

---

## ✨ Key Features

### 🛠️ Core Power
*   **Recursive Environment Detection:** Automatically finds Git repositories (`.git`) and Virtual Environments (`venv`, `.venv`, `pyvenv.cfg`) even when you are deep inside subdirectories.
*   **Smart Autocomplete:**
    *   **Ghost Mode:** Grey text suggestions that you can accept with `Tab` or `Ctrl+E`.
    *   **Menu Mode:** Classic dropdown list.
    *   **Sub-commands:** Supports `git`, `pip`, `npm`, `docker`, and more.
*   **Execution Timer:** Displays command duration if it exceeds 2 seconds.
*   **Safety Net:** Auto-exits if 100 consecutive internal errors occur.

### 🎨 Deep Customization
*   **Layout Modes:** Choose between `two_line` (classic) or `one_line` (compact) prompts.
*   **True Color Support:** Use Hex codes (`#ff5733`) or ANSI names for every part of the UI.
*   **Symbols:** Customize the `╭─`, `╰─`, and `$` characters.
*   **Toggles:** Turn off any element (User, Host, Path, Time, Git, Venv) via settings.

### 📦 Tools
*   **`nano`**: A built-in, full-screen text editor.
*   **`ls`**: Enhanced directory listing with colors, bolding, and icons.
*   **`/settings`**: Interactive TUI configuration manager.

---

## 🚀 Getting Started

1.  **Install:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Run:**
    ```bash
    python pybash.py
    ```
3.  **Portable Build:**
    ```bash
    python build-portable.py
    ```

---

## ⚙️ Configuration

Type `/settings` to open the configuration menu. Use arrow keys to navigate.

*   **General > Appearance > prompt_layout**: Switch between `two_line` and `one_line`.
*   **General > Prompt Symbols**: Change the connector lines and prompt character.
*   **General > Behavior > use_slash_paths**: Force `/` separators on Windows.

---

<p align="center">
  <i>This code was made 50% by ai and 50% by me</i>
</p>
