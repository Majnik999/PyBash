# ⚙️ PyBash Settings Reference

## 🛠️ General > Behavior

| Key | Description | Options | Default |
|-----|-------------|---------|---------|
| `history_limit` | Max history lines | - | `1000` |
| `show_welcome` | Startup message | `True/False` | `True` |
| `show_dev_logs` | Plugin debug logs | `True/False` | `False` |
| `use_slash_paths` | Force `/` on Windows | `True/False` | `True` |
| `autocomplete_mode` | Suggestion style | `ghost`, `menu` | `ghost` |
| `ls_show_hidden` | Show `.` files | `True/False` | `False` |

## 🎨 General > Appearance

| Key | Description | Default |
|-----|-------------|---------|
| `prompt_layout` | Prompt structure (`two_line`, `one_line`) | `two_line` |
| `welcome_message` | Startup text (supports `{user}`, `{host}`, `{os}`) | *See Default* |
| `prompt_path_color` | Current directory color | `ansicyan` |
| `prompt_git_color` | Git branch color | `ansimagenta` |
| `prompt_venv_color` | Virtual Env color | `ansiyellow` |
| `prompt_connector_color` | Line/Connector color (`╭─`) | `ansiwhite` |
| `prompt_char_color` | Input symbol color (`$`) | `ansiwhite` |
| `prompt_show_git` | Toggle Git info | `True` |
| `prompt_show_venv` | Toggle Venv info | `True` |
| `prompt_show_time` | Toggle Timestamp | `False` |

## 🔣 General > Prompt Symbols

| Key | Description | Default |
|-----|-------------|---------|
| `prompt_start_symbol` | Top line start | `╭─` |
| `prompt_end_symbol` | Bottom line start | `╰─` |
| `prompt_char` | Input character | `$` |

## 📁 File System > Appearance

| Key | Description | Default |
|-----|-------------|---------|
| `ls_dir_color` | Folder color | `ansiblue` |
| `ls_file_color` | File color | `ansiwhite` |
| `ls_dir_bold` | Bold folders | `True` |
