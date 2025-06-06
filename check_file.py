# check_file.py
import os
from pathlib import Path
import sys

print(f"Python version: {sys.version}")
print(f"Current Working Directory: {os.getcwd()}")

target_filename_literal = "openapi.json" # Our reference string

print(f"\nTarget filename literal: '{target_filename_literal}', repr: {repr(target_filename_literal)}, length: {len(target_filename_literal)}")
for i, char_code in enumerate(target_filename_literal.encode('utf-8')):
    # Handle potential IndexError if char is multi-byte and target_filename_literal[i] is used for display
    try:
        char_display = target_filename_literal[i]
    except IndexError:
        char_display = '?' # Fallback for display if multi-byte char causes index issue with simple indexing
    print(f"  Literal char {i} ('{char_display}'): UTF-8 code {char_code:02x} (dec {char_code})")


print("\n--- Detailed Listing & Comparison (os.listdir) ---")
found_it = False
try:
    files_in_cwd = os.listdir(".")
    print("Files found by os.listdir(.):\n")
    for f_name_from_os in files_in_cwd:
        print(f"Comparing with OS filename: '{f_name_from_os}', repr: {repr(f_name_from_os)}, length: {len(f_name_from_os)}")
        for i, char_code in enumerate(f_name_from_os.encode('utf-8')):
            try:
                char_display_os = f_name_from_os[i]
            except IndexError:
                char_display_os = '?'
            print(f"  OS char {i} ('{char_display_os}'): UTF-8 code {char_code:02x} (dec {char_code})")

        if f_name_from_os == target_filename_literal:
            print("  ==> EXACT STRING MATCH FOUND!\n")
            found_it = True
            # If exact match, pathlib should work with this f_name_from_os
            path_obj_from_os_name = Path(f_name_from_os)
            print(f"    Pathlib test with '{f_name_from_os}':")
            print(f"      Exists: {path_obj_from_os_name.exists()}")
            print(f"      Is file: {path_obj_from_os_name.is_file()}")
            if path_obj_from_os_name.is_file():
                try:
                    content = path_obj_from_os_name.read_text(encoding='utf-8')
                    print(f"      Successfully read. Size: {len(content)} chars.")
                except Exception as e_read:
                    print(f"      Error reading: {e_read}")
            print("-" * 20)

        elif f_name_from_os.lower() == target_filename_literal.lower():
            print("  ==> Case-insensitive match, but not exact string match.\n")
            print("-" * 20)
        else:
            print("  --> No match.\n")
            print("-" * 20)


    if not found_it:
        print(f"\nSTILL NO EXACT MATCH for '{target_filename_literal}' (repr: {repr(target_filename_literal)}, length: {len(target_filename_literal)}) after detailed char-by-char comparison idea.")
        print("This strongly suggests a subtle difference in the filename string (e.g., hidden characters, different Unicode representations of similar looking characters).")

except Exception as e:
    print(f"Error listing directory: {e}")

# Final pathlib check with the literal string, as datamodel-codegen would use
print(f"\n--- Final Pathlib check with literal string '{target_filename_literal}' ---")
final_path_obj = Path(target_filename_literal)
print(f"Path('{target_filename_literal}').exists(): {final_path_obj.exists()}")
print(f"Path('{target_filename_literal}').is_file(): {final_path_obj.is_file()}")