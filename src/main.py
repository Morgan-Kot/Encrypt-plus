# Top of main.py
import os
import json
import urllib.request
import webbrowser
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from ciphers import CIPHERS, INITIAL_WARNINGS, load_epac_methods, load_single_path, log


def levenshtein_distance(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


class AssetSelectionDialog(tk.Toplevel):
    def __init__(self, parent, release):
        super().__init__(parent)
        self.parent_dialog = parent
        self.release = release
        self.selected_asset = None

        release_name = release.get("name") or release.get("tag_name")
        self.title(f"Select Attachment - {release_name}")
        self.geometry("450x300")
        self.minsize(380, 220)

        BG_COLOR = "#d4d0c8"
        TEXT_COLOR = "#000000"
        self.configure(bg=BG_COLOR)

        self.transient(parent)
        self.grab_set()

        lbl_info = tk.Label(
            self,
            text="Choose an asset to download:",
            font=("MS Sans Serif", 8, "bold"),
            bg=BG_COLOR,
            fg=TEXT_COLOR,
        )
        lbl_info.pack(anchor="w", padx=10, pady=(10, 5))

        list_frame = tk.Frame(self, bg=BG_COLOR)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.asset_listbox = tk.Listbox(
            list_frame,
            bg="#ffffff",
            fg="#000000",
            selectbackground="#0a246a",
            selectforeground="#ffffff",
            bd=2,
            relief="sunken",
            font=("MS Sans Serif", 9)
        )
        self.asset_listbox.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=self.asset_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.asset_listbox.config(yscrollcommand=scrollbar.set)

        self.assets = release.get("assets", [])
        for ast in self.assets:
            name = ast.get("name", "Unknown")
            size_kb = round(ast.get("size", 0) / 1024, 1)
            self.asset_listbox.insert(tk.END, f"{name} ({size_kb} KB)")

        btn_frame = tk.Frame(self, bg=BG_COLOR)
        btn_frame.pack(fill="x", padx=10, pady=10)

        btn_confirm = tk.Button(
            btn_frame,
            text="Download Asset",
            width=16,
            command=self.confirm_selection,
            bg=BG_COLOR,
            fg=TEXT_COLOR,
            relief="raised",
            bd=2,
        )
        btn_confirm.pack(side="left", padx=5)

        btn_cancel = tk.Button(
            btn_frame,
            text="Cancel",
            width=10,
            command=self.destroy,
            bg=BG_COLOR,
            fg=TEXT_COLOR,
            relief="raised",
            bd=2,
        )
        btn_cancel.pack(side="right", padx=5)

    def confirm_selection(self):
        selected = self.asset_listbox.curselection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a file attachment from the list.", parent=self)
            return
        
        self.selected_asset = self.assets[selected[0]]
        self.destroy()


class DownloadDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_app = parent
        self.title("Download Ciphers - GitHub Releases")
        self.geometry("580x480")
        self.minsize(480, 350)

        BG_COLOR = "#d4d0c8"
        TEXT_COLOR = "#000000"
        self.configure(bg=BG_COLOR)

        self.transient(parent)
        self.grab_set()

        self.releases_data = []

        search_frame = tk.Frame(self, bg=BG_COLOR)
        search_frame.pack(fill="x", padx=10, pady=(10, 5))

        lbl_search = tk.Label(search_frame, text="Search (Title/Tags):", bg=BG_COLOR, fg=TEXT_COLOR, font=("MS Sans Serif", 8))
        lbl_search.pack(side="left", padx=(0, 5))

        self.ent_search = tk.Entry(search_frame, bg="#ffffff", fg="#000000", bd=2, relief="sunken")
        self.ent_search.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.ent_search.bind("<KeyRelease>", self.on_search)

        list_frame = tk.Frame(self, bg=BG_COLOR)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.listbox = tk.Listbox(
            list_frame,
            bg="#ffffff",
            fg="#000000",
            selectbackground="#0a246a",
            selectforeground="#ffffff",
            bd=2,
            relief="sunken",
            font=("MS Sans Serif", 9)
        )
        self.listbox.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)

        self.lbl_status = tk.Label(self, text="Fetching releases...", bg=BG_COLOR, fg=TEXT_COLOR, font=("MS Sans Serif", 8))
        self.lbl_status.pack(anchor="w", padx=10)

        btn_frame = tk.Frame(self, bg=BG_COLOR)
        btn_frame.pack(fill="x", padx=10, pady=10)

        btn_download = tk.Button(
            btn_frame,
            text="Select Download",
            width=18,
            command=self.open_asset_selector,
            bg=BG_COLOR,
            fg=TEXT_COLOR,
            relief="raised",
            bd=2,
        )
        btn_download.pack(side="left", padx=5)

        btn_close = tk.Button(
            btn_frame,
            text="Close",
            width=10,
            command=self.destroy,
            bg=BG_COLOR,
            fg=TEXT_COLOR,
            relief="raised",
            bd=2,
        )
        btn_close.pack(side="right", padx=5)

        self.fetch_releases()

    def fetch_releases(self):
        url = "https://api.github.com/repos/Morgan-Kot/Encrypt-plus/releases"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Encrypt-Plus-App"})
            with urllib.request.urlopen(req) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    self.releases_data = data
                    self.populate_list(self.releases_data)
                    self.lbl_status.config(text=f"Loaded {len(data)} releases.")
        except Exception as e:
            self.lbl_status.config(text="Fetch failed.")
            messagebox.showerror(
                "Network Error", 
                f"Failed fetching GitHub releases:\n\n{str(e)}", 
                parent=self
            )

    def populate_list(self, releases):
        self.listbox.delete(0, tk.END)
        for rel in releases:
            title = rel.get("name") or rel.get("tag_name") or "Unnamed Release"
            tag = rel.get("tag_name", "")
            assets = rel.get("assets", [])
            display_str = f"{title} [{tag}] - ({len(assets)} attachment/s)"
            self.listbox.insert(tk.END, display_str)

    def on_search(self, event=None):
        query = self.ent_search.get().strip().lower()
        if not query:
            self.populate_list(self.releases_data)
            return

        scored_releases = []
        for rel in self.releases_data:
            title = (rel.get("name") or "").lower()
            tag = (rel.get("tag_name") or "").lower()

            if query in title or query in tag:
                score = 0
            else:
                title_dist = levenshtein_distance(query, title) if title else 999
                tag_dist = levenshtein_distance(query, tag) if tag else 999
                score = min(title_dist, tag_dist)

            if score <= max(3, len(query)):
                scored_releases.append((score, rel))

        scored_releases.sort(key=lambda x: x[0])
        filtered = [rel for score, rel in scored_releases]
        self.populate_list(filtered)

    def open_asset_selector(self):
        selected_idx = self.listbox.curselection()
        if not selected_idx:
            messagebox.showwarning("Selection Error", "Please select a release from the list.", parent=self)
            return

        idx = selected_idx[0]
        query = self.ent_search.get().strip().lower()

        if query:
            scored_releases = []
            for rel in self.releases_data:
                title = (rel.get("name") or "").lower()
                tag = (rel.get("tag_name") or "").lower()
                if query in title or query in tag:
                    score = 0
                else:
                    title_dist = levenshtein_distance(query, title) if title else 999
                    tag_dist = levenshtein_distance(query, tag) if tag else 999
                    score = min(title_dist, tag_dist)
                if score <= max(3, len(query)):
                    scored_releases.append((score, rel))
            scored_releases.sort(key=lambda x: x[0])
            rel = scored_releases[idx][1]
        else:
            rel = self.releases_data[idx]

        assets = rel.get("assets", [])
        if not assets:
            messagebox.showwarning("Download Error", "Selected release contains no downloadable attachments.", parent=self)
            return

        dialog = AssetSelectionDialog(self, rel)
        self.wait_window(dialog)

        if dialog.selected_asset:
            self.execute_download(dialog.selected_asset)

    def execute_download(self, asset):
        download_url = asset.get("browser_download_url")
        filename = asset.get("name")

        script_dir = os.path.dirname(os.path.abspath(__file__))
        target_dir = os.path.join(script_dir, "epac-methods")
        os.makedirs(target_dir, exist_ok=True)
        save_path = os.path.join(target_dir, filename)

        try:
            self.lbl_status.config(text=f"Downloading '{filename}'...")
            self.update_idletasks()

            req = urllib.request.Request(download_url, headers={"User-Agent": "Encrypt-Plus-App"})
            with urllib.request.urlopen(req) as resp, open(save_path, "wb") as out_file:
                out_file.write(resp.read())

            messagebox.showinfo(
                "Download Success", 
                f"Successfully saved '{filename}' into epac-methods.", 
                parent=self
            )
            self.parent_app.reload_ciphers()
        except Exception as e:
            messagebox.showerror(
                "Download Failed", 
                f"Failed to download asset '{filename}':\n\n{str(e)}", 
                parent=self
            )
        finally:
            self.lbl_status.config(text="Ready.")


class FormulaDialog(tk.Toplevel):
    def __init__(self, parent, cipher_cls):
        super().__init__(parent)
        self.title(f"Formula Info: {cipher_cls.name}")
        self.geometry("460x320")
        self.minsize(350, 250)

        BG_COLOR = "#d4d0c8"
        TEXT_COLOR = "#000000"
        self.configure(bg=BG_COLOR)

        self.transient(parent)
        self.grab_set()

        lbl_title = tk.Label(
            self,
            text=f"{cipher_cls.name} (by {cipher_cls.creator})",
            font=("MS Sans Serif", 10, "bold"),
            bg=BG_COLOR,
            fg=TEXT_COLOR,
        )
        lbl_title.pack(anchor="w", padx=12, pady=(10, 4))

        meta_lbl = tk.Label(
            self,
            text=f"Year: {cipher_cls.year}  |  Copyright: {cipher_cls.copyright}",
            font=("MS Sans Serif", 8),
            bg=BG_COLOR,
            fg=TEXT_COLOR,
        )
        meta_lbl.pack(anchor="w", padx=12, pady=(0, 4))

        exp_frame = tk.LabelFrame(
            self,
            text=" Cipher Explanation ",
            bg=BG_COLOR,
            fg=TEXT_COLOR,
            font=("MS Sans Serif", 8, "bold"),
            bd=2,
            relief="groove",
        )
        exp_frame.pack(fill="both", expand=True, padx=10, pady=4)

        lbl_desc = tk.Label(
            exp_frame,
            text=cipher_cls.desc,
            font=("MS Sans Serif", 9),
            bg="#ffffff",
            fg="#000000",
            anchor="nw",
            justify="left",
            wraplength=400,
            bd=2,
            relief="sunken",
        )
        lbl_desc.pack(fill="both", expand=True, padx=6, pady=6)

        repo_url = cipher_cls.github_url
        lbl_link = tk.Label(
            self,
            text="View Documentation / GitHub Repo",
            font=("MS Sans Serif", 8, "underline"),
            bg=BG_COLOR,
            fg="#000000" if parent.tk.call("tk", "windowingsystem") == "win32" else "blue",
            cursor="hand2",
        )
        lbl_link.pack(pady=(2, 0))
        lbl_link.bind("<Button-1>", lambda e: webbrowser.open_new(repo_url))

        btn_close = tk.Button(
            self,
            text="OK",
            width=10,
            command=self.destroy,
            bg=BG_COLOR,
            fg=TEXT_COLOR,
            relief="raised",
            bd=2,
        )
        btn_close.pack(pady=8)


class EncryptionCenter(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Encrypter++")
        self.geometry("520x600")
        self.minsize(400, 400)

        BG_COLOR = "#d4d0c8"
        TEXT_COLOR = "#000000"
        self.configure(bg=BG_COLOR)

        self.updating = False
        self.selected_cipher_name = tk.StringVar()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        menubar = tk.Menu(self, bg=BG_COLOR, fg=TEXT_COLOR)
        file_menu = tk.Menu(menubar, tearoff=0, bg=BG_COLOR, fg=TEXT_COLOR)
        file_menu.add_command(label="Open Direct Path...", command=self.open_direct_path)
        file_menu.add_command(label="Clear All", command=self.clear_fields)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        formulas_menu = tk.Menu(menubar, tearoff=0, bg=BG_COLOR, fg=TEXT_COLOR)
        formulas_menu.add_command(
            label="View Active Cipher Info", command=self.show_formula_info
        )
        menubar.add_cascade(label="Formulas", menu=formulas_menu)

        menubar.add_command(label="Direct Path", command=self.open_direct_path)
        menubar.add_command(label="Download", command=self.show_download_dialog)

        self.config(menu=menubar)

        top_frame = tk.Frame(self, bg=BG_COLOR, bd=2, relief="groove")
        top_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=6)
        top_frame.columnconfigure(1, weight=1)

        title_lbl = tk.Label(
            top_frame,
            text="Encryption Center",
            font=("MS Sans Serif", 10, "bold"),
            bg=BG_COLOR,
            fg=TEXT_COLOR,
        )
        title_lbl.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        lbl_select = tk.Label(
            top_frame,
            text="Method:",
            font=("MS Sans Serif", 8),
            bg=BG_COLOR,
            fg=TEXT_COLOR,
        )
        lbl_select.grid(row=0, column=2, padx=2, sticky="e")

        self.cipher_dropdown = tk.OptionMenu(
            top_frame,
            self.selected_cipher_name,
            "",
            command=self.on_cipher_change,
        )
        self.cipher_dropdown.config(
            bg=BG_COLOR,
            fg=TEXT_COLOR,
            activebackground="#0a246a",
            activeforeground="#ffffff",
            highlightthickness=1,
            relief="raised",
        )
        self.cipher_dropdown.grid(row=0, column=3, padx=5, pady=3, sticky="e")

        main_frame = tk.Frame(self, bg=BG_COLOR)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        plain_frame = tk.LabelFrame(
            main_frame,
            text=" Plaintext / Input ",
            bg=BG_COLOR,
            fg=TEXT_COLOR,
            font=("MS Sans Serif", 8, "bold"),
            relief="groove",
            bd=2,
        )
        plain_frame.grid(row=0, column=0, sticky="nsew", pady=4)
        plain_frame.columnconfigure(0, weight=1)
        plain_frame.rowconfigure(0, weight=1)

        self.txt_plain = tk.Text(
            plain_frame,
            wrap="word",
            bg="#ffffff",
            fg="#000000",
            bd=2,
            relief="sunken",
            font=("Courier", 9),
        )
        self.txt_plain.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        cipher_frame = tk.LabelFrame(
            main_frame,
            text=" Ciphertext / Encrypted Output ",
            bg=BG_COLOR,
            fg=TEXT_COLOR,
            font=("MS Sans Serif", 8, "bold"),
            relief="groove",
            bd=2,
        )
        cipher_frame.grid(row=1, column=0, sticky="nsew", pady=4)
        cipher_frame.columnconfigure(0, weight=1)
        cipher_frame.rowconfigure(0, weight=1)

        self.txt_cipher = tk.Text(
            cipher_frame,
            wrap="word",
            bg="#ffffff",
            fg="#000000",
            bd=2,
            relief="sunken",
            font=("Courier", 9),
        )
        self.txt_cipher.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        self.txt_plain.bind("<KeyRelease>", self.on_plain_type)
        self.txt_cipher.bind("<KeyRelease>", self.on_cipher_type)

        self.populate_ciphers()
        self.after(200, self.check_initial_warnings)

    def reload_ciphers(self):
        global CIPHERS, INITIAL_WARNINGS
        CIPHERS, INITIAL_WARNINGS = load_epac_methods()
        self.populate_ciphers()
        self.check_initial_warnings()

    def open_direct_path(self):
        answer = messagebox.askyesno(
            "Direct Path Selection",
            "Would you like to select a File (.zip or .epac)?\n\nChoose 'No' to select a Folder instead.",
            parent=self
        )
        path = None
        if answer:
            path = filedialog.askopenfilename(
                title="Select Cipher File (.zip or .epac)",
                filetypes=[("EPAC Supported Files", "*.zip *.epac"), ("All Files", "*.*")],
                parent=self
            )
        else:
            path = filedialog.askdirectory(
                title="Select EPAC Method Directory",
                parent=self
            )

        if not path:
            return

        cipher_cls, errors = load_single_path(path)
        if cipher_cls:
            CIPHERS[cipher_cls.name] = cipher_cls
            self.populate_ciphers()
            self.selected_cipher_name.set(cipher_cls.name)
            self.on_cipher_change()
            messagebox.showinfo("Success", f"Successfully loaded method: '{cipher_cls.name}'", parent=self)
        else:
            err_msg = "\n".join(errors)
            messagebox.showerror("Loading Failed", f"Could not load method from path:\n{path}\n\nErrors:\n{err_msg}", parent=self)

    def populate_ciphers(self):
        menu = self.cipher_dropdown["menu"]
        menu.delete(0, "end")

        if CIPHERS:
            for name in CIPHERS.keys():
                menu.add_command(
                    label=name, command=tk._setit(self.selected_cipher_name, name, self.on_cipher_change)
                )
            first_key = list(CIPHERS.keys())[0]
            self.selected_cipher_name.set(first_key)
        else:
            self.selected_cipher_name.set("No Ciphers Found")

    def check_initial_warnings(self):
        if INITIAL_WARNINGS:
            msg = "The following cipher methods failed to load:\n\n"
            for folder, reason in INITIAL_WARNINGS:
                msg += f"Path: {folder}\nReason: {reason}\n\n"
            messagebox.showwarning("Cipher Loading Warnings", msg)

    def get_cipher_class(self):
        return CIPHERS.get(self.selected_cipher_name.get())

    def on_plain_type(self, event=None):
        if self.updating:
            return
        cipher_cls = self.get_cipher_class()
        if not cipher_cls:
            return

        self.updating = True
        try:
            plain_text = self.txt_plain.get("1.0", tk.END).rstrip("\n")
            encrypted = cipher_cls.encrypt(plain_text)
            self.txt_cipher.delete("1.0", tk.END)
            self.txt_cipher.insert("1.0", encrypted)
        except Exception as e:
            messagebox.showerror(
                "Execution Failure", 
                f"Cipher '{cipher_cls.name}' error on encrypt:\n\n{type(e).__name__}: {str(e)}"
            )
        finally:
            self.updating = False

    def on_cipher_type(self, event=None):
        if self.updating:
            return
        cipher_cls = self.get_cipher_class()
        if not cipher_cls:
            return

        self.updating = True
        try:
            cipher_text = self.txt_cipher.get("1.0", tk.END).rstrip("\n")
            decrypted = cipher_cls.decrypt(cipher_text)
            self.txt_plain.delete("1.0", tk.END)
            self.txt_plain.insert("1.0", decrypted)
        except Exception as e:
            messagebox.showerror(
                "Execution Failure", 
                f"Cipher '{cipher_cls.name}' error on decrypt:\n\n{type(e).__name__}: {str(e)}"
            )
        finally:
            self.updating = False

    def on_cipher_change(self, value=None):
        self.on_plain_type()

    def clear_fields(self):
        self.txt_plain.delete("1.0", tk.END)
        self.txt_cipher.delete("1.0", tk.END)

    def show_formula_info(self):
        cipher_cls = self.get_cipher_class()
        if cipher_cls:
            FormulaDialog(self, cipher_cls)

    def show_download_dialog(self):
        DownloadDialog(self)


if __name__ == "__main__":
    app = EncryptionCenter()
    app.mainloop()

# Bottom of main.py