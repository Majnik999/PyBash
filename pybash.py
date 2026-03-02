import os
import sys
import subprocess
import getpass
import socket
import platform
import shutil
import time
import html
from datetime import datetime
from pathlib import Path
from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML, FormattedText
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.lexers import PygmentsLexer, DynamicLexer
from pygments.lexers.shell import BashLexer
from prompt_toolkit.filters import Condition
import colorama
from colorama import Fore, Style as ColorStyle

from core.settings import SettingsManager
from core.plugin_manager import PluginManager
from core.completer import PyBashCompleter, AutoSuggestFromCompleter
from core.settings_tui import SettingsTUI
from core.utils import get_history_path

colorama.init()

class PyBashShell:
    def __init__(self):
        self.settings = SettingsManager()
        self._register_appearance_defaults()
        self.settings.load()

        self.builtins = {
            "ls": self.cmd_ls, "cd": self.cmd_cd, "/settings": self.cmd_settings,
            "/restart": self.cmd_restart, "exit": sys.exit, "logout": sys.exit,
            "help": self.cmd_help, "nano": self.cmd_nano,
            "cls": lambda x: os.system('cls' if os.name == 'nt' else 'clear'),
            "clear": lambda x: os.system('cls' if os.name == 'nt' else 'clear'),
        }
        
        self.last_cwd = ""; self.cached_git = ""; self.cached_venv = ""
        self.error_count = 0
        self.last_exec_duration = 0

        self.settings.set_plugin_mode(True)
        self.plugin_manager = PluginManager(self)
        self.plugin_manager.load_plugins()
        self.settings.set_plugin_mode(False)

        self.last_login = self.settings.get("last_run")
        self.settings.set("last_run", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        self.completer = PyBashCompleter(lambda: self.builtins.keys())
        self.auto_suggest = AutoSuggestFromCompleter(self.completer)

    def _register_appearance_defaults(self):
        self.settings.register("File System", "", "Appearance", "ls_dir_color", "ansiblue", str, "Dir Color")
        self.settings.register("File System", "", "Appearance", "ls_file_color", "ansiwhite", str, "File Color")
        self.settings.register("File System", "", "Appearance", "ls_dir_bold", True, bool, "Dir Bold")
        self.settings.register("File System", "", "Appearance", "ls_file_bold", False, bool, "File Bold")
        self.settings.register("Syntax", "", "General", "highlight_enabled", True, bool, "Syntax Highlighting")
        self.settings.register("Syntax", "", "Theme", "syntax_theme", "monokai", str, "Syntax Theme")
        
        self.settings.register("General", "", "Prompt Symbols", "prompt_char", "$", str, "Command prompt character")
        self.settings.register("General", "", "Prompt Symbols", "prompt_start_symbol", "╭─", str, "Top line start symbol")
        self.settings.register("General", "", "Prompt Symbols", "prompt_end_symbol", "╰─", str, "Bottom line start symbol")
        
        self.settings.register("General", "", "Appearance", "prompt_show_git", True, bool, "Show Git branch")
        self.settings.register("General", "", "Appearance", "prompt_show_venv", True, bool, "Show Python Venv")
        self.settings.register("General", "", "Appearance", "prompt_show_path", True, bool, "Show Current Path")

    def print_welcome(self):
        if not self.settings.get("show_welcome"): return
        msg = self.settings.get("welcome_message")
        vars = {
            "user": getpass.getuser(), "host": socket.gethostname(),
            "os": f"{platform.system()} {platform.release()}",
            "python_ver": sys.version.split()[0], "last_login": self.last_login
        }
        try:
            formatted_msg = msg.format(**vars)
            print_formatted_text(HTML(formatted_msg))
        except Exception as e: print(f"Error rendering welcome message: {e}")

    def cmd_restart(self, args):
        print(f"{Fore.YELLOW}Restarting PyBash...{ColorStyle.RESET_ALL}")
        if getattr(sys, 'frozen', False): os.execv(sys.executable, sys.argv)
        else: os.execv(sys.executable, [sys.executable] + sys.argv)

    def cmd_nano(self, args):
        if not args: print("nano: missing file operand"); return
        filename = args[0]; content = ""
        if os.path.exists(filename):
            with open(filename, 'r') as f: content = f.read()
        from prompt_toolkit.layout.containers import HSplit, Window
        from prompt_toolkit.layout.controls import FormattedTextControl
        from prompt_toolkit.widgets import TextArea
        from prompt_toolkit.application import Application
        from prompt_toolkit.layout.layout import Layout
        text_field = TextArea(text=content, lexer=PygmentsLexer(BashLexer), scrollbar=True, line_numbers=True)
        def get_header(): return HTML(f" <style fg='ansiblue'>Nano Editor - {filename}</style> (Ctrl+S: Save, Ctrl+X: Exit)")
        root = HSplit([Window(height=1, content=FormattedTextControl(get_header), style="bg:#444444"), text_field])
        kb = KeyBindings()
        @kb.add('c-s')
        def _(event):
            with open(filename, 'w') as f: f.write(text_field.text)
        @kb.add('c-x')
        def _(event): event.app.exit()
        app = Application(layout=Layout(root), key_bindings=kb, full_screen=True); app.run()

    def register_command(self, name, func): self.builtins[name] = func
    def register_setting(self, tab, group, key, default, value_type=str, description="", options=None):
        self.settings.register(tab, "", group, key, default, value_type, description, options)

    def normalize_paths(self, args):
        if not args: return args
        use_slash = self.settings.get("use_slash_paths")
        if use_slash: return [arg.replace('\\', '/') for arg in args]
        elif os.name == 'nt': return [arg.replace('/', '\\') for arg in args]
        return args

    def get_true_case_path(self, path):
        try:
            p = Path(path).resolve()
            return str(p)
        except: return path

    def format_path(self, path):
        path = self.get_true_case_path(path)
        use_slash = self.settings.get("use_slash_paths")
        if use_slash: return path.replace('\\', '/')
        return path

    def cmd_ls(self, args):
        args = self.normalize_paths(args); path = args[0] if args else "."
        show_hidden = self.settings.get("ls_show_hidden"); show_size = self.settings.get("ls_show_size"); show_date = self.settings.get("ls_show_date")
        try:
            entries = os.listdir(path)
            if not show_hidden: entries = [e for e in entries if not e.startswith('.')]
            dir_c = self.settings.get("ls_dir_color"); file_c = self.settings.get("ls_file_color")
            dir_b = "bold" if self.settings.get("ls_dir_bold") else ""; file_b = "bold" if self.settings.get("ls_file_bold") else ""
            formatted_out = []; full_entries = []
            for e in entries:
                full_path = os.path.join(path, e); is_dir = os.path.isdir(full_path); stats = os.stat(full_path)
                full_entries.append((is_dir, e, stats))
            full_entries.sort(key=lambda x: (not x[0], x[1].lower()))
            for is_dir, name, stats in full_entries:
                style = f"fg:{dir_c} {dir_b}" if is_dir else f"fg:{file_c} {file_b}"
                meta = ""
                if show_size:
                    size = stats.st_size
                    if size > 1024*1024: meta += f" [{size/(1024*1024):.1f}MB]"
                    elif size > 1024: meta += f" [{size/1024:.1f}KB]"
                    else: meta += f" [{size}B]"
                if show_date: meta += f" ({datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d')})"
                formatted_out.append((style, name))
                if meta: formatted_out.append(("fg:#666666 italic", meta))
                formatted_out.append(("", "  "))
            print_formatted_text(FormattedText(formatted_out))
        except Exception as e: print(f"ls: {e}")

    def cmd_cd(self, args):
        args = self.normalize_paths(args); target = args[0] if args else os.path.expanduser("~")
        try: os.chdir(target)
        except Exception as e: print(f"cd: {e}")

    def cmd_settings(self, args):
        if not args: tui = SettingsTUI(self.settings); tui.run(); return
        key, value = args[0], args[1]; self.settings.set(key, value); print(f"[*] Updated {key}")

    def cmd_help(self, args):
        print(f"{Fore.CYAN}--- PyBash Help ---{ColorStyle.RESET_ALL}")
        print("Built-ins:", ", ".join(self.builtins.keys()))

    def _find_upwards(self, current_dir, targets):
        """Recursively checks for targets in current dir and parents."""
        curr = Path(current_dir)
        root = Path(curr.anchor)
        while True:
            for target in targets:
                p = curr / target
                if p.exists(): return str(p)
            if curr == root: break
            curr = curr.parent
        return None

    def _manual_git_check(self, cwd):
        """Fallback: Read .git/HEAD manually if git command fails."""
        git_dir = self._find_upwards(cwd, [".git"])
        if not git_dir: return ""
        
        try:
            head_path = os.path.join(git_dir, "HEAD")
            if not os.path.exists(head_path): return ""
            
            with open(head_path, "r") as f:
                ref = f.read().strip()
                if ref.startswith("ref: refs/heads/"):
                    return html.escape(f"({ref.split('/')[-1]})")
                elif len(ref) > 7:
                    # Detached HEAD (hash)
                    return html.escape(f"({ref[:7]})")
        except: pass
        return ""

    def _update_prompt_cache(self, cwd):
        # 1. Git branch
        if self.settings.get("prompt_show_git"):
            # Try command first
            found = False
            if shutil.which("git"):
                try:
                    output = subprocess.check_output(
                        ["git", "rev-parse", "--abbrev-ref", "HEAD"], 
                        stderr=subprocess.DEVNULL, cwd=cwd
                    ).decode().strip()
                    if output:
                        self.cached_git = html.escape(f"({output})")
                        found = True
                except: pass
            
            # If command failed or git not found, use manual fallback
            if not found:
                self.cached_git = self._manual_git_check(cwd)
        else: self.cached_git = ""
        
        # 2. Venv detection
        if self.settings.get("prompt_show_venv"):
            env = os.environ.get("VIRTUAL_ENV")
            if env:
                self.cached_venv = html.escape(f"({os.path.basename(env)})")
            else:
                venv_cfg = self._find_upwards(cwd, ["pyvenv.cfg"])
                if venv_cfg:
                    venv_name = os.path.basename(os.path.dirname(venv_cfg))
                    self.cached_venv = html.escape(f"({venv_name})")
                else:
                    found_venv = self._find_upwards(cwd, ["venv", ".venv", "env"])
                    if found_venv:
                        self.cached_venv = html.escape(f"({os.path.basename(found_venv)})")
                    else:
                        self.cached_venv = ""
        else: self.cached_venv = ""

    def _format_duration(self, seconds):
        if seconds < 60: return f"{seconds:.1f}s"
        m, s = divmod(int(seconds), 60)
        return f"{m}m {s}s"

    def get_prompt(self):
        cwd = os.getcwd()
        if cwd != self.last_cwd: self._update_prompt_cache(cwd); self.last_cwd = cwd
        
        display_cwd = self.format_path(cwd)
        home = os.path.expanduser("~")
        true_home = self.format_path(home)
        if display_cwd.lower().startswith(true_home.lower()):
            suffix = display_cwd[len(true_home):]
            display_cwd = "~" + suffix
        
        path_c = self.settings.get("prompt_path_color")
        git_c = self.settings.get("prompt_git_color")
        venv_c = self.settings.get("prompt_venv_color")
        user_c = self.settings.get("prompt_user_color")
        time_c = self.settings.get("prompt_time_color")
        conn_c = self.settings.get("prompt_connector_color")
        char_c = self.settings.get("prompt_char_color")
        
        show_uh = self.settings.get("prompt_show_user_host")
        show_time = self.settings.get("prompt_show_time")
        show_icon = self.settings.get("prompt_show_os_icon")
        show_path = self.settings.get("prompt_show_path")
        
        sym_char = self.settings.get("prompt_char")
        sym_start = self.settings.get("prompt_start_symbol")
        sym_end = self.settings.get("prompt_end_symbol")
        
        uh_str = f"<style fg='{user_c}'>{getpass.getuser()}@{socket.gethostname()}</style>:" if show_uh else ""
        time_str = f"<style fg='{time_c}'>[{datetime.now().strftime('%H:%M:%S')}] </style>" if show_time else ""
        icon = (" " if os.name == 'nt' else " ") if show_icon else ""
        path_str = f"<style fg='{path_c}'>{display_cwd}</style>" if show_path else ""
        
        venv_str = f" <style fg='{venv_c}'>{self.cached_venv}</style>" if self.cached_venv else ""
        git_str = f" <style fg='{git_c}'>{self.cached_git}</style>" if self.cached_git else ""
        
        time_right = ""
        if self.last_exec_duration > 2:
            time_right = f" <style fg='#888888'>[{self._format_duration(self.last_exec_duration)}]</style>"

        layout = self.settings.get("prompt_layout")
        
        if layout == "one_line":
            return HTML(f"{time_str}{uh_str}{icon}{path_str}{venv_str}{git_str}{time_right}\n<style fg='{char_c}'>{sym_char} </style>")
        else:
            line1 = f"<style fg='{conn_c}'>{sym_start} </style>{time_str}{uh_str}{icon}{path_str}{venv_str}{git_str}{time_right}"
            line2 = f"\n<style fg='{conn_c}'>{sym_end} </style><style fg='{char_c}'>{sym_char} </style>"
            return HTML(line1 + line2)

    def run(self):
        bindings = KeyBindings()
        @Condition
        def has_suggestion(): return self.session.app.current_buffer.suggestion is not None
        
        @Condition
        def is_navigating_history():
            # Simplistic check: if working index is not equal to the end
            # This is hard to detect perfectly without internal access,
            # but usually we can trust the keybindings to just call history_backward
            # UNLESS there is text.
            # A better check: is the user actively typing?
            # If buffer was modified by user typing, then cycle.
            # If buffer was modified by Up/Down history, then History.
            # We can use a custom flag.
            return getattr(self.session.app.current_buffer, 'history_nav_active', False)

        @bindings.add('up')
        def _(event):
            b = event.app.current_buffer
            
            # If we are already navigating history, keep doing it
            if getattr(b, 'history_nav_active', False):
                b.history_backward()
                return

            # If text is empty, start history nav
            if not b.text:
                b.history_nav_active = True
                b.history_backward()
                return
            
            # Otherwise, cycle autocomplete
            self.auto_suggest.prev_suggestion()
            event.app.invalidate()

        @bindings.add('down')
        def _(event):
            b = event.app.current_buffer
            
            if getattr(b, 'history_nav_active', False):
                b.history_forward()
                # If we return to end of history (empty), clear flag
                if not b.text: # This check might be too late, but decent approx
                    pass 
                return

            if not b.text:
                b.history_nav_active = True
                b.history_forward()
                return

            self.auto_suggest.next_suggestion()
            event.app.invalidate()
        
        # Reset history flag on typing
        @bindings.add('<any>')
        def _(event):
            event.app.current_buffer.history_nav_active = False
            event.app.current_buffer.insert_text(event.data)

        @bindings.add('right', filter=Condition(lambda: self.session.app.current_buffer.cursor_position == len(self.session.app.current_buffer.text)) & has_suggestion)
        def _(event): 
            event.app.current_buffer.insert_text(event.app.current_buffer.suggestion.text)
            event.app.current_buffer.history_nav_active = False
            
        @bindings.add('c-e')
        @bindings.add('tab', filter=has_suggestion)
        def _(event):
            if event.app.current_buffer.suggestion: event.app.current_buffer.insert_text(event.app.current_buffer.suggestion.text)
            event.app.current_buffer.history_nav_active = False

        @bindings.add('c-a')
        def _(event):
            b = event.app.current_buffer; b.cursor_position = 0; b.start_selection(); b.cursor_position = len(b.text)
        @bindings.add('backspace')
        def _(event):
            b = event.app.current_buffer
            b.history_nav_active = False
            if b.selection_state: b.cut_selection()
            else: b.delete_before_cursor()

        history_file = get_history_path()
        def get_lexer():
            if self.settings.get("highlight_enabled") is False: return None
            return PygmentsLexer(BashLexer)
        def get_shell_style():
            color = self.settings.get("ghost_text_color") or "#888888"
            return Style.from_dict({'auto-suggestion': color})

        mode = self.settings.get("autocomplete_mode")
        self.session = PromptSession(
            history=FileHistory(history_file), completer=self.completer,
            auto_suggest=self.auto_suggest if mode == "ghost" else None,
            complete_while_typing=True if mode == "menu" else False,
            lexer=DynamicLexer(get_lexer), style=get_shell_style()
        )

        self.print_welcome()

        while True:
            try:
                # Reset history flag at start of new prompt
                if hasattr(self.session.app, 'current_buffer'):
                    self.session.app.current_buffer.history_nav_active = False
                
                text = self.session.prompt(self.get_prompt, key_bindings=bindings)
                text = text.strip()
                if not text: continue
                parts = text.split(); cmd = parts[0]; args = parts[1:]
                start_time = time.time()
                if cmd in self.builtins: self.builtins[cmd](args)
                else:
                    if cmd.lower() == "dir" and os.name == 'nt':
                        args = self.normalize_paths(args); subprocess.run([cmd] + args, shell=True)
                    else: subprocess.run(text, shell=True)
                self.last_exec_duration = time.time() - start_time
                self.error_count = 0
            except KeyboardInterrupt: print("^C"); self.error_count = 0
            except EOFError: break
            except Exception as e:
                print(f"Shell error: {e}"); self.error_count += 1
                if self.error_count >= 100: print(f"{Fore.RED}Too many consecutive errors (100). Auto-exiting.{ColorStyle.RESET_ALL}"); break

if __name__ == "__main__": PyBashShell().run()
