import os
import sys

def get_config_dir():
    """Returns the user configuration directory: ~/.config/PyBash"""
    home = os.path.expanduser("~")
    config_dir = os.path.join(home, ".config", "PyBash")
    
    if not os.path.exists(config_dir):
        try:
            os.makedirs(config_dir)
            os.makedirs(os.path.join(config_dir, "plugins"))
        except OSError:
            pass # Ignore if already exists race condition
            
    return config_dir

def get_settings_path():
    return os.path.join(get_config_dir(), "settings.json")

def get_history_path():
    return os.path.join(get_config_dir(), "history.txt")

def get_plugins_dir():
    return os.path.join(get_config_dir(), "plugins")
