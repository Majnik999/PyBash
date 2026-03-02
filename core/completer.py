from prompt_toolkit.auto_suggest import AutoSuggest, Suggestion
from prompt_toolkit.completion import PathCompleter, Completer, Completion, NestedCompleter
import os
import threading

class AutoSuggestFromCompleter(AutoSuggest):
    def __init__(self, completer):
        self.completer = completer
        self.current_index = 0
        self._last_text = ""
        self._completions = []

    def get_suggestion(self, buffer, document):
        text = document.text_before_cursor
        if not text.strip(): return None
        
        if text != self._last_text:
            self._last_text = text
            self.current_index = 0
            self._completions = list(self.completer.get_completions(document, None))

        if not self._completions: return None

        idx = self.current_index % len(self._completions)
        completion = self._completions[idx]
        
        if completion.start_position < 0:
            offset = -completion.start_position
            return Suggestion(completion.text[offset:])
        else:
            return Suggestion(completion.text)

    def next_suggestion(self):
        if self._completions: self.current_index += 1

    def prev_suggestion(self):
        if self._completions: self.current_index -= 1


class PyBashCompleter(Completer):
    def __init__(self, get_builtins):
        self.get_builtins = get_builtins
        self.path_completer = PathCompleter()
        self._cache_commands = set()
        self._cache_loaded = False
        
        self.nested_dict = {
            'git': {
                'status': None, 'commit': None, 'push': None, 'pull': None,
                'checkout': None, 'branch': None, 'add': None, 'clone': None,
                'log': None, 'diff': None, 'merge': None, 'init': None
            },
            'pip': {
                'install': None, 'uninstall': None, 'list': None, 'freeze': None,
                'show': None, 'check': None, 'config': None, 'cache': None
            },
            'npm': {
                'install': None, 'start': None, 'run': None, 'test': None,
                'build': None, 'publish': None, 'init': None
            },
            'python': {
                '-m': None, '--version': None, '--help': None, '-c': None
            },
            'docker': {
                'ps': None, 'images': None, 'run': None, 'build': None, 
                'stop': None, 'rm': None, 'rmi': None, 'exec': None
            }
        }
        self.nested_completer = NestedCompleter.from_nested_dict(self.nested_dict)
        
        threading.Thread(target=self._load_system_commands, daemon=True).start()

    def _load_system_commands(self):
        paths = os.environ.get("PATH", "").split(os.pathsep)
        for p in paths:
            if os.path.isdir(p):
                try:
                    for f in os.listdir(p):
                        if f.lower().endswith((".exe", ".bat", ".cmd", ".sh", ".py")):
                            self._cache_commands.add(f.lower())
                            self._cache_commands.add(os.path.splitext(f)[0].lower())
                        elif "." not in f: self._cache_commands.add(f.lower())
                except: continue
        for tool in self.nested_dict.keys(): self._cache_commands.add(tool)
        self._cache_loaded = True

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        word_before = document.get_word_before_cursor()
        
        # 1. Nested Completions
        try:
            yield from self.nested_completer.get_completions(document, complete_event)
        except: pass

        # 2. Command Completions
        # Check if we are typing the first word (ignoring leading spaces)
        if " " not in text.strip():
            str_text = text.strip()
            builtins = self.get_builtins()
            
            # Special handling for /commands
            if str_text.startswith("/"):
                # Only show builtins starting with /
                for cmd in builtins:
                    if cmd.startswith(str_text):
                        yield Completion(cmd, start_position=-len(str_text))
                return # STRICT STOP: Do not fall through to system commands or paths

            # Normal commands (non-slash)
            for cmd in builtins:
                if cmd.startswith(str_text):
                    yield Completion(cmd, start_position=-len(str_text))
            
            cmds = list(self._cache_commands)
            for cmd in cmds:
                if cmd.startswith(str_text.lower()):
                    yield Completion(cmd, start_position=-len(str_text))

            # Path completion for ./ or / paths
            if str_text.startswith(".") or "/" in str_text or "\\" in str_text:
                yield from self.path_completer.get_completions(document, complete_event)

        # 3. Path Fallback (Arguments)
        else:
            first_word = text.split()[0]
            if first_word not in self.nested_dict:
                yield from self.path_completer.get_completions(document, complete_event)
