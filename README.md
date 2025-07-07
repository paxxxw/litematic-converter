# ⚡ Litematic Converter

A user-friendly tool for converting `.litematic` files from Minecraft's Litematica mod to other formats:
- **`.bp`** (Axiom Blueprint files)
- **`.schem`** (WorldEdit Schematic files)

## 🚀 Quick Start

### 1. Download and Setup

1. **Download** or **Clone** this repository
2. **Install Python** (3.7 or newer) from [python.org](https://python.org/downloads/)
3. **Install dependencies** by opening a terminal/command prompt in the project folder and running:
   ```
   pip install -r requirements.txt
   ```

4. **Verify installation** (optional but recommended):
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

**Command line for .litematic to .bp (single files only):**
```
python litematic_to_bp_converter.py mycastle.litematic mycastle.bp
```

**Command line for .litematic to .schem (single files only):**
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
