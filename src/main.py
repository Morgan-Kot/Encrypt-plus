import webbrowser
import tkinter as tk
from tkinter import messagebox
from ciphers import CIPHERS, INITIAL_WARNINGS


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
        file_menu.add_command(label="Clear All", command=self.clear_fields)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        formulas_menu = tk.Menu(menubar, tearoff=0, bg=BG_COLOR, fg=TEXT_COLOR)
        formulas_menu.add_command(
            label="View Active Cipher Info", command=self.show_formula_info
        )
        menubar.add_cascade(label="Formulas", menu=formulas_menu)

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
            msg = "The following .epac methods failed to load and should be removed/fixed:\n\n"
            for folder, reason in INITIAL_WARNINGS:
                msg += f"Path: {folder}\nReason: {reason}\n\n"
            messagebox.showwarning(".epac Loading Warning", msg)

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
            messagebox.showerror("Encryption Error", f"Failed during execution:\n{str(e)}")
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
            messagebox.showerror("Decryption Error", f"Failed during execution:\n{str(e)}")
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


if __name__ == "__main__":
    app = EncryptionCenter()
    app.mainloop()
