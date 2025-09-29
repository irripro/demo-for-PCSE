import os
import sys
import csv
from datetime import datetime

# 用户提供的值
angstromA = 0.177639701
angstromB = 0.570986696
has_sunshine = False

# 定义输出文件路径
output_file = r"e:/pcse_demo/angstrom_results.csv"

print(f"Python版本: {sys.version}")
print(f"当前工作目录: {os.getcwd()}")
print(f"输出文件路径: {os.path.abspath(output_file)}")

# 创建结果数据
results = [
    ['AngstromA', 'AngstromB', 'HasSunshine'],
    [angstromA, angstromB, has_sunshine]
]

# 尝试写入CSV文件（Excel可以直接打开）
try:
    # 确保目录存在
    output_dir = os.path.dirname(output_file)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"创建目录: {output_dir}")
    
    # 写入CSV文件
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerows(results)
    
    print(f"\n成功将结果写入CSV文件: {output_file}")
    print(f"\n计算结果:")
    print(f"AngstromA: {angstromA}")
    print(f"AngstromB: {angstromB}")
    print(f"HasSunshine: {has_sunshine}")
    
    # 显示文件内容确认
    print("\n文件内容:")
    with open(output_file, 'r', encoding='utf-8-sig') as f:
        content = f.read()
        print(content)
        
    print("\n提示: 这个CSV文件可以用Excel打开，您也可以手动将其另存为Excel格式(.xlsx)")

except Exception as e:
    print(f"写入文件时出错: {e}")
    # 如果CSV写入失败，尝试创建一个简单的文本文件
    txt_file = output_file.replace('.csv', '.txt')
    try:
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("AngstromA,AngstromB,HasSunshine\n")
            f.write(f"{angstromA},{angstromB},{has_sunshine}\n")
        print(f"\n已创建文本文件: {txt_file}")
    except Exception as txt_error:
        print(f"创建文本文件时也出错: {txt_error}")
        # 如果所有写入都失败，只显示结果
        print("\n无法创建文件，以下是计算结果:")
        print(f"AngstromA: {angstromA}")
        print(f"AngstromB: {angstromB}")
        print(f"HasSunshine: {has_sunshine}")

print("\n处理完成！")