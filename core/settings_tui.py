from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import Window, HSplit, VSplit
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.styles import Style
from prompt_toolkit.filters import Condition

try:
    from prompt_toolkit.layout.containers import WindowAlign
except ImportError:
    class WindowAlign:
        CENTER = "CENTER"
        LEFT = "LEFT"
        RIGHT = "RIGHT"

class SettingsTUI:
    def __init__(self, settings_manager):
        self.settings = settings_manager
        self.structure = self.settings.get_structure()
        
        self.tabs = sorted([t for t in self.structure.keys() if t != "Plugins"])
        if "Plugins" in self.structure:
            self.tabs.append("Plugins")

        self.current_tab_idx = 0
        self.current_subtab_idx = 0
        self.current_group_idx = 0
        self.current_setting_idx = 0
        self.focus_area = 'tabs' 
        self.is_dirty = False
        self._temp_settings = {}

    def get_current_tab(self):
        return self.tabs[self.current_tab_idx]

    def get_subtabs(self):
        return sorted(list(self.structure[self.get_current_tab()].keys()))

    def get_current_subtab(self):
        subs = self.get_subtabs()
        return subs[self.current_subtab_idx] if subs else ""

    def get_groups(self):
        tab = self.get_current_tab()
        sub = self.get_current_subtab()
        return sorted(list(self.structure[tab][sub].keys()))

    def get_current_group(self):
        groups = self.get_groups()
        return groups[self.current_group_idx] if groups else None

    def get_settings(self):
        tab = self.get_current_tab()
        sub = self.get_current_subtab()
        group = self.get_current_group()
        if not group: return []
        return list(self.structure[tab][sub][group].items())

    def run(self):
        kb = KeyBindings()

        @kb.add('q')
        def _(event):
            if self.is_dirty: self.focus_area = "exit_prompt"
            else: event.app.exit()

        @kb.add('c-x')
        def _(event): event.app.exit()

        @kb.add('c-s')
        def _(event):
            for k, v in self._temp_settings.items():
                self.settings.set(k, v, save=False)
            self.settings.save()
            self.is_dirty = False
            self._temp_settings = {}

        @kb.add('right')
        @kb.add('tab')
        def _(event):
            if self.focus_area == 'tabs':
                subs = self.get_subtabs()
                if len(subs) == 1 and subs[0] == "":
                    self.focus_area = 'groups'
                    self.current_group_idx = 0
                else:
                    self.focus_area = 'subtabs'
                    self.current_subtab_idx = 0
            elif self.focus_area == 'subtabs':
                self.focus_area = 'groups'
                self.current_group_idx = 0
            elif self.focus_area == 'groups':
                self.focus_area = 'settings'
                self.current_setting_idx = 0

        @kb.add('left')
        @kb.add('s-tab')
        def _(event):
            if self.focus_area == 'settings': self.focus_area = 'groups'
            elif self.focus_area == 'groups':
                subs = self.get_subtabs()
                if len(subs) == 1 and subs[0] == "": self.focus_area = 'tabs'
                else: self.focus_area = 'subtabs'
            elif self.focus_area == 'subtabs': self.focus_area = 'tabs'

        @kb.add('up')
        def _(event):
            if self.focus_area == 'tabs':
                self.current_tab_idx = (self.current_tab_idx - 1) % len(self.tabs)
                self.current_subtab_idx = 0; self.current_group_idx = 0
            elif self.focus_area == 'subtabs':
                subs = self.get_subtabs()
                self.current_subtab_idx = (self.current_subtab_idx - 1) % len(subs)
                self.current_group_idx = 0
            elif self.focus_area == 'groups':
                groups = self.get_groups()
                self.current_group_idx = (self.current_group_idx - 1) % len(groups)
            elif self.focus_area == 'settings':
                settings = self.get_settings()
                if settings: self.current_setting_idx = (self.current_setting_idx - 1) % len(settings)

        @kb.add('down')
        def _(event):
            if self.focus_area == 'tabs':
                self.current_tab_idx = (self.current_tab_idx + 1) % len(self.tabs)
                self.current_subtab_idx = 0; self.current_group_idx = 0
            elif self.focus_area == 'subtabs':
                subs = self.get_subtabs()
                self.current_subtab_idx = (self.current_subtab_idx + 1) % len(subs)
                self.current_group_idx = 0
            elif self.focus_area == 'groups':
                groups = self.get_groups()
                self.current_group_idx = (self.current_group_idx + 1) % len(groups)
            elif self.focus_area == 'settings':
                settings = self.get_settings()
                if settings: self.current_setting_idx = (self.current_setting_idx + 1) % len(settings)

        @kb.add('enter')
        def _(event):
            if self.focus_area == 'settings':
                settings = self.get_settings()
                if not settings: return
                key, info = settings[self.current_setting_idx]
                val = self._temp_settings.get(key, info['value'])
                options = info.get('options')

                if info['type'] == 'bool':
                    self._temp_settings[key] = not val
                    self.is_dirty = True
                elif options:
                    # Cycle through options
                    try:
                        curr_idx = options.index(val)
                        new_idx = (curr_idx + 1) % len(options)
                        self._temp_settings[key] = options[new_idx]
                        self.is_dirty = True
                    except ValueError:
                        # Value not in options, reset to first
                        self._temp_settings[key] = options[0]
                        self.is_dirty = True
                else:
                    self.focus_area = "editing"
                    self._edit_key = key
                    self._edit_buffer = str(val)

        @kb.add('y', filter=Condition(lambda: self.focus_area == "exit_prompt"))
        def _(event):
            for k, v in self._temp_settings.items(): self.settings.set(k, v, save=False)
            self.settings.save()
            event.app.exit()

        @kb.add('n', filter=Condition(lambda: self.focus_area == "exit_prompt"))
        def _(event): event.app.exit()

        @kb.add('escape', filter=Condition(lambda: self.focus_area == "exit_prompt"))
        def _(event): self.focus_area = "tabs"

        @kb.add('<any>', filter=Condition(lambda: self.focus_area == "editing"))
        def _(event): self._edit_buffer += event.data

        @kb.add('backspace', filter=Condition(lambda: self.focus_area == "editing"))
        def _(event): self._edit_buffer = self._edit_buffer[:-1]

        @kb.add('enter', filter=Condition(lambda: self.focus_area == "editing"))
        def _(event):
            self._temp_settings[self._edit_key] = self._edit_buffer
            self.is_dirty = True
            self.focus_area = "settings"

        @kb.add('escape', filter=Condition(lambda: self.focus_area == "editing"))
        def _(event): self.focus_area = "settings"

        def get_sidebar_text():
            result = []
            for i, tab in enumerate(self.tabs):
                is_tab_selected = (i == self.current_tab_idx)
                style = "class:tab.active" if is_tab_selected and self.focus_area == 'tabs' else "class:tab.selected" if is_tab_selected else "class:tab"
                prefix = "▼ " if is_tab_selected else "▶ "
                result.append((style, f"{prefix}{tab}\n"))
                
                if is_tab_selected:
                    subs = self.get_subtabs()
                    for j, sub in enumerate(subs):
                        if sub == "": 
                            groups = self.get_groups()
                            for k, group in enumerate(groups):
                                g_selected = (k == self.current_group_idx)
                                g_style = "class:group.active" if g_selected and self.focus_area in ('groups', 'settings') else "class:group.selected" if g_selected else "class:group"
                                result.append((g_style, f"    {group}\n"))
                        else:
                            s_selected = (j == self.current_subtab_idx)
                            s_style = "class:subtab.active" if s_selected and self.focus_area == 'subtabs' else "class:subtab.selected" if s_selected else "class:subtab"
                            s_prefix = "  ▼ " if s_selected else "  ▶ "
                            result.append((s_style, f"{s_prefix}{sub}\n"))
                            if s_selected:
                                groups = self.get_groups()
                                for k, group in enumerate(groups):
                                    g_selected = (k == self.current_group_idx)
                                    g_style = "class:group.active" if g_selected and self.focus_area in ('groups', 'settings') else "class:group.selected" if g_selected else "class:group"
                                    result.append((g_style, f"      {group}\n"))
            return result

        def get_main_text():
            if self.focus_area == "editing":
                return [("class:header_small", f"\n  Editing {self._edit_key}\n\n"), ("class:text", "  Enter new value: "), ("class:edit_buffer", f"{self._edit_buffer}_"), ("\n\n  [Enter] Confirm  [Esc] Cancel", "")]
            settings = self.get_settings()
            if not settings: return [("class:text", "\n  No settings available.")]
            
            path_str = f"{self.get_current_tab()}"
            if self.get_current_subtab(): path_str += f" > {self.get_current_subtab()}"
            path_str += f" > {self.get_current_group()}"

            result = [("class:header_small", f"\n  {path_str}\n\n")]
            for i, (key, info) in enumerate(settings):
                prefix = " >" if i == self.current_setting_idx and self.focus_area == 'settings' else "  "
                style = "class:setting.active" if i == self.current_setting_idx and self.focus_area == 'settings' else "class:setting"
                
                val = self._temp_settings.get(key, info['value'])
                val_str = str(val)
                if info['type'] == 'bool':
                    val_str = "ON" if val else "OFF"
                    val_color = "class:value.bool.true" if val else "class:value.bool.false"
                else: val_color = "class:value.text"
                
                # Show available options if any
                options_hint = ""
                if info.get('options'):
                    options_hint = f" [{', '.join(info['options'])}]"

                result.append((style, f"{prefix} {key:<20} "))
                result.append(("", " : "))
                result.append((val_color, f"{val_str}"))
                result.append(("", f"{options_hint}"))
                result.append(("", f"\n    # {info['description']}\n"))
            return result

        def get_footer_text():
            if self.focus_area == "exit_prompt": return " Unsaved changes! Save? [y] Yes  [n] No, discard  [Esc] Return"
            dirty = "*" if self.is_dirty else ""
            return f" {dirty} PyBash TUI | Ctrl+S: Save | Ctrl+X: Exit | q: Quit | Arrows/Tab: Nav | Enter: Edit/Toggle"

        sidebar = Window(content=FormattedTextControl(get_sidebar_text), width=35, style="class:sidebar")
        main = Window(content=FormattedTextControl(get_main_text), style="class:content")
        root = HSplit([
            Window(height=1, content=FormattedTextControl(" PyBash Nested Settings "), style="class:header", align=WindowAlign.CENTER),
            VSplit([sidebar, Window(width=1, char='│', style="class:border"), main]),
            Window(height=1, content=FormattedTextControl(get_footer_text), style="class:footer")
        ])

        style = Style.from_dict({
            "header": "bg:#00aaaa #ffffff bold", "footer": "bg:#333333 #ffffff",
            "sidebar": "bg:#1e1e1e #888888", "content": "bg:#000000 #ffffff", "border": "#444444",
            "tab.active": "#00ffff bold bg:#333333", "tab.selected": "#ffffff bold",
            "subtab.active": "#00aa00 bold bg:#222222", "subtab.selected": "#00aa00 bold",
            "group.active": "#ffff00 bold bg:#333333", "setting.active": "bg:#222222 #ffffff",
            "value.bool.true": "#00ff00", "value.bool.false": "#ff0000", "value.text": "#00aaff",
            "header_small": "#00aaaa bold underline", "edit_buffer": "bg:#333333 #ffffff bold",
        })

        app = Application(layout=Layout(root), key_bindings=kb, style=style, full_screen=True)
        app.run()
