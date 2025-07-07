# ⚡ Litematic Converter

Convert `.litematic` files from Minecraft's Litematica mod to:
- **`.bp`** (Axiom Blueprint files) 
- **`.schem`** (WorldEdit Schematic files)

## 📥 Get Started

**Option 1: Download Release (Recommended)**
- Go to [Releases](https://github.com/yourusername/litematic-converter/releases)
- Download the latest release
- Extract to a folder

**Option 2: Clone with Git**
- Navigate to, or create, a folder where you want the project
- Open terminal/command prompt there, then run:
```
git clone https://github.com/yourusername/litematic-converter.git
```
- This creates a `litematic-converter` folder in your current location

## 🚀 Quick Start

### 1. Setup

1. **Install Python** (3.7 or newer) from [python.org](https://python.org/downloads/)
   - ⚠️ **Important:** Check "Add Python to PATH" during installation!

2. **Install dependencies:**
   - **First, navigate into the project folder:**
     - **If downloaded:** Extract the ZIP file, then go INSIDE the extracted folder (not just where you extracted it). You should see files like `README.md`, `requirements.txt`, etc.
     - **If cloned:** Go INSIDE the `litematic-converter` folder that was created. You should see files like `README.md`, `requirements.txt`, etc.
   - **Then, open terminal/command prompt from inside that folder**
   - Copy and paste this command in the terminal/command prompt:
   ```
   pip install -r requirements.txt
   ```
   - Press Enter and wait for it to finish

3. **Verify everything works** (optional but recommended):
   ```
   python setup_check.py
   ```

### 2. Start the Application

**GUI (recommended for most users):**
```
python litematic_converter_gui.py
```

GUI Features:
- **File browser** (select one or many files)
- **Batch conversion** (can convert multiple files at once)
- **Smart folder detection** (finds your Minecraft directories automatically)  
- **Progress tracking** with detailed logs
- **Cross-platform** (Windows, macOS, Linux)

**Command line for .litematic → .bp (single files only):**
```
python litematic_to_bp_converter.py mycastle.litematic mycastle.bp
```

**Command line for .litematic → .schem (single files only):**
```
python litematic_to_schem_advanced.py mycastle.litematic mycastle.schem
```
*Note: .litematic files and output go in the project folder ONLY if using the command line*

## ✨ What These Tools Can Do

**Blueprint Converter (.litematic → .bp):**
- Creates Axiom-compatible files with 3D thumbnails
- Preserves all block properties and tile entities  
- Supports banners with custom patterns

**Schematic Converter (.litematic → .schem):**
- Modern WorldEdit format support
- Handles multiple regions and entities
- Preserves metadata and banner patterns

**Important:** Build names in Axiom match your .litematic filename (without extension)

## 🎯 Supported Formats

### Input Formats
- **.litematic** - Litematica mod schematic files

### Output Formats
- **.bp** - Axiom Blueprint files (with 3D thumbnails)
- **.schem** - WorldEdit/WorldGuard schematic files

## 🐛 Troubleshooting

### Common Issues

- **"ModuleNotFoundError" when running**
  - **Solution:** Install dependencies
  ```
  pip install -r requirements.txt
  ```

- **"Permission denied" errors**
  - **Solutions:**
    - Run as administrator (Windows) or with sudo (Mac/Linux)
    - Or choose a different output directory

- **GUI doesn't open**
  - **Solutions:** 
      - Ensure tkinter is installed (usually comes with Python)
      - On Ubuntu/Debian:
      ```bash
      sudo apt-get install python3-tk
      ```

- **Conversion fails**
  - **Solutions:**
    - Check that your `.litematic` file isn't corrupted
    - Ensure you have write permissions to the output directory
    - Try converting to a different location

- **"File not found" or "No such file or directory"**
  - **Solutions:**
    - Ensure the `.litematic` file path doesn't contain special characters (like `&`, `%`, or unicode symbols)
    - Try moving the file to a simpler folder path (e.g., Desktop)
    - Check that the filename doesn't have extra spaces at the beginning or end

- **Conversion takes extremely long or appears frozen**
  - **Solutions:**
    - Very large builds can take up to a minute (depending on PC hardware)
    - Check Task Manager/Activity Monitor - if CPU usage is high, it's still working
    - Try converting a smaller section first to test if the file is valid

## 🤝 Contributing

Issues and pull requests are welcome! Please:
1. Check existing issues before creating new ones
2. Provide sample `.litematic` files for bug reports
3. Include error messages and Python version info

## 📄 License

This project is open source. Feel free to use, modify, and distribute.

---

## 💡 Need Help?

1. **Read this README thoroughly**
2. **Check the troubleshooting section**
3. **Try the command line versions** if GUI has issues
4. **Create an issue** with details about your problem
