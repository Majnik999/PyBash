import json
import os
import shutil
from collections import defaultdict
from datetime import datetime
from core.utils import get_settings_path

class SettingsManager:
    def __init__(self):
        self.file_path = get_settings_path()
        self.registry = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        self._flat_cache = {} 
        self._is_plugin_registering = False
        
        self._register_defaults()

    def _register_defaults(self):
        # Behavior
        self.register("General", "", "Behavior", "history_limit", 1000, int, "Max history entries")
        self.register("General", "", "Behavior", "show_welcome", True, bool, "Show welcome message")
        self.register("General", "", "Behavior", "show_dev_logs", False, bool, "Show developer/plugin logs on startup")
        self.register("General", "", "Behavior", "use_slash_paths", True, bool, "Force / instead of \\ on Windows")
        self.register("General", "", "Behavior", "autocomplete_mode", "ghost", str, "Autocomplete Style", options=["ghost", "menu"])
        
        # Appearance - Layout
        self.register("General", "", "Appearance", "prompt_layout", "two_line", str, "Prompt Layout", options=["two_line", "one_line"])
        self.register("General", "", "Appearance", "welcome_message", "Welcome back, {user}!", str, "Custom welcome text")
        
        # Appearance - Colors
        self.register("General", "", "Appearance", "prompt_path_color", "ansicyan", str, "Path Color")
        self.register("General", "", "Appearance", "prompt_git_color", "ansimagenta", str, "Git Color")
        self.register("General", "", "Appearance", "prompt_venv_color", "ansiyellow", str, "Venv Color")
        self.register("General", "", "Appearance", "prompt_user_color", "ansigreen", str, "User Color")
        self.register("General", "", "Appearance", "prompt_connector_color", "ansiwhite", str, "Line/Connector Color")
        self.register("General", "", "Appearance", "prompt_char_color", "ansiwhite", str, "Input Symbol ($) Color")
        self.register("General", "", "Appearance", "prompt_time_color", "#888888", str, "Time Color")
        
        # Internal
        self.register("Internal", "", "Tracking", "last_run", "Never", str, "Internal last run timestamp")

    def set_plugin_mode(self, mode: bool):
        self._is_plugin_registering = mode

    def register(self, tab, subtab, group, key, default, value_type=str, description="", options=None):
        actual_tab = "Plugins" if self._is_plugin_registering else tab
        actual_subtab = tab if self._is_plugin_registering else subtab

        if key not in self.registry[actual_tab][actual_subtab][group]:
            self.registry[actual_tab][actual_subtab][group][key] = {
                "value": default, "default": default, "type": value_type.__name__, "description": description, "options": options
            }
            self._flat_cache[key] = (actual_tab, actual_subtab, group)

    def load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r") as f:
                    data = json.load(f)
                    for key, val in data.items(): self.set(key, val, save=False)
            except Exception as e: 
                print(f"Error loading settings: {e}")
                self._restore_backup()

    def _restore_backup(self):
        bak = self.file_path + ".bak"
        if os.path.exists(bak):
            try: shutil.copy(bak, self.file_path); self.load()
            except: pass

    def save(self):
        if os.path.exists(self.file_path):
            try: shutil.copy(self.file_path, self.file_path + ".bak")
            except: pass
        flat_data = {}
        for tab in self.registry:
            for sub in self.registry[tab]:
                for group in self.registry[tab][sub]:
                    for key, info in self.registry[tab][sub][group].items():
                        flat_data[key] = info["value"]
        try:
            with open(self.file_path, "w") as f: json.dump(flat_data, f, indent=4)
        except: self._restore_backup()

    def get(self, key):
        if key in self._flat_cache:
            tab, sub, group = self._flat_cache[key]
            return self.registry[tab][sub][group][key]["value"]
        return None

    def get_options(self, key):
        if key in self._flat_cache:
            tab, sub, group = self._flat_cache[key]
            return self.registry[tab][sub][group][key].get("options")
        return None

    def set(self, key, value, save=True):
        if key in self._flat_cache:
            tab, sub, group = self._flat_cache[key]
            options = self.registry[tab][sub][group][key].get("options")
            if options and value not in options: return False
            target_type_name = self.registry[tab][sub][group][key]["type"]
            try:
                if target_type_name == "int": value = int(value)
                elif target_type_name == "bool":
                    if isinstance(value, str): value = value.lower() in ("true", "yes", "1")
                    else: value = bool(value)
                elif target_type_name == "str": value = str(value)
            except: pass 
            self.registry[tab][sub][group][key]["value"] = value
            if save: self.save()
        return True

    def get_structure(self):
        return {k: v for k, v in self.registry.items() if k != "Internal"}
