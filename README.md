<p align="center">
  <img src="assets/ModUpdater.png" alt="Stellaris Mod Updater Logo" width="300">
</p>

# Stellaris Mod Updater v4.0

A Python-based utility designed to assist Stellaris modders in comparing and updating mod content across different game versions. This tool is useful for tracking basic changes (any kind of syntax, traits, modifiers) and ensuring mod compatibility.

## ✨ Features

Automate the process of updating a modpack's version metadata. It includes functionality to:

- Scan and validate mod files inside a given folder.
- Assists with batch processing multiple mods at once.
- Copy or sync mod directories into a new output folder.
- Update .mod descriptor files, including fields like version, path, and supported_version.
- Simple syntax-formatter (and so validator).
- Automatic <b>downgrade</b> to v4.0 and to v3.14 (WIP)!

### ⌨️ Example 
- https://github.com/Coggernaut/Distant-Stars-Overhaul/commit/5b259f82002b4ce993c70179d24c39f996d86d65

## 🛠️ Requirements

- Python 3.6 or higher

## 📦 Installation

1. (optional) Clone the repository (needs Git):

 ```bash
 git clone https://github.com/F1r3Pr1nc3/Stellaris-Mod-Updater.git
 cd Stellaris-Mod-Updater
 ```

Alternatively, download and extract the ZIP manually from the [GitHub releases page](https://github.com/F1r3Pr1nc3/Stellaris-Mod-Updater/releases).

## 🚀 Usage

2. Execute `py modupdater-v4.0.py`
3. If you run the script for the first time, run it again.

### ⚙️ Optional Parameters

You can enable additional functionality using either config variables or command-line flags:

- `-h` (`--help`) — Prints available options and descriptions
- `-c` (`--code_cosmetic`) — enables cosmetic formatting changes in the code output 
- `-m` (`--mergerofrules`) — forces compatibility for [The Merger of Rules](https://steamcommunity.com/workshop/filedetails/2807759164) (MoR) - otherwise automatically detection (slower)
- `-ut` (`--ACTUAL_STELLARIS_VERSION_FLOAT`):
  - Specifies the maximum Stellaris version to which the updater should apply changes.
  - Example: `-ut = 3.6`
- `-w` (`--only_warning`) — only output warnings instead of making changes.
- `-a` (`--only_actual`) — speeds up the search to only the last relevant version.
- `-k` (`--keep_default_country_trigger`) — keeps trigger like `is_country_type = default` vanilla.
- `-o` (`--also_old`) — Beta: some pre 2.3 stuff. 
- `-input` (`--mod_path`) — path to the mod directory
- `-output` (`--mod_outpath`) — (optional) output path for the updated

These can be set directly in the script or passed as arguments when launching.

### ⌨️ Example 
 ```bash
py modupdater-v4.0.py -a 1 -m 1 -input "c:\\Users\\User\\Documents\\Paradox Interactive\\Stellaris\\mod\\ADeadlyTempest"
```
Note: To use <b>double backslashes</b> or <b>forward slashes</b> for the path strings you are passing as arguments (on Windows).
Or just use: ```py modupdater-v4.0.py``` (if same folder)

## 📄 License

This project is licensed under the terms of the [GNU General Public License version 3 (GPLv3)](https://www.gnu.org/licenses/gpl-3.0.html).

## ☕ Support This Project

If you find this tool helpful, consider supporting development:

- [Buy me a coffee on Ko-fi](https://ko-fi.com/f1r3pr1nc3)
- [Donate via PayPal](https://www.paypal.me/supportfireprinc)
