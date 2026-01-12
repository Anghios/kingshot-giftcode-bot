# -*- coding: utf-8 -*-
"""
Modern GUI interface for Kingshot Gift Code Bot
Features: Dark theme, smooth animations, improved UX
"""

from __future__ import annotations

import queue
import threading
import time
import webbrowser
from tkinter import messagebox
from typing import Callable, List, Optional, Tuple
import tkinter as tk
from tkinter import ttk, scrolledtext

from config import (
    GUI_CONFIG, VERSION, APP_NAME, GITHUB_URL,
    PLAYER_ID_FILE, TIMEOUTS
)
from utils import (
    check_and_install_dependencies, install_packages,
    fetch_active_gift_codes, detect_available_browsers,
    get_preferred_browser, BrowserDetector
)
from bot_core import KingshotBotHeadless, RedeemResult


class ModernStyle:
    """Custom styling for modern dark theme"""

    @staticmethod
    def configure_styles():
        """Configure ttk styles for modern appearance"""
        style = ttk.Style()

        # Try to use clam theme as base (more customizable)
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass

        cfg = GUI_CONFIG

        # Main frame style
        style.configure(
            'Main.TFrame',
            background=cfg.bg_primary
        )

        # Card frame style
        style.configure(
            'Card.TFrame',
            background=cfg.bg_card,
            relief='flat'
        )

        # Label styles
        style.configure(
            'Title.TLabel',
            background=cfg.bg_primary,
            foreground=cfg.text_primary,
            font=(cfg.font_family, cfg.font_size_title, 'bold')
        )

        style.configure(
            'Subtitle.TLabel',
            background=cfg.bg_primary,
            foreground=cfg.text_secondary,
            font=(cfg.font_family, cfg.font_size_small)
        )

        style.configure(
            'Card.TLabel',
            background=cfg.bg_card,
            foreground=cfg.text_primary,
            font=(cfg.font_family, cfg.font_size_normal)
        )

        style.configure(
            'CardHeading.TLabel',
            background=cfg.bg_card,
            foreground=cfg.text_primary,
            font=(cfg.font_family, cfg.font_size_heading, 'bold')
        )

        style.configure(
            'Stats.TLabel',
            background=cfg.bg_card,
            foreground=cfg.text_secondary,
            font=(cfg.font_family, cfg.font_size_normal)
        )

        style.configure(
            'Success.TLabel',
            background=cfg.bg_card,
            foreground=cfg.accent_success,
            font=(cfg.font_family, cfg.font_size_normal, 'bold')
        )

        style.configure(
            'Warning.TLabel',
            background=cfg.bg_card,
            foreground=cfg.accent_warning,
            font=(cfg.font_family, cfg.font_size_normal, 'bold')
        )

        style.configure(
            'Error.TLabel',
            background=cfg.bg_card,
            foreground=cfg.accent_error,
            font=(cfg.font_family, cfg.font_size_normal, 'bold')
        )

        # LabelFrame style
        style.configure(
            'Card.TLabelframe',
            background=cfg.bg_card,
            foreground=cfg.text_primary,
            borderwidth=0
        )

        style.configure(
            'Card.TLabelframe.Label',
            background=cfg.bg_card,
            foreground=cfg.accent_secondary,
            font=(cfg.font_family, cfg.font_size_heading, 'bold')
        )

        # Button styles
        style.configure(
            'Primary.TButton',
            background=cfg.accent_primary,
            foreground=cfg.text_primary,
            font=(cfg.font_family, cfg.font_size_normal, 'bold'),
            padding=(20, 10),
            borderwidth=0
        )
        style.map('Primary.TButton',
            background=[('active', '#d1365a'), ('disabled', '#555555')],
            foreground=[('disabled', '#888888')]
        )

        style.configure(
            'Secondary.TButton',
            background=cfg.bg_tertiary,
            foreground=cfg.text_primary,
            font=(cfg.font_family, cfg.font_size_normal),
            padding=(20, 10),
            borderwidth=0
        )
        style.map('Secondary.TButton',
            background=[('active', '#1a4a7a'), ('disabled', '#333333')],
            foreground=[('disabled', '#666666')]
        )

        style.configure(
            'Accent.TButton',
            background=cfg.accent_secondary,
            foreground=cfg.text_primary,
            font=(cfg.font_family, cfg.font_size_normal, 'bold'),
            padding=(15, 8),
            borderwidth=0
        )
        style.map('Accent.TButton',
            background=[('active', '#0b8ac4')]
        )

        # Entry style
        style.configure(
            'Modern.TEntry',
            fieldbackground=cfg.bg_secondary,
            foreground=cfg.text_primary,
            insertcolor=cfg.text_primary,
            borderwidth=0,
            padding=10
        )

        # Combobox style
        style.configure(
            'Modern.TCombobox',
            fieldbackground=cfg.bg_secondary,
            background=cfg.bg_secondary,
            foreground=cfg.text_primary,
            arrowcolor=cfg.text_primary,
            borderwidth=0,
            padding=8
        )
        style.map('Modern.TCombobox',
            fieldbackground=[('readonly', cfg.bg_secondary)],
            selectbackground=[('readonly', cfg.accent_secondary)]
        )

        # Checkbutton style
        style.configure(
            'Modern.TCheckbutton',
            background=cfg.bg_card,
            foreground=cfg.text_primary,
            font=(cfg.font_family, cfg.font_size_normal)
        )
        style.map('Modern.TCheckbutton',
            background=[('active', cfg.bg_card)]
        )

        # Progressbar style
        style.configure(
            'Modern.Horizontal.TProgressbar',
            background=cfg.accent_primary,
            troughcolor=cfg.bg_secondary,
            borderwidth=0,
            thickness=8
        )

        # Separator
        style.configure(
            'Modern.TSeparator',
            background=cfg.bg_tertiary
        )


class AnimatedProgressBar(ttk.Progressbar):
    """Progress bar with smooth animation support"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._target_value = 0
        self._current_value = 0
        self._animating = False

    def set_value_animated(self, value: float, duration_ms: int = 300):
        """Animate to target value"""
        self._target_value = value

        if not self._animating:
            self._animating = True
            self._animate_step(duration_ms)

    def _animate_step(self, duration_ms: int):
        """Single animation step"""
        if abs(self._current_value - self._target_value) < 0.5:
            self._current_value = self._target_value
            self['value'] = self._current_value
            self._animating = False
            return

        # Ease-out animation
        diff = self._target_value - self._current_value
        step = diff * 0.2  # 20% of remaining distance

        self._current_value += step
        self['value'] = self._current_value

        self.after(GUI_CONFIG.progress_update_ms, lambda: self._animate_step(duration_ms))


class StatsPanel(ttk.Frame):
    """Panel showing redemption statistics with visual indicators"""

    def __init__(self, master, **kwargs):
        super().__init__(master, style='Card.TFrame', **kwargs)
        self._create_widgets()

    def _create_widgets(self):
        cfg = GUI_CONFIG

        # Create stat boxes
        self.stats_frame = ttk.Frame(self, style='Card.TFrame')
        self.stats_frame.pack(fill=tk.X, padx=10, pady=10)

        # Configure grid
        for i in range(4):
            self.stats_frame.columnconfigure(i, weight=1)

        # Success stat
        self.success_frame = self._create_stat_box(
            self.stats_frame, "Successful", "0", cfg.accent_success, 0
        )

        # Already claimed stat
        self.claimed_frame = self._create_stat_box(
            self.stats_frame, "Already Claimed", "0", cfg.accent_warning, 1
        )

        # Failed stat
        self.failed_frame = self._create_stat_box(
            self.stats_frame, "Failed", "0", cfg.accent_error, 2
        )

        # Total stat
        self.total_frame = self._create_stat_box(
            self.stats_frame, "Total", "0", cfg.accent_secondary, 3
        )

    def _create_stat_box(
        self,
        parent: ttk.Frame,
        label: str,
        value: str,
        color: str,
        column: int
    ) -> Tuple[ttk.Frame, tk.Label]:
        """Create a single stat box"""
        frame = ttk.Frame(parent, style='Card.TFrame')
        frame.grid(row=0, column=column, padx=5, sticky='nsew')

        # Value label (large number)
        value_label = tk.Label(
            frame,
            text=value,
            font=(GUI_CONFIG.font_family, 24, 'bold'),
            fg=color,
            bg=GUI_CONFIG.bg_card
        )
        value_label.pack()

        # Description label
        desc_label = tk.Label(
            frame,
            text=label,
            font=(GUI_CONFIG.font_family, GUI_CONFIG.font_size_small),
            fg=GUI_CONFIG.text_secondary,
            bg=GUI_CONFIG.bg_card
        )
        desc_label.pack()

        # Store reference to value label
        setattr(self, f'{label.lower().replace(" ", "_")}_value', value_label)

        return frame, value_label

    def update_stats(self, successful: int, already_claimed: int, failed: int, total: int):
        """Update all statistics"""
        self.successful_value.config(text=str(successful))
        self.already_claimed_value.config(text=str(already_claimed))
        self.failed_value.config(text=str(failed))
        self.total_value.config(text=str(total))


class LogPanel(ttk.Frame):
    """Styled log panel with colored output"""

    def __init__(self, master, **kwargs):
        super().__init__(master, style='Card.TFrame', **kwargs)
        self._create_widgets()

    def _create_widgets(self):
        cfg = GUI_CONFIG

        # Log text widget with custom styling
        self.log_text = tk.Text(
            self,
            wrap=tk.WORD,
            height=cfg.log_height,
            width=cfg.log_width,
            font=(cfg.font_family_mono, cfg.font_size_small),
            bg=cfg.bg_secondary,
            fg=cfg.text_primary,
            insertbackground=cfg.text_primary,
            selectbackground=cfg.accent_secondary,
            relief='flat',
            padx=10,
            pady=10,
            borderwidth=0
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Configure tags for colored output
        self.log_text.tag_config('info', foreground=cfg.accent_secondary)
        self.log_text.tag_config('success', foreground=cfg.accent_success)
        self.log_text.tag_config('error', foreground=cfg.accent_error)
        self.log_text.tag_config('warning', foreground=cfg.accent_warning)
        self.log_text.tag_config('header', foreground=cfg.text_primary, font=(cfg.font_family_mono, cfg.font_size_small, 'bold'))

        # Scrollbar
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def append(self, message: str, tag: str = 'info'):
        """Append a message to the log"""
        self.log_text.insert(tk.END, message + '\n', tag)
        self.log_text.see(tk.END)

    def clear(self):
        """Clear all log content"""
        self.log_text.delete(1.0, tk.END)


class KingshotBotGUI:
    """Modern graphical user interface for the Kingshot bot"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self._configure_window()

        self.bot: Optional[KingshotBotHeadless] = None
        self.bot_thread: Optional[threading.Thread] = None
        self.is_running = False
        self.log_queue: queue.Queue = queue.Queue()
        self.available_browsers: List[Tuple[str, str]] = []
        self.selected_browser: Optional[Tuple[str, str]] = None

        # Apply modern styling
        ModernStyle.configure_styles()

        # Check dependencies
        self._check_dependencies()

        # Detect browsers
        self._detect_browsers()

        # Build UI
        self._setup_ui()
        self._load_saved_player_id()
        self._process_log_queue()

    def _configure_window(self):
        """Configure main window properties"""
        cfg = GUI_CONFIG

        self.root.title(cfg.window_title)
        self.root.geometry(cfg.window_size)
        self.root.minsize(cfg.min_width, cfg.min_height)
        self.root.configure(bg=cfg.bg_primary)

        # Center window on screen
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'+{x}+{y}')

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

    def _check_dependencies(self):
        """Check and install missing dependencies"""
        missing = check_and_install_dependencies()

        if missing:
            response = messagebox.askyesno(
                "Missing Dependencies",
                f"The following packages are required:\n\n{', '.join(missing)}\n\n"
                f"Install them now?",
                icon='warning'
            )

            if response:
                self._show_install_dialog(missing)
            else:
                messagebox.showwarning(
                    "Cannot Continue",
                    f"Please install manually:\npip install {' '.join(missing)}"
                )
                self.root.quit()

    def _show_install_dialog(self, packages: List[str]):
        """Show installation progress dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Installing Packages")
        dialog.geometry("400x150")
        dialog.resizable(False, False)
        dialog.configure(bg=GUI_CONFIG.bg_primary)
        dialog.transient(self.root)
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 200
        y = (dialog.winfo_screenheight() // 2) - 75
        dialog.geometry(f'+{x}+{y}')

        # Content
        label = tk.Label(
            dialog,
            text=f"Installing packages...\n\n{', '.join(packages)}",
            font=(GUI_CONFIG.font_family, 11),
            fg=GUI_CONFIG.text_primary,
            bg=GUI_CONFIG.bg_primary,
            justify='center'
        )
        label.pack(expand=True, pady=20)

        progress = ttk.Progressbar(dialog, mode='indeterminate', length=300)
        progress.pack(pady=10)
        progress.start(10)

        def install_thread():
            success = install_packages(packages)
            dialog.after(0, lambda: on_complete(success))

        def on_complete(success: bool):
            progress.stop()
            dialog.destroy()

            if success:
                messagebox.showinfo(
                    "Success",
                    "Packages installed!\nPlease restart the application."
                )
                self.root.quit()
            else:
                messagebox.showerror(
                    "Error",
                    f"Installation failed.\nPlease run manually:\npip install {' '.join(packages)}"
                )
                self.root.quit()

        threading.Thread(target=install_thread, daemon=True).start()

    def _detect_browsers(self):
        """Detect available browsers"""
        self.available_browsers = detect_available_browsers()

        if not self.available_browsers:
            messagebox.showwarning(
                "No Browser Found",
                "No compatible browser detected!\n\n"
                "Please install one of:\n"
                "- Google Chrome (recommended)\n"
                "- Brave Browser\n"
                "- Microsoft Edge"
            )
        else:
            browser_name, browser_path = get_preferred_browser()
            self.selected_browser = (browser_name, browser_path)

    def _setup_ui(self):
        """Create all GUI elements with two-column layout"""
        cfg = GUI_CONFIG

        # Main container
        self.main_frame = ttk.Frame(self.root, style='Main.TFrame')
        self.main_frame.grid(row=0, column=0, sticky='nsew')
        self.main_frame.columnconfigure(0, weight=0)  # Left column (fixed)
        self.main_frame.columnconfigure(1, weight=1)  # Right column (expandable)
        self.main_frame.rowconfigure(0, weight=1)

        # Left panel (config, buttons, progress)
        self._create_left_panel()

        # Right panel (activity log)
        self._create_right_panel()

    def _create_left_panel(self):
        """Create left panel with config, buttons, and progress"""
        cfg = GUI_CONFIG

        # Left container
        left_frame = ttk.Frame(self.main_frame, style='Main.TFrame')
        left_frame.grid(row=0, column=0, sticky='nsew', padx=(cfg.padding_large, cfg.padding_small), pady=cfg.padding_large)
        left_frame.columnconfigure(0, weight=1)

        # Header section
        self._create_header(left_frame)

        # Configuration section
        self._create_config_section(left_frame)

        # Action buttons
        self._create_action_buttons(left_frame)

        # Progress section
        self._create_progress_section(left_frame)

    def _create_right_panel(self):
        """Create right panel with activity log"""
        cfg = GUI_CONFIG

        # Right container
        right_frame = ttk.Frame(self.main_frame, style='Main.TFrame')
        right_frame.grid(row=0, column=1, sticky='nsew', padx=(cfg.padding_small, cfg.padding_large), pady=cfg.padding_large)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)

        # Log section
        self._create_log_section(right_frame)

    def _create_header(self, parent):
        """Create header with title and subtitle"""
        cfg = GUI_CONFIG

        header_frame = ttk.Frame(parent, style='Main.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, cfg.padding_small))

        # App icon/logo placeholder and title
        title_frame = ttk.Frame(header_frame, style='Main.TFrame')
        title_frame.pack(fill=tk.X)

        # Title
        title_label = tk.Label(
            title_frame,
            text=f"  {APP_NAME}",
            font=(cfg.font_family, cfg.font_size_title, 'bold'),
            fg=cfg.text_primary,
            bg=cfg.bg_primary
        )
        title_label.pack(side=tk.LEFT)

        # Version badge
        version_label = tk.Label(
            title_frame,
            text=f" v{VERSION}",
            font=(cfg.font_family, cfg.font_size_small),
            fg=cfg.accent_secondary,
            bg=cfg.bg_primary
        )
        version_label.pack(side=tk.LEFT, padx=(5, 0))

        # Subtitle
        subtitle_label = tk.Label(
            header_frame,
            text="Automatically redeem gift codes for Kingshot",
            font=(cfg.font_family, cfg.font_size_small),
            fg=cfg.text_secondary,
            bg=cfg.bg_primary
        )
        subtitle_label.pack(anchor='w', padx=(3, 0))

    def _create_config_section(self, parent):
        """Create configuration panel"""
        cfg = GUI_CONFIG

        # Config card
        config_frame = tk.Frame(
            parent,
            bg=cfg.bg_card,
            highlightthickness=0
        )
        config_frame.pack(fill=tk.X, pady=cfg.padding_small)
        config_frame.columnconfigure(1, weight=1)

        # Section title
        title_label = tk.Label(
            config_frame,
            text="Configuration",
            font=(cfg.font_family, cfg.font_size_heading, 'bold'),
            fg=cfg.accent_secondary,
            bg=cfg.bg_card
        )
        title_label.grid(row=0, column=0, columnspan=3, sticky='w', padx=cfg.padding_medium, pady=(cfg.padding_medium, cfg.padding_small))

        # Player ID
        player_label = tk.Label(
            config_frame,
            text="Player ID:",
            font=(cfg.font_family, cfg.font_size_normal),
            fg=cfg.text_primary,
            bg=cfg.bg_card
        )
        player_label.grid(row=1, column=0, sticky='w', padx=cfg.padding_medium, pady=cfg.padding_tiny)

        self.player_id_entry = tk.Entry(
            config_frame,
            font=(cfg.font_family, cfg.font_size_normal),
            bg=cfg.bg_secondary,
            fg=cfg.text_primary,
            insertbackground=cfg.text_primary,
            relief='flat',
            width=cfg.entry_width
        )
        self.player_id_entry.grid(row=1, column=1, sticky='ew', padx=cfg.padding_small, pady=cfg.padding_tiny, ipady=8)

        # Browser selector
        browser_label = tk.Label(
            config_frame,
            text="Browser:",
            font=(cfg.font_family, cfg.font_size_normal),
            fg=cfg.text_primary,
            bg=cfg.bg_card
        )
        browser_label.grid(row=2, column=0, sticky='w', padx=cfg.padding_medium, pady=cfg.padding_tiny)

        self.browser_var = tk.StringVar()
        if self.selected_browser:
            self.browser_var.set(self.selected_browser[0])

        browser_names = [name for name, _ in self.available_browsers] if self.available_browsers else ['Chrome']
        self.browser_combo = ttk.Combobox(
            config_frame,
            textvariable=self.browser_var,
            values=browser_names,
            state='readonly',
            style='Modern.TCombobox',
            width=cfg.entry_width - 3
        )
        self.browser_combo.grid(row=2, column=1, sticky='ew', padx=cfg.padding_small, pady=cfg.padding_tiny)
        self.browser_combo.bind('<<ComboboxSelected>>', self._on_browser_change)

        # Headless mode checkbox
        self.headless_var = tk.BooleanVar(value=True)
        self.headless_check = tk.Checkbutton(
            config_frame,
            text=" Run in background (headless mode)",
            variable=self.headless_var,
            font=(cfg.font_family, cfg.font_size_normal),
            fg=cfg.text_primary,
            bg=cfg.bg_card,
            selectcolor=cfg.bg_secondary,
            activebackground=cfg.bg_card,
            activeforeground=cfg.text_primary
        )
        self.headless_check.grid(row=3, column=0, columnspan=2, sticky='w', padx=cfg.padding_medium, pady=(cfg.padding_tiny, cfg.padding_medium))

    def _create_action_buttons(self, parent):
        """Create action buttons panel"""
        cfg = GUI_CONFIG

        button_frame = ttk.Frame(parent, style='Main.TFrame')
        button_frame.pack(fill=tk.X, pady=cfg.padding_small)

        # Start button
        self.start_button = tk.Button(
            button_frame,
            text="  Start Bot",
            command=self._start_bot,
            font=(cfg.font_family, cfg.font_size_normal, 'bold'),
            bg=cfg.accent_success,
            fg=cfg.text_primary,
            activebackground='#0d9668',
            activeforeground=cfg.text_primary,
            relief='flat',
            cursor='hand2',
            width=cfg.button_width,
            pady=10
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, cfg.padding_small))

        # Stop button
        self.stop_button = tk.Button(
            button_frame,
            text="  Stop Bot",
            command=self._stop_bot,
            font=(cfg.font_family, cfg.font_size_normal, 'bold'),
            bg=cfg.accent_error,
            fg=cfg.text_primary,
            activebackground='#dc2626',
            activeforeground=cfg.text_primary,
            relief='flat',
            cursor='hand2',
            width=cfg.button_width,
            state='disabled',
            pady=10
        )
        self.stop_button.pack(side=tk.LEFT, padx=cfg.padding_small)

        # GitHub button
        self.github_button = tk.Button(
            button_frame,
            text="  GitHub",
            command=self._open_github,
            font=(cfg.font_family, cfg.font_size_normal),
            bg=cfg.bg_tertiary,
            fg=cfg.text_primary,
            activebackground='#1a4a7a',
            activeforeground=cfg.text_primary,
            relief='flat',
            cursor='hand2',
            width=cfg.button_width,
            pady=10
        )
        self.github_button.pack(side=tk.RIGHT)

    def _create_progress_section(self, parent):
        """Create progress and stats section"""
        cfg = GUI_CONFIG

        # Progress card
        progress_card = tk.Frame(
            parent,
            bg=cfg.bg_card,
            highlightthickness=0
        )
        progress_card.pack(fill=tk.X, pady=cfg.padding_small)

        # Section title
        title_label = tk.Label(
            progress_card,
            text="Progress",
            font=(cfg.font_family, cfg.font_size_heading, 'bold'),
            fg=cfg.accent_secondary,
            bg=cfg.bg_card
        )
        title_label.pack(anchor='w', padx=cfg.padding_medium, pady=(cfg.padding_medium, cfg.padding_small))

        # Status label
        self.progress_label = tk.Label(
            progress_card,
            text="Ready to start",
            font=(cfg.font_family, cfg.font_size_normal),
            fg=cfg.text_secondary,
            bg=cfg.bg_card
        )
        self.progress_label.pack(anchor='w', padx=cfg.padding_medium)

        # Progress bar
        self.progress_bar = AnimatedProgressBar(
            progress_card,
            style='Modern.Horizontal.TProgressbar',
            mode='determinate',
            length=400
        )
        self.progress_bar.pack(fill=tk.X, padx=cfg.padding_medium, pady=cfg.padding_small)

        # Stats panel
        self.stats_panel = StatsPanel(progress_card)
        self.stats_panel.pack(fill=tk.X, padx=cfg.padding_small, pady=(0, cfg.padding_medium))

    def _create_log_section(self, parent):
        """Create log output section"""
        cfg = GUI_CONFIG

        # Log card (fills the entire right panel)
        log_card = tk.Frame(
            parent,
            bg=cfg.bg_card,
            highlightthickness=0
        )
        log_card.pack(fill=tk.BOTH, expand=True)
        log_card.columnconfigure(0, weight=1)
        log_card.rowconfigure(1, weight=1)

        # Section title
        title_label = tk.Label(
            log_card,
            text="Activity Log",
            font=(cfg.font_family, cfg.font_size_heading, 'bold'),
            fg=cfg.accent_secondary,
            bg=cfg.bg_card
        )
        title_label.grid(row=0, column=0, sticky='w', padx=cfg.padding_medium, pady=(cfg.padding_medium, cfg.padding_small))

        # Log panel
        self.log_panel = LogPanel(log_card)
        self.log_panel.grid(row=1, column=0, sticky='nsew', padx=cfg.padding_small, pady=(0, cfg.padding_small))

    def _on_browser_change(self, event=None):
        """Handle browser selection change"""
        selected_name = self.browser_var.get()
        for name, path in self.available_browsers:
            if name == selected_name:
                self.selected_browser = (name, path)
                break

    def _open_github(self):
        """Open GitHub repository"""
        webbrowser.open(GITHUB_URL)

    def _load_saved_player_id(self):
        """Load saved Player ID from file"""
        try:
            with open(PLAYER_ID_FILE, 'r') as f:
                player_id = f.read().strip()
                if player_id:
                    self.player_id_entry.insert(0, player_id)
        except FileNotFoundError:
            pass

    def _save_player_id(self, player_id: str):
        """Save Player ID to file"""
        try:
            with open(PLAYER_ID_FILE, 'w') as f:
                f.write(player_id)
        except Exception as e:
            self._log(f"[!] Could not save Player ID: {str(e)}", 'warning')

    def _log(self, message: str, tag: str = 'info'):
        """Add message to log queue"""
        self.log_queue.put((message, tag))

    def _process_log_queue(self):
        """Process messages from log queue"""
        try:
            while True:
                message, tag = self.log_queue.get_nowait()
                self.log_panel.append(message, tag)
        except queue.Empty:
            pass
        finally:
            self.root.after(GUI_CONFIG.log_queue_check_ms, self._process_log_queue)

    def _start_bot(self):
        """Start bot in separate thread"""
        player_id = self.player_id_entry.get().strip()

        if not player_id:
            messagebox.showerror("Error", "Please enter a Player ID")
            return

        if self.is_running:
            messagebox.showwarning("Warning", "Bot is already running")
            return

        # Save Player ID
        self._save_player_id(player_id)

        # Update UI state
        self._set_ui_running_state(True)

        # Clear log and reset stats
        self.log_panel.clear()
        self.stats_panel.update_stats(0, 0, 0, 0)
        self.progress_bar['value'] = 0
        self.progress_label.config(text="Starting bot...")

        # Start bot thread
        self.is_running = True
        self.bot_thread = threading.Thread(target=self._run_bot, args=(player_id,), daemon=True)
        self.bot_thread.start()

    def _stop_bot(self):
        """Stop the bot"""
        if self.bot and self.is_running:
            self._log("[!] Stopping bot...", 'warning')
            self.is_running = False
            try:
                if self.bot:
                    self.bot.close()
            except:
                pass
            self._reset_ui()

    def _set_ui_running_state(self, running: bool):
        """Set UI to running or idle state"""
        state = 'disabled' if running else 'normal'
        stop_state = 'normal' if running else 'disabled'

        self.start_button.config(state=state)
        self.stop_button.config(state=stop_state)
        self.player_id_entry.config(state=state)
        self.headless_check.config(state=state)
        self.browser_combo.config(state='disabled' if running else 'readonly')

    def _reset_ui(self):
        """Reset UI to initial state"""
        self._set_ui_running_state(False)
        self.progress_label.config(text="Ready to start")
        self.is_running = False

    def _run_bot(self, player_id: str):
        """Run bot logic in background thread"""
        successful = 0
        already_claimed = 0
        failed = 0

        try:
            # Fetch codes
            self._log("[*] Fetching active gift codes...", 'info')
            codes = fetch_active_gift_codes()

            if not codes:
                self._log("[ERROR] Could not fetch active codes", 'error')
                messagebox.showerror(
                    "Error",
                    "Could not fetch active codes.\nCheck your connection or visit: https://kingshot.net/gift-codes"
                )
                self.root.after(0, self._reset_ui)
                return

            self._log(f"[+] Found {len(codes)} active codes:", 'success')
            for i, code in enumerate(codes, 1):
                self._log(f"    {i}. {code}", 'info')

            # Initialize bot
            headless = self.headless_var.get()
            browser_name, browser_path = self.selected_browser if self.selected_browser else (None, None)

            self._log(f"[*] Initializing bot (browser={browser_name}, headless={headless})...", 'info')

            self.bot = KingshotBotHeadless(
                player_id,
                headless=headless,
                log_callback=self._log_callback,
                browser_path=browser_path,
                browser_name=browser_name
            )

            if not self.is_running:
                self.bot.close()
                self.root.after(0, self._reset_ui)
                return

            # Login
            self._log("[*] Logging in...", 'info')
            if not self.bot.login():
                self._log("[ERROR] Login failed. Aborting.", 'error')
                messagebox.showerror("Error", "Login failed. Please check your Player ID.")
                self.bot.close()
                self.root.after(0, self._reset_ui)
                return

            # Redeem codes
            total_codes = len(codes)
            for i, code in enumerate(codes, 1):
                if not self.is_running:
                    break

                # Progress callback
                def progress_callback(step, total_steps, description):
                    code_base_progress = ((i - 1) / total_codes) * 100
                    step_progress = (step / total_steps) * (100 / total_codes)
                    overall_progress = code_base_progress + step_progress

                    self.root.after(0, lambda p=overall_progress, d=description:
                                   self._update_progress(p, f"Code {i}/{total_codes} ({code}): {d}"))

                # Redeem code
                result = self.bot.redeem_code(code, progress_callback=progress_callback)

                if result == RedeemResult.SUCCESS:
                    successful += 1
                elif result == RedeemResult.ALREADY_CLAIMED:
                    already_claimed += 1
                else:
                    failed += 1

                # Update stats
                self.root.after(0, lambda s=successful, a=already_claimed, f=failed:
                               self.stats_panel.update_stats(s, a, f, total_codes))

                if i < total_codes and self.is_running:
                    time.sleep(TIMEOUTS.between_codes)

            # Final summary
            self._log("\n" + "=" * 60, 'header')
            self._log("FINAL SUMMARY", 'header')
            self._log("=" * 60, 'header')
            self._log(f"[+] Successful: {successful}", 'success')
            self._log(f"[!] Already claimed: {already_claimed}", 'warning')
            self._log(f"[-] Failed: {failed}", 'error')
            self._log(f"[*] Total: {successful + already_claimed + failed}", 'info')
            self._log("=" * 60, 'header')

            if self.is_running:
                self._log("[+] Process completed!", 'success')
                messagebox.showinfo(
                    "Success",
                    f"Process completed!\n\n"
                    f"Successful: {successful}\n"
                    f"Already claimed: {already_claimed}\n"
                    f"Failed: {failed}"
                )

        except Exception as e:
            self._log(f"[ERROR] Unexpected error: {str(e)}", 'error')
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")

        finally:
            if self.bot:
                self.bot.close()
            self.root.after(0, self._reset_ui)

    def _log_callback(self, message: str):
        """Callback for bot logs"""
        tag = 'info'
        if message.startswith('[+]'):
            tag = 'success'
        elif message.startswith('[ERROR]'):
            tag = 'error'
        elif message.startswith('[!]'):
            tag = 'warning'

        self._log(message, tag)

    def _update_progress(self, value: float, text: str):
        """Update progress bar and label"""
        self.progress_bar.set_value_animated(value)
        self.progress_label.config(text=text)
