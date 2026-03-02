import os
import importlib.util
import sys
import shutil
from core.utils import get_plugins_dir

class PluginManager:
    def __init__(self, shell):
        self.shell = shell
        self.plugin_dir = get_plugins_dir()
        self.plugins = []
        
        # Ensure example plugin exists in user dir for reference
        self._ensure_example()

    def _ensure_example(self):
        example_path = os.path.join(self.plugin_dir, "example.py")
        if not os.path.exists(example_path):
            try:
                # Basic example content
                content = '''def my_command(args):
    print("Hello from your custom plugin!")

def setup(shell):
    shell.register_command("mycmd", my_command)
'''
                with open(example_path, "w") as f:
                    f.write(content)
            except: pass

    def dev_log(self, message):
        if self.shell.settings.get("show_dev_logs"):
            from prompt_toolkit import print_formatted_text
            from prompt_toolkit.formatted_text import HTML
            print_formatted_text(HTML(f"<style fg='#666666'>[DEV] {message}</style>"))

    def load_plugins(self):
        if not os.path.exists(self.plugin_dir):
            return

        for filename in os.listdir(self.plugin_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                path = os.path.join(self.plugin_dir, filename)
                self.load_plugin(path)

    def load_plugin(self, path):
        module_name = os.path.basename(path)[:-3]
        try:
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                
                if hasattr(module, "setup"):
                    module.setup(self.shell)
                    self.plugins.append(module)
                    self.dev_log(f"Loaded plugin: {module_name}")
        except Exception as e:
            self.dev_log(f"Failed to load plugin {module_name}: {e}")
