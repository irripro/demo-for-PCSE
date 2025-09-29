import subprocess
import sys
import os

# 确保中文显示正常
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def capture_script_output(script_path):
    """运行Python脚本并捕获其输出"""
    try:
        print(f"正在运行脚本: {script_path}")
        
        # 使用subprocess运行脚本
        process = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        # 获取输出和错误
        stdout, stderr = process.communicate()
        
        # 打印结果
        print(f"\n=== 脚本输出 ===")
        if stdout:
            print(stdout)
        else:
            print("没有标准输出")
        
        print(f"\n=== 错误输出 ===")
        if stderr:
            print(stderr)
        else:
            print("没有错误输出")
        
        print(f"\n脚本退出代码: {process.returncode}")
        
    except Exception as e:
        print(f"捕获输出过程中出错: {e}")

if __name__ == "__main__":
    # 运行简单的天气提供者测试脚本
    capture_script_output("simple_weather_provider_test.py")
    
    # 也可以尝试直接运行原始的测试脚本
    print("\n\n=== 直接测试get_weather_provider方法 ===")
    try:
        # 导入必要的模块
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from app import CropGrowthSimulator
        
        # 创建模拟器实例
        simulator = CropGrowthSimulator()
        
        # 直接测试get_weather_provider方法
        latitude, longitude = 39.9042, 116.4074
        print(f"调用get_weather_provider({latitude}, {longitude}, False)")
        
        # 捕获可能的异常
        try:
            result = simulator.get_weather_provider(latitude, longitude, False)
            print(f"返回值类型: {type(result).__name__}")
            print(f"是否为元组: {isinstance(result, tuple)}")
        except Exception as e:
            print(f"调用get_weather_provider时出错: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"导入或初始化过程中出错: {e}")
        import traceback
        traceback.print_exc()