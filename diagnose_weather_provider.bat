@echo off
REM 批处理文件用于捕获测试脚本的执行信息

REM 设置执行策略为无限制
powershell -Command "Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force"

REM 打印系统信息
echo 开始诊断PCSE环境问题...
echo.
echo 系统信息:
echo 操作系统: %OS%
echo Python版本:
python --version
echo.

REM 检查当前目录内容
echo 当前目录内容:
dir /b

echo.
echo 运行天气提供者测试脚本...
REM 运行测试脚本并捕获输出
python weather_provider_test.py > test_output.log 2>&1

REM 检查测试结果
echo 测试完成，输出内容:
echo.
type test_output.log
echo.
echo 测试执行状态: %ERRORLEVEL%

REM 检查app.py文件是否存在
echo.
echo 检查app.py文件:
if exist app.py (
echo 找到app.py文件
echo 文件大小: %~z1 bytes
echo 最后修改时间: %~t1
echo.
echo 尝试直接导入PCSE模块并检查版本:
powershell -Command "& { try { Import-Module pcse -ErrorAction Stop; Write-Host 'PowerShell成功导入PCSE模块'; } catch { Write-Host 'PowerShell导入PCSE模块失败: $_' } }"
) else (
echo 错误: 未找到app.py文件
)

echo.
echo 诊断完成。按任意键退出...
pause > nul