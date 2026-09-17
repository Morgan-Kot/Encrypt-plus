# Top of ciphers.py
# Dynamic cipher loader using SourceFileLoader to parse .epac files properly

import os
from importlib.machinery import SourceFileLoader
import importlib.util
from typing import Dict, Type


class BaseCipher:
    name = "Base"
    desc = "Base cipher class"
    creator = "Unknown"
    year = "N/A"
    copyright = "N/A"
    github_url = "https://github.com/Morgan-Kot/Standard-Lock/tree/Encryption"

    @staticmethod
    def encrypt(plaintext: str) -> str:
        raise NotImplementedError

    @staticmethod
    def decrypt(ciphertext: str) -> str:
        raise NotImplementedError


def load_epac_file(file_path: str):
    abs_path = os.path.abspath(file_path)
    module_name = os.path.splitext(os.path.basename(abs_path))[0]
    
    loader = SourceFileLoader(module_name, abs_path)
    spec = importlib.util.spec_from_loader(module_name, loader)
    if spec is None:
        raise ImportError(f"Could not create module spec for {abs_path}")
        
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def load_epac_methods(base_dir: str = "epac-methods"):
    ciphers = {}
    warnings = []

    script_dir = os.path.dirname(os.path.abspath(__file__))
    target_dir = os.path.join(script_dir, base_dir)

    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)
        return ciphers, warnings

    for folder_name in os.listdir(target_dir):
        folder_path = os.path.join(target_dir, folder_name)
        if not os.path.isdir(folder_path):
            continue

        enc_path = os.path.join(folder_path, "encrypter.epac")
        dec_path = os.path.join(folder_path, "decrypter.epac")

        if not os.path.exists(enc_path) or not os.path.exists(dec_path):
            warnings.append((
                folder_path,
                "Missing required files. Both 'encrypter.epac' and 'decrypter.epac' must exist."
            ))
            continue

        try:
            enc_mod = load_epac_file(enc_path)
            dec_mod = load_epac_file(dec_path)

            if not hasattr(enc_mod, "encrypt"):
                raise AttributeError("encrypter.epac is missing the 'encrypt(plaintext)' function.")
            if not hasattr(dec_mod, "decrypt"):
                raise AttributeError("decrypter.epac is missing the 'decrypt(ciphertext)' function.")

            cipher_name = getattr(enc_mod, "NAME", folder_name)
            cipher_desc = getattr(enc_mod, "DESCRIPTION", "No description provided.")
            cipher_creator = getattr(enc_mod, "CREATOR", "Unknown")
            cipher_year = getattr(enc_mod, "YEAR", "N/A")
            cipher_copyright = getattr(enc_mod, "COPYRIGHT", "N/A")
            cipher_url = getattr(enc_mod, "GITHUB_URL", "https://github.com/Morgan-Kot/Standard-Lock/tree/Encryption")

            dynamic_cipher = type(
                f"EPAC_{folder_name}",
                (BaseCipher,),
                {
                    "name": cipher_name,
                    "desc": cipher_desc,
                    "creator": cipher_creator,
                    "year": cipher_year,
                    "copyright": cipher_copyright,
                    "github_url": cipher_url,
                    "encrypt": staticmethod(enc_mod.encrypt),
                    "decrypt": staticmethod(dec_mod.decrypt),
                }
            )

            ciphers[cipher_name] = dynamic_cipher

        except Exception as e:
            warnings.append((folder_path, str(e)))

    return ciphers, warnings


CIPHERS, INITIAL_WARNINGS = load_epac_methods()

# Bottom of ciphers.py
