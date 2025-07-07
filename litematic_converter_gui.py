import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys
import threading
from pathlib import Path
import subprocess

class ModernLitematicConverterGUI:

    def __init__(self, root):
        self.root = root
        self.root.title('Litematic to Blueprint Converter')
        self.root.geometry('900x700')
        self.root.resizable(True, True)
        self.root.state('zoomed')
        self.colors = {'bg_primary': '#1a1a1a', 'bg_secondary': '#2d2d2d',
            'bg_tertiary': '#3a3a3a', 'accent': '#00d4ff', 'accent_hover':
            '#00b8e6', 'success': '#00ff88', 'error': '#ff4757', 'warning':
            '#ffa502', 'text_primary': '#ffffff', 'text_secondary':
            '#b8b8b8', 'text_muted': '#808080', 'border': '#404040',
            'shadow': '#0f0f0f'}
        self.root.configure(bg=self.colors['bg_primary'])
        self.default_input_dir = self._get_smart_input_dir()
        self.default_output_dir = self._get_smart_output_dir()
        self.selected_files = []
        self.output_folder = tk.StringVar(value=self.default_output_dir)
        self.converter_script = os.path.join(os.path.dirname(__file__),
            'litematic_to_bp_converter.py')
        if not os.path.exists(self.converter_script):
            messagebox.showerror('Error',
                f"""Converter script '{self.converter_script}' not found!
Make sure it's in the same folder as this GUI."""
                )
            sys.exit(1)
        self.setup_modern_styles()
        self.setup_ui()
        self.center_window()

    def _get_smart_input_dir(self):
        possible_dirs = []
        if sys.platform == 'win32':
            appdata = os.getenv('APPDATA')
            if appdata:
                possible_dirs.extend([os.path.join(appdata, '.minecraft',
                    'schematics'), os.path.join(appdata, '.minecraft',
                    'config', 'litematica', 'schematics'), os.path.join(
                    appdata, '.minecraft')])
        elif sys.platform == 'darwin':
            home = os.path.expanduser('~')
            possible_dirs.extend([os.path.join(home, 'Library',
                'Application Support', 'minecraft', 'schematics'), os.path.
                join(home, 'Library', 'Application Support', 'minecraft',
                'config', 'litematica', 'schematics'), os.path.join(home,
                'Library', 'Application Support', 'minecraft')])
        else:
            home = os.path.expanduser('~')
            possible_dirs.extend([os.path.join(home, '.minecraft',
                'schematics'), os.path.join(home, '.minecraft', 'config',
                'litematica', 'schematics'), os.path.join(home, '.minecraft')])
        home = os.path.expanduser('~')
        possible_dirs.extend([os.path.join(home, 'Documents', 'Minecraft'),
            os.path.join(home, 'Documents', 'Schematics'), os.path.join(
            home, 'Downloads'), os.path.join(home, 'Desktop')])
        for directory in possible_dirs:
            if os.path.exists(directory):
                return directory
        return os.getcwd()

    def _get_smart_output_dir(self):
        possible_dirs = []
        if sys.platform == 'win32':
            appdata = os.getenv('APPDATA')
            if appdata:
                possible_dirs.extend([os.path.join(appdata, '.minecraft',
                    'config', 'axiom', 'blueprints'), os.path.join(appdata,
                    '.minecraft', 'blueprints'), os.path.join(appdata,
                    '.minecraft')])
        elif sys.platform == 'darwin':
            home = os.path.expanduser('~')
            possible_dirs.extend([os.path.join(home, 'Library',
                'Application Support', 'minecraft', 'config', 'axiom',
                'blueprints'), os.path.join(home, 'Library',
                'Application Support', 'minecraft', 'blueprints'), os.path.
                join(home, 'Library', 'Application Support', 'minecraft')])
        else:
            home = os.path.expanduser('~')
            possible_dirs.extend([os.path.join(home, '.minecraft', 'config',
                'axiom', 'blueprints'), os.path.join(home, '.minecraft',
                'blueprints'), os.path.join(home, '.minecraft')])
        home = os.path.expanduser('~')
        possible_dirs.extend([os.path.join(home, 'Documents', 'Minecraft',
            'Blueprints'), os.path.join(home, 'Documents', 'Blueprints'),
            os.path.join(home, 'Desktop', 'Blueprints'), os.path.join(home,
            'Desktop')])
        for directory in possible_dirs:
            if os.path.exists(directory):
                return directory
        home = os.path.expanduser('~')
        preferred_output = os.path.join(home, 'Documents',
            'Minecraft Blueprints')
        try:
            os.makedirs(preferred_output, exist_ok=True)
            return preferred_output
        except (OSError, PermissionError):
            pass
        return os.getcwd()

    def setup_modern_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('Modern.TFrame', background=self.colors[
            'bg_primary'], relief='flat', borderwidth=0)
        self.style.configure('Card.TFrame', background=self.colors[
            'bg_secondary'], relief='flat', borderwidth=1)
        self.style.configure('Modern.TLabel', background=self.colors[
            'bg_primary'], foreground=self.colors['text_primary'], font=(
            'Segoe UI', 10))
        self.style.configure('Title.TLabel', background=self.colors[
            'bg_primary'], foreground=self.colors['accent'], font=(
            'Segoe UI', 24, 'bold'))
        self.style.configure('Heading.TLabel', background=self.colors[
            'bg_primary'], foreground=self.colors['text_primary'], font=(
            'Segoe UI', 14, 'bold'))
        self.style.configure('Subtitle.TLabel', background=self.colors[
            'bg_primary'], foreground=self.colors['text_secondary'], font=(
            'Segoe UI', 10))
        self.style.configure('Modern.TButton', background=self.colors[
            'bg_tertiary'], foreground=self.colors['text_primary'],
            borderwidth=0, focuscolor='none', font=('Segoe UI', 10),
            padding=(15, 8))
        self.style.map('Modern.TButton', background=[('active', self.colors
            ['border']), ('pressed', self.colors['bg_tertiary'])])
        self.style.configure('Accent.TButton', background=self.colors[
            'accent'], foreground='white', borderwidth=0, focuscolor='none',
            font=('Segoe UI', 12, 'bold'), padding=(20, 12))
        self.style.map('Accent.TButton', background=[('active', self.colors
            ['accent_hover']), ('pressed', self.colors['accent']), (
            'disabled', self.colors['border'])])
        self.style.configure('Modern.TEntry', fieldbackground=self.colors[
            'bg_tertiary'], borderwidth=1, relief='flat', insertcolor=self.
            colors['text_primary'], foreground=self.colors['text_primary'],
            font=('Segoe UI', 11), padding=(12, 8))
        self.style.configure('Modern.Horizontal.TProgressbar', background=
            self.colors['accent'], troughcolor=self.colors['bg_tertiary'],
            borderwidth=0, lightcolor=self.colors['accent'], darkcolor=self
            .colors['accent'])

    def setup_ui(self):
        main_container = tk.Frame(self.root, bg=self.colors['bg_primary'])
        main_container.pack(fill='both', expand=True, padx=30, pady=30)
        self.create_header(main_container)
        content_frame = tk.Frame(main_container, bg=self.colors['bg_primary'])
        content_frame.pack(fill='both', expand=True, pady=(30, 0))
        self.create_file_selection_card(content_frame)
        self.create_output_card(content_frame)
        self.create_convert_section(content_frame)
        self.create_bottom_section(main_container)

    def create_header(self, parent):
        header_frame = tk.Frame(parent, bg=self.colors['bg_primary'])
        header_frame.pack(fill='x', pady=(0, 20))
        title_frame = tk.Frame(header_frame, bg=self.colors['bg_primary'])
        title_frame.pack()
        title_label = ttk.Label(title_frame, text='⚡ Litematic Converter',
            style='Title.TLabel')
        title_label.pack()
        subtitle_label = ttk.Label(title_frame, text=
            'Convert .litematic files to .bp blueprints with style', style=
            'Subtitle.TLabel')
        subtitle_label.pack(pady=(5, 0))
        separator = tk.Frame(header_frame, height=2, bg=self.colors['accent'])
        separator.pack(fill='x', pady=(20, 0))

    def create_file_selection_card(self, parent):
        card_frame = tk.Frame(parent, bg=self.colors['bg_secondary'],
            relief='flat')
        card_frame.pack(fill='both', expand=True, pady=(0, 20))
        shadow_frame = tk.Frame(parent, bg=self.colors['shadow'], height=4)
        shadow_frame.pack(fill='x', pady=(0, 20))
        card_content = tk.Frame(card_frame, bg=self.colors['bg_secondary'])
        card_content.pack(fill='both', expand=True, padx=25, pady=25)
        header_frame = tk.Frame(card_content, bg=self.colors['bg_secondary'])
        header_frame.pack(fill='x', pady=(0, 15))
        ttk.Label(header_frame, text='📁 Select Files', style='Heading.TLabel'
            ).pack(side='left')
        files_count_label = ttk.Label(header_frame, text='0 files selected',
            style='Subtitle.TLabel')
        files_count_label.pack(side='right')
        self.files_count_label = files_count_label
        list_frame = tk.Frame(card_content, bg=self.colors['bg_secondary'])
        list_frame.pack(fill='both', expand=True, pady=(0, 15))
        self.file_listbox = tk.Listbox(list_frame, bg=self.colors[
            'bg_tertiary'], fg=self.colors['text_primary'],
            selectbackground=self.colors['accent'], selectforeground=
            'white', borderwidth=0, highlightthickness=0, font=('Segoe UI',
            10), activestyle='none')
        self.file_listbox.pack(side='left', fill='both', expand=True)
        scrollbar = tk.Scrollbar(list_frame, bg=self.colors['bg_tertiary'],
            troughcolor=self.colors['bg_tertiary'], borderwidth=0,
            highlightthickness=0)
        scrollbar.pack(side='right', fill='y')
        self.file_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.file_listbox.yview)
        file_buttons_frame = tk.Frame(card_content, bg=self.colors[
            'bg_secondary'])
        file_buttons_frame.pack(fill='x')
        self.browse_files_btn = ttk.Button(file_buttons_frame, text=
            '📁 Browse Files', command=self.select_files, style='Modern.TButton'
            )
        self.browse_files_btn.pack(side='left', padx=(0, 10))
        self.remove_selected_btn = ttk.Button(file_buttons_frame, text=
            '❌ Remove Selected', command=self.remove_selected_file, style=
            'Modern.TButton')
        self.remove_selected_btn.pack(side='left', padx=(0, 10))
        self.clear_all_btn = ttk.Button(file_buttons_frame, text=
            '🗑️ Clear All', command=self.clear_files, style='Modern.TButton')
        self.clear_all_btn.pack(side='left')

    def create_output_card(self, parent):
        card_frame = tk.Frame(parent, bg=self.colors['bg_secondary'],
            relief='flat')
        card_frame.pack(fill='x', pady=(0, 20))
        card_content = tk.Frame(card_frame, bg=self.colors['bg_secondary'])
        card_content.pack(fill='both', expand=True, padx=25, pady=20)
        ttk.Label(card_content, text='📂 Output Destination', style=
            'Heading.TLabel').pack(anchor='w', pady=(0, 10))
        output_frame = tk.Frame(card_content, bg=self.colors['bg_secondary'])
        output_frame.pack(fill='x')
        self.output_entry = ttk.Entry(output_frame, textvariable=self.
            output_folder, style='Modern.TEntry')
        self.output_entry.pack(side='left', fill='x', expand=True, padx=(0, 10)
            )
        self.browse_btn = ttk.Button(output_frame, text='Browse', command=
            self.select_output_folder, style='Modern.TButton')
        self.browse_btn.pack(side='right')

    def create_convert_section(self, parent):
        card_frame = tk.Frame(parent, bg=self.colors['bg_secondary'],
            relief='flat')
        card_frame.pack(fill='x', pady=(20, 0))
        card_content = tk.Frame(card_frame, bg=self.colors['bg_secondary'])
        card_content.pack(fill='both', expand=True, padx=25, pady=20)
        header_frame = tk.Frame(card_content, bg=self.colors['bg_secondary'])
        header_frame.pack(fill='x', pady=(0, 15))
        ttk.Label(header_frame, text='🚀 Ready to Convert', style=
            'Heading.TLabel').pack(side='left')
        self.status_label = ttk.Label(header_frame, text='Status: Ready',
            style='Subtitle.TLabel')
        self.status_label.pack(side='right')
        self.convert_btn = ttk.Button(card_content, text='🚀 Convert Files',
            command=self.start_conversion, style='Accent.TButton')
        self.convert_btn.pack(fill='x', pady=(20, 0))

    def create_bottom_section(self, parent):
        bottom_frame = tk.Frame(parent, bg=self.colors['bg_primary'])
        bottom_frame.pack(fill='both', expand=True, pady=(20, 0))
        progress_frame = tk.Frame(bottom_frame, bg=self.colors['bg_secondary'])
        progress_frame.pack(fill='x', pady=(0, 20))
        progress_content = tk.Frame(progress_frame, bg=self.colors[
            'bg_secondary'])
        progress_content.pack(fill='x', padx=25, pady=15)
        ttk.Label(progress_content, text='📊 Progress', style='Heading.TLabel'
            ).pack(anchor='w', pady=(0, 10))
        self.progress = ttk.Progressbar(progress_content, mode=
            'indeterminate', style='Modern.Horizontal.TProgressbar')
        self.progress.pack(fill='x')
        log_frame = tk.Frame(bottom_frame, bg=self.colors['bg_secondary'])
        log_frame.pack(fill='both', expand=True)
        log_content = tk.Frame(log_frame, bg=self.colors['bg_secondary'])
        log_content.pack(fill='both', expand=True, padx=25, pady=25)
        log_header = tk.Frame(log_content, bg=self.colors['bg_secondary'])
        log_header.pack(fill='x', pady=(0, 10))
        ttk.Label(log_header, text='📜 Conversion Log', style='Heading.TLabel'
            ).pack(side='left')
        clear_log_btn = ttk.Button(log_header, text='Clear Log', command=
            self.clear_log, style='Modern.TButton')
        clear_log_btn.pack(side='right')
        self.log_text = scrolledtext.ScrolledText(log_content, bg=self.
            colors['bg_tertiary'], fg=self.colors['text_primary'],
            borderwidth=0, highlightthickness=0, font=('Consolas', 10),
            insertbackground=self.colors['text_primary'])
        self.log_text.pack(fill='both', expand=True)
        self.log_message('🎉 Welcome to Litematic Converter!')
        self.log_message(f'📍 Converter script: {self.converter_script}')
        self.log_message('💡 Add some .litematic files to get started!')

    def select_files(self):
        files = filedialog.askopenfilenames(title='Select Litematic Files',
            filetypes=[('Litematic files', '*.litematic'), ('All files',
            '*.*')], multiple=True, initialdir=self.default_input_dir)
        added_count = 0
        for file in files:
            if file not in self.selected_files:
                self.selected_files.append(file)
                filename = os.path.basename(file)
                self.file_listbox.insert(tk.END, f'📄 {filename}')
                added_count += 1
        self.update_files_count()
        if added_count > 0:
            self.log_message(
                f'✅ Added {added_count} file(s) to conversion queue')

    def clear_files(self):
        self.selected_files.clear()
        self.file_listbox.delete(0, tk.END)
        self.update_files_count()
        self.log_message('🗑️ Cleared all files from queue')

    def remove_selected_file(self):
        selection = self.file_listbox.curselection()
        if selection:
            index = selection[0]
            filename = os.path.basename(self.selected_files[index])
            del self.selected_files[index]
            self.file_listbox.delete(index)
            self.update_files_count()
            self.log_message(f'🗑️ Removed: {filename}')

    def select_output_folder(self):
        folder = filedialog.askdirectory(title='Select Output Folder',
            initialdir=self.output_folder.get())
        if folder:
            self.output_folder.set(folder)
            self.log_message(f'📂 Output folder: {folder}')

    def update_files_count(self):
        count = len(self.selected_files)
        self.files_count_label.config(text=f'{count} files selected')

    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
        self.log_message('📜 Log cleared')

    def log_message(self, message):
        self.log_text.insert(tk.END, message + '\n')
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def start_conversion(self):
        if not self.selected_files:
            messagebox.showwarning('No Files',
                'Please select at least one litematic file to convert.')
            return
        if not self.output_folder.get():
            messagebox.showwarning('No Output Folder',
                'Please select an output folder.')
            return
        if not os.path.exists(self.output_folder.get()):
            messagebox.showerror('Invalid Folder',
                'The selected output folder does not exist.')
            return
        self.convert_btn.configure(state='disabled', text='🔄 Converting...')
        self.status_label.config(text='Converting...')
        self.progress.start()
        thread = threading.Thread(target=self.convert_files, daemon=True)
        thread.start()

    def convert_files(self):
        try:
            total_files = len(self.selected_files)
            successful = 0
            failed = 0
            self.log_message(
                f'\n🚀 Starting conversion of {total_files} file(s)')
            self.log_message('=' * 50)
            for i, input_file in enumerate(self.selected_files, 1):
                try:
                    if not os.path.exists(input_file):
                        failed += 1
                        self.log_message(
                            f'❌ Input file not found: {input_file}')
                        continue
                    input_name = Path(input_file).stem
                    output_file = os.path.join(self.output_folder.get(),
                        f'{input_name}.bp')
                    self.log_message(
                        f'🔄 [{i}/{total_files}] Converting: {os.path.basename(input_file)}'
                        )
                    result = subprocess.run([sys.executable, self.
                        converter_script, input_file, output_file],
                        capture_output=True, text=True, timeout=120)
                    if result.stdout:
                        self.log_message(f'   📤 {result.stdout.strip()}')
                    if result.stderr:
                        self.log_message(f'   ⚠️ {result.stderr.strip()}')
                    ret_code = result.returncode
                    if ret_code == 0 and os.path.exists(output_file):
                        successful += 1
                        file_size = os.path.getsize(output_file)
                        self.log_message(f'✅ Success ({file_size:,} bytes)')
                    else:
                        failed += 1
                        self.log_message(
                            f'❌ Failed to convert {os.path.basename(input_file)}'
                            )
                except subprocess.TimeoutExpired:
                    failed += 1
                    self.log_message(
                        f'⏱️ Timeout: {os.path.basename(input_file)}')
                except Exception as e:
                    failed += 1
                    self.log_message(
                        f'💥 Error converting {os.path.basename(input_file)} - {str(e)}'
                        )
            self.log_message('\n' + '=' * 50)
            self.log_message('🎯 CONVERSION COMPLETE')
            self.log_message(f'✅ Successful: {successful}')
            self.log_message(f'❌ Failed: {failed}')
            self.log_message(f'📁 Output: {self.output_folder.get()}')
            if failed == 0:
                messagebox.showinfo('🎉 Success!',
                    f'All {successful} file(s) converted successfully!')
            else:
                messagebox.showwarning('⚠️ Partial Success',
                    f"""Converted {successful} file(s) successfully.
{failed} file(s) failed."""
                    )
        except Exception as e:
            self.log_message(f'💥 Conversion failed: {str(e)}')
            messagebox.showerror('Error', f'Conversion failed: {str(e)}')
        finally:
            self.root.after(0, self._conversion_finished)

    def _conversion_finished(self):
        self.progress.stop()
        self.convert_btn.configure(state='normal', text='🚀 Convert Files')
        self.status_label.config(text='Ready')

    def center_window(self):
        self.root.update_idletasks()
        x = self.root.winfo_screenwidth() // 2 - self.root.winfo_width() // 2
        y = self.root.winfo_screenheight() // 2 - self.root.winfo_height() // 2
        self.root.geometry(f'+{x}+{y}')

def main():
    root = tk.Tk()
    app = ModernLitematicConverterGUI(root)
    root.mainloop()
if __name__ == '__main__':
    main()