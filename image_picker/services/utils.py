from pathlib import Path


def is_file_marked(filename:str|Path) -> bool:
    file = filename if type(filename) == Path else Path(filename)
    return file.stem.endswith("_")    


# TODO deal with js time format and python
def get_mod_time(filename:str|Path) -> float:
        file = filename if type(filename) == Path else Path(filename)
        return file.stat().st_mtime * 1000