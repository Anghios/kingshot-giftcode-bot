# -*- coding: utf-8 -*-
"""
GUI interface for Kingshot Bot using Tkinter
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import time
import webbrowser

from utils import (check_and_install_dependencies, install_packages,
                   fetch_active_gift_codes, detect_available_browsers,
                   get_preferred_browser)
from bot_core import KingshotBotHeadless


class KingshotBotGUI:
    """Graphical user interface for the Kingshot bot"""

    def __init__(self, root):
        self.root = root
        self.root.title("Kingshot Gift Code Bot")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        self.bot = None
        self.bot_thread = None
        self.is_running = False
        self.log_queue = queue.Queue()
        self.available_browsers = []
        self.selected_browser = None

        # Check dependencies before setting up UI
        self.check_dependencies()

        # Detect available browsers
        self.detect_browsers()

        self.setup_ui()
        self.load_saved_player_id()
        self.process_log_queue()

    def detect_browsers(self):
        """Detect available Chromium-based browsers"""
        self.available_browsers = detect_available_browsers()

        if not self.available_browsers:
            messagebox.showwarning(
                "No Browser Found",
                "No compatible browser detected!\n\n"
                "Please install one of:\n"
                "- Google Chrome\n"
                "- Brave Browser\n"
                "- Microsoft Edge"
            )
        else:
            # Select preferred browser by default
            browser_name, browser_path = get_preferred_browser()
            self.selected_browser = (browser_name, browser_path)

    def check_dependencies(self):
        """Check and install missing dependencies"""
        missing = check_and_install_dependencies()
        if missing:
            response = messagebox.askyesno(
                "Missing Dependencies",
                f"The following packages are missing:\n\n{', '.join(missing)}\n\n"
                f"Would you like to install them now?\n\n"
                f"This will run: pip install {' '.join(missing)}",
                icon='warning'
            )

            if response:
                # Show installing message
                install_window = tk.Toplevel(self.root)
                install_window.title("Installing Packages")
                install_window.geometry("400x150")
                install_window.resizable(False, False)

                # Center the window
                install_window.transient(self.root)
                install_window.grab_set()

                label = ttk.Label(install_window,
                                 text=f"Installing packages...\n\n{', '.join(missing)}\n\nPlease wait...",
                                 justify='center',
                                 font=('Arial', 10))
                label.pack(expand=True, pady=20)

                progress = ttk.Progressbar(install_window, mode='indeterminate', length=300)
                progress.pack(pady=10)
                progress.start(10)

                # Install in thread to avoid freezing
                def install_thread():
                    success = install_packages(missing)
                    install_window.after(0, lambda: on_install_complete(success))

                def on_install_complete(success):
                    progress.stop()
                    install_window.destroy()

                    if success:
                        messagebox.showinfo(
                            "Success",
                            "Packages installed successfully!\n\n"
                            "Please restart the application for changes to take effect."
                        )
                        self.root.quit()
                    else:
                        messagebox.showerror(
                            "Error",
                            "Failed to install packages.\n\n"
                            "Please run manually:\n"
                            f"pip install {' '.join(missing)}"
                        )
                        self.root.quit()

                threading.Thread(target=install_thread, daemon=True).start()
            else:
                messagebox.showwarning(
                    "Cannot Continue",
                    "The application requires these packages to work.\n\n"
                    f"Please install them manually:\npip install {' '.join(missing)}"
                )
                self.root.quit()

    def setup_ui(self):
        """Create all GUI elements"""
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights for resizing
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)

        # Title
        title_label = ttk.Label(main_frame, text="Kingshot Gift Code Bot",
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))

        # Player ID section
        player_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        player_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        player_frame.columnconfigure(1, weight=1)

        ttk.Label(player_frame, text="Player ID:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.player_id_entry = ttk.Entry(player_frame, width=30)
        self.player_id_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)

        # Browser selector
        ttk.Label(player_frame, text="Browser:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))

        self.browser_var = tk.StringVar()
        if self.selected_browser:
            self.browser_var.set(self.selected_browser[0])

        browser_names = [name for name, _ in self.available_browsers] if self.available_browsers else ['Chrome']
        self.browser_combo = ttk.Combobox(player_frame, textvariable=self.browser_var,
                                          values=browser_names, state='readonly', width=28)
        self.browser_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        self.browser_combo.bind('<<ComboboxSelected>>', self.on_browser_change)

        # Headless mode checkbox
        self.headless_var = tk.BooleanVar(value=True)
        self.headless_check = ttk.Checkbutton(player_frame, text="Headless mode (invisible browser)",
                                             variable=self.headless_var)
        self.headless_check.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)

        self.start_button = ttk.Button(button_frame, text="Start Bot",
                                       command=self.start_bot, width=15)
        self.start_button.grid(row=0, column=0, padx=5)

        self.stop_button = ttk.Button(button_frame, text="Stop Bot",
                                      command=self.stop_bot, width=15, state='disabled')
        self.stop_button.grid(row=0, column=1, padx=5)

        self.github_button = ttk.Button(button_frame, text="⭐ GitHub",
                                       command=self.open_github, width=15)
        self.github_button.grid(row=0, column=2, padx=5)

        # Progress section
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)

        self.progress_label = ttk.Label(progress_frame, text="Ready to start")
        self.progress_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=300)
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))

        # Stats frame
        stats_frame = ttk.Frame(progress_frame)
        stats_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))

        self.stats_label = ttk.Label(stats_frame, text="Successful: 0 | Already claimed: 0 | Failed: 0 | Total: 0")
        self.stats_label.grid(row=0, column=0, sticky=tk.W)

        # Log section
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="10")
        log_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD,
                                                  height=15, width=80,
                                                  font=('Consolas', 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure text tags for colored output
        self.log_text.tag_config('info', foreground='blue')
        self.log_text.tag_config('success', foreground='green')
        self.log_text.tag_config('error', foreground='red')
        self.log_text.tag_config('warning', foreground='orange')

    def on_browser_change(self, event=None):
        """Handle browser selection change"""
        selected_name = self.browser_var.get()
        for name, path in self.available_browsers:
            if name == selected_name:
                self.selected_browser = (name, path)
                break

    def open_github(self):
        """Open GitHub repository in browser"""
        webbrowser.open("https://github.com/Anghios/kingshot-giftcode-bot")

    def load_saved_player_id(self):
        """Load Player ID from login_id.txt if exists"""
        try:
            with open('login_id.txt', 'r') as f:
                player_id = f.read().strip()
                if player_id:
                    self.player_id_entry.insert(0, player_id)
        except FileNotFoundError:
            pass

    def save_player_id(self, player_id):
        """Save Player ID to login_id.txt"""
        try:
            with open('login_id.txt', 'w') as f:
                f.write(player_id)
        except Exception as e:
            self.log(f"[!] Could not save Player ID: {str(e)}", 'warning')

    def log(self, message, tag='info'):
        """Add message to log queue"""
        self.log_queue.put((message, tag))

    def process_log_queue(self):
        """Process messages from log queue"""
        try:
            while True:
                message, tag = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, message + '\n', tag)
                self.log_text.see(tk.END)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_log_queue)

    def start_bot(self):
        """Start bot in separate thread"""
        player_id = self.player_id_entry.get().strip()

        if not player_id:
            messagebox.showerror("Error", "Please enter a Player ID")
            return

        if self.is_running:
            messagebox.showwarning("Warning", "Bot is already running")
            return

        # Save Player ID
        self.save_player_id(player_id)

        # Disable start button, enable stop button
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.player_id_entry.config(state='disabled')
        self.headless_check.config(state='disabled')
        self.browser_combo.config(state='disabled')

        # Clear log
        self.log_text.delete(1.0, tk.END)

        # Reset progress
        self.progress_bar['value'] = 0
        self.progress_label.config(text="Starting bot...")

        # Start bot thread
        self.is_running = True
        self.bot_thread = threading.Thread(target=self.run_bot, args=(player_id,), daemon=True)
        self.bot_thread.start()

    def stop_bot(self):
        """Stop the bot"""
        if self.bot and self.is_running:
            self.log("[!] Stopping bot...", 'warning')
            self.is_running = False
            try:
                if self.bot:
                    self.bot.close()
            except:
                pass
            self.reset_ui()

    def reset_ui(self):
        """Reset UI to initial state"""
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.player_id_entry.config(state='normal')
        self.headless_check.config(state='normal')
        self.browser_combo.config(state='readonly')
        self.progress_label.config(text="Ready to start")
        self.is_running = False

    def run_bot(self, player_id):
        """Run bot logic in background thread"""
        successful = 0
        already_claimed = 0
        failed = 0

        try:
            # Fetch codes
            self.log("[*] Fetching active gift codes...", 'info')
            codes = fetch_active_gift_codes()

            if not codes:
                self.log("[ERROR] Could not fetch active codes", 'error')
                messagebox.showerror("Error", "Could not fetch active codes.\nCheck your connection or visit: https://kingshot.net/gift-codes")
                self.reset_ui()
                return

            self.log(f"[+] Found {len(codes)} active codes:", 'success')
            for i, code in enumerate(codes, 1):
                self.log(f"    {i}. {code}", 'info')

            # Initialize bot
            headless = self.headless_var.get()
            browser_name, browser_path = self.selected_browser if self.selected_browser else (None, None)

            self.log(f"[*] Initializing bot (browser={browser_name}, headless={headless})...", 'info')

            self.bot = KingshotBotHeadless(player_id, headless=headless,
                                          log_callback=self.log_callback,
                                          browser_path=browser_path,
                                          browser_name=browser_name)

            if not self.is_running:
                self.bot.close()
                self.reset_ui()
                return

            # Login
            self.log("[*] Logging in...", 'info')
            if not self.bot.login():
                self.log("[ERROR] Login failed. Aborting.", 'error')
                messagebox.showerror("Error", "Login failed. Please check your Player ID.")
                self.bot.close()
                self.reset_ui()
                return

            # Redeem codes
            total_codes = len(codes)
            for i, code in enumerate(codes, 1):
                if not self.is_running:
                    break

                # Create progress callback for this code
                def progress_callback(step, total_steps, description):
                    # Calculate overall progress: code progress + step progress within code
                    code_base_progress = ((i - 1) / total_codes) * 100
                    step_progress = (step / total_steps) * (100 / total_codes)
                    overall_progress = code_base_progress + step_progress

                    self.root.after(0, lambda p=overall_progress, d=description, idx=i, tot=total_codes, c=code:
                                   self.update_progress(p, f"Code {idx}/{tot} ({c}): {d}"))

                # Redeem code with progress callback
                result = self.bot.redeem_code(code, progress_callback=progress_callback)
                if result == 'success':
                    successful += 1
                elif result == 'already_claimed':
                    already_claimed += 1
                else:  # 'failed'
                    failed += 1

                # Update stats
                self.root.after(0, lambda s=successful, a=already_claimed, f=failed:
                               self.update_stats(s, a, f, total_codes))

                if i < total_codes and self.is_running:
                    time.sleep(3)

            # Final summary
            self.log("\n" + "="*60, 'info')
            self.log("FINAL SUMMARY", 'info')
            self.log("="*60, 'info')
            self.log(f"[+] Successful: {successful}", 'success')
            self.log(f"[!] Already claimed: {already_claimed}", 'warning')
            self.log(f"[-] Failed: {failed}", 'error')
            self.log(f"[*] Total: {successful + already_claimed + failed}", 'info')
            self.log("="*60, 'info')

            if self.is_running:
                self.log("[+] Process completed!", 'success')
                messagebox.showinfo("Success",
                                   f"Process completed!\n\nSuccessful: {successful}\nAlready claimed: {already_claimed}\nFailed: {failed}")

        except Exception as e:
            self.log(f"[ERROR] Unexpected error: {str(e)}", 'error')
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")

        finally:
            if self.bot:
                self.bot.close()
            self.root.after(0, self.reset_ui)

    def log_callback(self, message):
        """Callback for bot logs"""
        # Determine tag based on message prefix
        tag = 'info'
        if message.startswith('[+]'):
            tag = 'success'
        elif message.startswith('[ERROR]'):
            tag = 'error'
        elif message.startswith('[!]'):
            tag = 'warning'

        self.log(message, tag)

    def update_progress(self, value, text):
        """Update progress bar and label"""
        self.progress_bar['value'] = value
        self.progress_label.config(text=text)

    def update_stats(self, successful, already_claimed, failed, total):
        """Update statistics label"""
        self.stats_label.config(text=f"Successful: {successful} | Already claimed: {already_claimed} | Failed: {failed} | Total: {total}")
