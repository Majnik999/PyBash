def hello_command(args):
    name = args[0] if args else "World"
    print(f"Hello, {name}! This is a custom command from a plugin.")

def setup(shell):
    """
    Standard setup function for PyBash plugins.
    'shell' is the PyBashShell instance.
    """
    # Register a custom command
    shell.register_command("hello", hello_command)

    # Register custom settings using the new API
    # Params: tab, group, key, default, type, description
    shell.register_setting(
        "Example Plugin", 
        "General", 
        "use_custom_greeting", 
        True, 
        bool, 
        "Whether to use custom greeting"
    )
    
    shell.register_setting(
        "Example Plugin", 
        "General", 
        "greeting_name", 
        "Developer", 
        str, 
        "Name to use for greetings"
    )
    
    # Nested-like structure using Tab names
    shell.register_setting(
        "Theme", 
        "Colors", 
        "my_plugin_primary_color", 
        "CYAN", 
        str, 
        "Primary color for example plugin"
    )
