# 🔌 PyBash Plugin API

## Creating a Plugin

Place a `.py` file in `plugins/`.

```python
def my_cmd(args):
    print("Hello from plugin!")

def setup(shell):
    # Register command
    shell.register_command("mycmd", my_cmd)
    
    # Register setting (Automatically grouped under Plugins tab)
    shell.register_setting(
        tab="MyPlugin",
        group="General",
        key="my_setting",
        default=True,
        value_type=bool,
        description="A plugin setting"
    )
```

## Developer Mode
To see plugin loading logs and debug information, enable **General > Behavior > show_dev_logs** in `/settings`.
