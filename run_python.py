# 使用绝对路径运行 Python 脚本
python_exe = r"C:\Users\18268\AppData\Local\Programs\Python\Python39\python.exe"
script_path = r"e:\kimicode\660MWHF\upload_to_github.py"

import subprocess
import sys

result = subprocess.run([python_exe, script_path], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("ERRORS:", result.stderr)
sys.exit(result.returncode)
