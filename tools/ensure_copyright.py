# endcord - Copyright (C) 2025-2026 SparkLost. All Rights Reserved.
# Source-available under the Endcord License. See LICENSE for terms.
# Redistribution of modified versions is not permitted.

import os
from datetime import datetime

PROJECT_NAME = "endcord"
AUTHOR = "SparkLost"
START_YEAR = "2025"
CURRENT_YEAR = str(datetime.now().year)
HEADER_LINE = f"# {PROJECT_NAME} - Copyright (C) {START_YEAR}-{CURRENT_YEAR} {AUTHOR}. All Rights Reserved.\n"
HEADER_FULL = f"""{HEADER_LINE.strip()}
# Source-available under the Endcord License. See LICENSE for terms.
# Redistribution of modified versions is not permitted.

"""
extensions_white = [".py", ".pyx"]
extensions_black = [".pyc", "pb2.py", "endcord/wide_ranges.py", "xterm256.py", "setup.py", "acs.py"]


def get_file_list():
    """Get list of all files with extensions from extensions_white"""
    file_list = []
    for path, subdirs, files in os.walk(os.getcwd()):
        subdirs[:] = [d for d in subdirs if not d.startswith(".")]   # skip hidden dirs
        for name in files:
            file_path = os.path.join(path, name)
            if any(name.endswith(x) for x in extensions_white) and not name.startswith("."):
                if not any(file_path.endswith(x) for x in extensions_black):
                    file_list.append(file_path)
    return file_list


def main():
    """Ensure there is copyright notice in all py files"""
    print("Running ensure copyright script")
    file_list = get_file_list()
    for path in file_list:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        insert_index = 0
        header_exists = False
        header_index = None
        updated = False

        # skip shebang and encoding line
        if lines and lines[0].startswith("#!"):
            insert_index += 1
        if len(lines) > insert_index and "coding" in lines[insert_index]:
            insert_index += 1

        # check for existing header
        for i in range(min(10, len(lines))):
            if "Copyright (C)" in lines[i] and AUTHOR in lines[i]:
                header_exists = True
                header_index = i
                break

        # update file
        if header_exists:
            if lines[header_index] != HEADER_LINE:
                lines[header_index] = HEADER_LINE
                updated = True
        else:
            lines.insert(insert_index, HEADER_FULL)
            updated = True
        if updated:
            print("Header updated in:", path)
            with open(path, "w", encoding="utf-8") as f:
                f.writelines(lines)


if __name__ == "__main__":
    main()
