import sys
import subprocess

# 检查app.py的语法
result = subprocess.run(['python', '-m', 'py_compile', 'app.py'], capture_output=True, text=True)

if result.returncode == 0:
    print("app.py的语法正确！")
else:
    print(f"app.py语法错误:\n{result.stderr}")