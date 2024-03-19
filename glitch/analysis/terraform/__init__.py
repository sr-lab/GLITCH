import os

__all__ = []

for file in os.listdir(os.path.dirname(__file__)):
    if file.endswith(".py") and file != "__init__.py":
        __all__.append(file[:-3])
