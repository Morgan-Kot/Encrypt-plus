# Top of ciphers.py
# Cipher loader with detailed terminal logging and single path importing capabilities.

import os
import zipfile
import tempfile
import shutil
from importlib.machinery import SourceFileLoader
import importlib.util
from typing import Dict, Type, Tuple, List


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


def log(msg: str):
    print(f"[EPAC LOG] {msg}")


def load_epac_file(file_path: str):
    abs_path = os.path.abspath(file_path)
    module_name = os.path.splitext(os.path.basename(abs_path))[0]
    log(f"Attempting SourceFileLoader on: {abs_path}")
    
    loader = SourceFileLoader(module_name, abs_path)
    spec = importlib.util.spec_from_loader(module_name, loader)
    if spec is None:
        log(f"ERROR: Could not create module spec for '{abs_path}'.")
        raise ImportError(f"Could not create module spec for '{abs_path}'. Check file syntax.")
        
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    log(f"SUCCESS: Loaded module '{module_name}' from '{abs_path}'.")
    return module


def create_cipher_class(class_name: str, enc_mod, dec_mod) -> Type[BaseCipher]:
    cipher_name = getattr(enc_mod, "NAME", class_name)
    cipher_desc = getattr(enc_mod, "DESCRIPTION", "No description provided.")
    cipher_creator = getattr(enc_mod, "CREATOR", "Unknown")
    cipher_year = getattr(enc_mod, "YEAR", "N/A")
    cipher_copyright = getattr(enc_mod, "COPYRIGHT", "N/A")
    cipher_url = getattr(enc_mod, "GITHUB_URL", "https://github.com/Morgan-Kot/Standard-Lock/tree/Encryption")

    log(f"Creating cipher class instance: '{cipher_name}' (Identifier: {class_name})")

    return type(
        f"EPAC_{class_name}",
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


def process_cipher_directory(dir_path: str, default_identifier: str) -> Tuple[Type[BaseCipher], List[str]]:
    log(f"Processing directory: '{dir_path}' with default identifier: '{default_identifier}'")
    errors = []
    
    if not os.path.exists(dir_path):
        log(f"ERROR: Directory '{dir_path}' does not exist.")
        return None, [f"Directory '{dir_path}' does not exist."]

    dir_files = os.listdir(dir_path)
    log(f"Directory contents of '{dir_path}': {dir_files}")

    enc_path = os.path.join(dir_path, "encrypter.epac")
    dec_path = os.path.join(dir_path, "decrypter.epac")
    
    single_path = None
    for entry in dir_files:
        if entry.lower() == "single.epac" or entry.lower().endswith(".epac"):
            single_path = os.path.join(dir_path, entry)
            log(f"Found candidate single epac file: '{single_path}'")
            break

    # Dual file check
    if os.path.exists(enc_path) or os.path.exists(dec_path):
        log(f"Evaluating dual epac mode for folder '{dir_path}'")
        if not os.path.exists(enc_path):
            errors.append(f"Missing 'encrypter.epac' in '{dir_path}'.")
        if not os.path.exists(dec_path):
            errors.append(f"Missing 'decrypter.epac' in '{dir_path}'.")
        if errors:
            log(f"Dual mode validation failed: {errors}")
            return None, errors

        try:
            enc_mod = load_epac_file(enc_path)
            dec_mod = load_epac_file(dec_path)

            if not hasattr(enc_mod, "encrypt"):
                errors.append(f"'encrypter.epac' missing 'encrypt(plaintext)' in '{dir_path}'.")
            if not hasattr(dec_mod, "decrypt"):
                errors.append(f"'decrypter.epac' missing 'decrypt(ciphertext)' in '{dir_path}'.")

            if errors:
                log(f"Dual mode attributes missing: {errors}")
                return None, errors

            return create_cipher_class(default_identifier, enc_mod, dec_mod), []
        except Exception as e:
            err_msg = f"Error parsing dual .epac files in '{dir_path}': {str(e)}"
            log(f"EXCEPTION: {err_msg}")
            errors.append(err_msg)
            return None, errors

    # Standalone single.epac check
    elif single_path and os.path.exists(single_path):
        log(f"Evaluating single epac mode for file '{single_path}'")
        try:
            mod = load_epac_file(single_path)
            if not hasattr(mod, "encrypt"):
                errors.append(f"'{os.path.basename(single_path)}' missing 'encrypt(plaintext)' in '{dir_path}'.")
            if not hasattr(mod, "decrypt"):
                errors.append(f"'{os.path.basename(single_path)}' missing 'decrypt(ciphertext)' in '{dir_path}'.")

            if errors:
                log(f"Single mode attributes missing: {errors}")
                return None, errors

            return create_cipher_class(default_identifier, mod, mod), []
        except Exception as e:
            err_msg = f"Error parsing '{os.path.basename(single_path)}' in '{dir_path}': {str(e)}"
            log(f"EXCEPTION: {err_msg}")
            errors.append(err_msg)
            return None, errors

    else:
        err_msg = f"Invalid cipher folder '{dir_path}'. Must contain '.epac' file OR both 'encrypter.epac' and 'decrypter.epac'."
        log(f"REJECTED: {err_msg}")
        errors.append(err_msg)
        return None, errors


def find_target_dir(root_dir: str) -> str:
    log(f"Searching for target .epac location recursively inside extracted path: '{root_dir}'")
    for current_root, dirs, files in os.walk(root_dir):
        log(f"Inspecting extracted subfolder: '{current_root}' | Files: {files}")
        lower_files = [f.lower() for f in files]
        has_dual = ("encrypter.epac" in lower_files and "decrypter.epac" in lower_files)
        has_single = any(f.endswith(".epac") for f in lower_files)
        if has_dual or has_single:
            log(f"Match found in walk: '{current_root}'")
            return current_root
    log(f"No nested match found. Defaulting to root extracted folder: '{root_dir}'")
    return root_dir


def load_single_path(path: str) -> Tuple[Type[BaseCipher], List[str]]:
    log(f"--- Direct Path Loading Started for: '{path}' ---")
    if not os.path.exists(path):
        log(f"ERROR: Specified direct path does not exist: '{path}'")
        return None, [f"Path '{path}' does not exist."]

    if os.path.isdir(path):
        identifier = os.path.basename(os.path.normpath(path))
        return process_cipher_directory(path, identifier)

    elif path.lower().endswith(".zip"):
        if not zipfile.is_zipfile(path):
            log(f"ERROR: '{path}' is not a valid zip archive.")
            return None, [f"File '{path}' is not a valid zip archive."]

        temp_dir = tempfile.mkdtemp()
        log(f"Extracting direct zip file to temp directory: '{temp_dir}'")
        try:
            with zipfile.ZipFile(path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)
            valid_dir = find_target_dir(temp_dir)
            base_identifier = os.path.splitext(os.path.basename(path))[0]
            return process_cipher_directory(valid_dir, base_identifier)
        except Exception as e:
            log(f"EXCEPTION: Direct zip load failed: {str(e)}")
            return None, [f"Failed unpacking zip: {str(e)}"]
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    elif path.lower().endswith(".epac"):
        base_identifier = os.path.splitext(os.path.basename(path))[0]
        parent_dir = os.path.dirname(path)
        log(f"Loading direct standalone epac file from directory: '{parent_dir}'")
        return process_cipher_directory(parent_dir, base_identifier)

    else:
        log(f"ERROR: Unsupported file format or direct target: '{path}'")
        return None, [f"Unsupported target or extension for path '{path}'."]


def load_epac_methods(base_dir: str = "epac-methods"):
    log("================== Starting Method Discovery ==================")
    ciphers = {}
    warnings = []

    script_dir = os.path.dirname(os.path.abspath(__file__))
    target_dir = os.path.join(script_dir, base_dir)
    log(f"Target epac directory set to: '{target_dir}'")

    if not os.path.exists(target_dir):
        log(f"Directory '{target_dir}' not found. Creating empty target folder.")
        os.makedirs(target_dir, exist_ok=True)
        return ciphers, warnings

    items = os.listdir(target_dir)
    log(f"Items detected in base directory ({len(items)} items total): {items}")

    for item in items:
        item_path = os.path.join(target_dir, item)
        log(f"\n--- Checking Item: '{item}' ---")

        # 1. Directories
        if os.path.isdir(item_path):
            log(f"Item '{item}' recognized as Directory.")
            cipher_cls, errors = process_cipher_directory(item_path, item)
            if cipher_cls:
                log(f"Successfully registered directory method: '{cipher_cls.name}'")
                ciphers[cipher_cls.name] = cipher_cls
            else:
                for err in errors:
                    warnings.append((item_path, err))

        # 2. Standalone .epac files in base folder
        elif item.lower().endswith(".epac"):
            log(f"Item '{item}' recognized as Standalone .epac File.")
            base_identifier = os.path.splitext(item)[0]
            try:
                mod = load_epac_file(item_path)
                errs = []
                if not hasattr(mod, "encrypt"):
                    errs.append(f"File '{item}' missing 'encrypt(plaintext)'.")
                if not hasattr(mod, "decrypt"):
                    errs.append(f"File '{item}' missing 'decrypt(ciphertext)'.")
                
                if not errs:
                    cipher_cls = create_cipher_class(base_identifier, mod, mod)
                    log(f"Successfully registered single file method: '{cipher_cls.name}'")
                    ciphers[cipher_cls.name] = cipher_cls
                else:
                    for err in errs:
                        warnings.append((item_path, err))
            except Exception as e:
                log(f"EXCEPTION: Processing standalone epac file failed: {str(e)}")
                warnings.append((item_path, f"Error parsing standalone file '{item}': {str(e)}"))

        # 3. Zip Archives
        elif item.lower().endswith(".zip"):
            log(f"Item '{item}' recognized as Zip Archive.")
            if not zipfile.is_zipfile(item_path):
                log(f"ERROR: '{item}' is not a valid zip archive.")
                warnings.append((item_path, "File is not a valid or readable .zip archive."))
                continue

            temp_dir = tempfile.mkdtemp()
            log(f"Extracting '{item}' to temporary folder: '{temp_dir}'")
            try:
                with zipfile.ZipFile(item_path, "r") as zip_ref:
                    zip_ref.extractall(temp_dir)

                valid_dir = find_target_dir(temp_dir)
                base_identifier = os.path.splitext(item)[0]
                
                cipher_cls, errors = process_cipher_directory(valid_dir, base_identifier)
                if cipher_cls:
                    log(f"Successfully registered zip method: '{cipher_cls.name}'")
                    ciphers[cipher_cls.name] = cipher_cls
                else:
                    for err in errors:
                        warnings.append((item_path, f"Zip contents error: {err}"))
            except Exception as e:
                log(f"EXCEPTION: Zip handling failed for '{item}': {str(e)}")
                warnings.append((item_path, f"Failed unpacking zip archive: {str(e)}"))
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)
                log(f"Cleaned up temporary directory: '{temp_dir}'")

        else:
            log(f"Ignoring non-cipher item: '{item}'")

    log(f"================ Discovery Complete: Registered {len(ciphers)} methods ================\n")
    return ciphers, warnings


CIPHERS, INITIAL_WARNINGS = load_epac_methods()

# Bottom of ciphers.py