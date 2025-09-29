import pandas as pd
import os

def check_excel_files():
    # 设置项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    meteo_dir = os.path.join(project_root, "data", "meteo")
    
    # 列出要检查的关键文件
    key_files = ["example_weather.xlsx", "weather_39.90_116.41_2023.xlsx"]
    
    print(f"检查目录: {meteo_dir}")
    
    # 检查每个关键文件
    for file_name in key_files:
        file_path = os.path.join(meteo_dir, file_name)
        print(f"\n===== 检查文件: {file_name} =====")
        
        if os.path.exists(file_path):
            try:
                # 读取Excel文件
                df = pd.read_excel(file_path)
                print(f"文件包含 {len(df)} 行, {len(df.columns)} 列")
                print("\n列名:")
                print(df.columns.tolist())
                
                # 检查Angstrom相关列
                has_angstrom = False
                for col in df.columns:
                    if 'angstrom' in col.lower():
                        has_angstrom = True
                        print(f"\n找到Angstrom相关列: {col}")
                        # 显示该列的前5个值
                        print(f"前5个值: {df[col].head().tolist()}")
                        
                if not has_angstrom:
                    print("\n未找到Angstrom相关列")
                
                # 检查第一行数据的类型
                if len(df) > 0:
                    print("\n第一行数据类型:")
                    for col in df.columns[:5]:  # 只显示前5列的类型
                        value = df[col].iloc[0]
                        print(f"{col}: 值={value}, 类型={type(value)}")
                
            except Exception as e:
                print(f"读取文件时出错: {e}")
        else:
            print(f"文件不存在")
    
    print("\n检查完成")

if __name__ == "__main__":
    check_excel_files()