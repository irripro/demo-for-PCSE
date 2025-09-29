@echo off

REM 批处理文件，用于捕获Python脚本的所有输出

REM 设置UTF-8编码
chcp 65001 >nul

REM 运行测试脚本并将输出重定向到日志文件
echo 正在运行simple_weather_provider_test.py...
python simple_weather_provider_test.py > output.log 2>&1

REM 检查脚本执行状态
if %errorlevel% equ 0 (
    echo 脚本执行成功
) else (
    echo 脚本执行失败，错误代码: %errorlevel%
)

REM 显示日志文件内容
echo.
echo --- 输出日志内容 --- 
type output.log
echo.
echo --------------------

REM 暂停以便查看输出
pause