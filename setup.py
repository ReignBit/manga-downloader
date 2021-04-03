from cx_Freeze import setup, Executable

base = None    

executables = [Executable("manga-dl.py", base=base)]

packages = ["idna", "requests", "curses", "os", "re", "math", "threading", "argparse"]
options = {
    'build_exe': {    
        'packages':packages,
    },    
}

setup(
    name = "manga-dl",
    options = options,
    version = "1.0.0",
    description = 'Quickly download manga from Manganelo',
    executables = executables
)