"""Double-clickable launcher for the GUI.

Place this file in the `src` folder. Double-clicking it on Windows will
run the GUI without opening a console window (when `.pyw` files are
associated with `pythonw.exe`).
"""
from main import main


if __name__ == "__main__":
    main()
