#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""模拟ExcelWeatherDataProvider的读取逻辑，诊断KeyError: None问题"""

import os
import sys
import openpyxl
from datetime import datetime

# 添加虚拟环境的site-packages目录到sys.path
site_packages = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.venv', 'Lib', 'site-packages')
sys.path.append(site_packages)


def diagnose_excel_file(file_path):
    """模拟ExcelWeatherDataProvider的读取逻辑，诊断问题"""
    print(f"===== 诊断Excel文件: {file_path} =====")
    
    # 1. 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"✗ 文件不存在: {file_path}")
        return 1
    
    # 2. 尝试加载Excel文件
    try:
        wb = openpyxl.load_workbook(file_path, data_only=True)
        ws = wb.active
        print("✓ 成功加载Excel文件")
    except Exception as e:
        print(f"✗ 加载Excel文件失败: {str(e)}")
        return 1
    
    # 3. 模拟ExcelWeatherDataProvider的读取逻辑
    try:
        print("\n===== 模拟ExcelWeatherDataProvider读取过程 =====")
        
        # 模拟obs_conversions字典 - 从检查结果中我们知道它包含哪些键
        obs_conversions = {
            'TMAX': lambda x: x,
            'TMIN': lambda x: x,
            'IRRAD': lambda x: x,
            'VAP': lambda x: x,
            'WIND': lambda x: x,
            'RAIN': lambda x: x,
            'SNOWDEPTH': lambda x: x
        }
        print(f"模拟的obs_conversions字典包含的键: {list(obs_conversions.keys())}")
        
        # 查找数据标签行
        print("\n1. 查找数据标签行...")
        header_row = None
        header_columns = []
        
        # 扫描可能的数据标签行（10-20行）
        for row in range(10, 21):
            potential_labels = []
            has_date = False
            has_valid_labels = False
            
            # 检查前8列
            for col in range(1, 9):
                cell = ws.cell(row=row, column=col)
                value = cell.value
                
                # 只关心非空单元格
                if value is not None:
                    # 转换为字符串并去除首尾空格
                    if isinstance(value, str):
                        value = value.strip().upper()
                    else:
                        value = str(value).strip().upper()
                    
                    potential_labels.append((col, value))
                    
                    # 检查是否包含'DATE'标签
                    if value == 'DATE':
                        has_date = True
                    
                    # 检查是否包含其他有效标签
                    if value in obs_conversions:
                        has_valid_labels = True
            
            # 如果找到'DATE'和至少一个其他有效标签，这可能是数据标签行
            if has_date and has_valid_labels:
                header_row = row
                header_columns = potential_labels
                print(f"✓ 找到数据标签行: 第{row}行")
                print(f"   找到的标签: {[(col, val) for col, val in potential_labels]}")
                break
        
        if header_row is None:
            print("✗ 未找到有效的数据标签行")
            return 1
        
        # 2. 检查数据标签的有效性
        print("\n2. 检查数据标签的有效性...")
        valid_labels = []
        invalid_labels = []
        
        for col, label in header_columns:
            if label == 'DATE':
                valid_labels.append((col, label))
            elif label in obs_conversions:
                valid_labels.append((col, label))
            else:
                invalid_labels.append((col, label))
        
        print(f"   有效标签: {valid_labels}")
        if invalid_labels:
            print(f"   无效标签: {invalid_labels}")
            print(f"   注意: 无效标签可能导致ExcelWeatherDataProvider出错")
        
        # 3. 检查数据行
        print(f"\n3. 检查数据行（从第{header_row + 1}行开始）...")
        data_start_row = header_row + 1
        row_num = data_start_row
        
        # 尝试读取前5行数据
        for _ in range(5):
            if row_num > ws.max_row:
                break
            
            print(f"   第{row_num}行数据:")
            
            # 检查每个有标签的列
            for col, label in header_columns:
                cell = ws.cell(row=row_num, column=col)
                value = cell.value
                
                # 特殊处理DATE列
                if label == 'DATE':
                    date_value = value
                    if isinstance(date_value, datetime):
                        print(f"     列{col} ({label}): 类型=datetime, 值={date_value.strftime('%Y-%m-%d')}")
                    elif isinstance(date_value, str):
                        print(f"     列{col} ({label}): 类型=str, 值='{date_value}'")
                        # 检查字符串格式是否为YYYYMMDD
                        try:
                            parsed_date = datetime.strptime(date_value, '%Y%m%d')
                            print(f"       ✓ 字符串格式有效: {parsed_date.strftime('%Y-%m-%d')}")
                        except ValueError:
                            print(f"       ✗ 字符串格式无效，应为YYYYMMDD")
                    else:
                        print(f"     列{col} ({label}): 类型={type(value).__name__}, 值={value}")
                        print(f"       ✗ 日期类型应为字符串(YYYYMMDD)或datetime对象")
                
                # 处理其他数值列
                else:
                    print(f"     列{col} ({label}): 类型={type(value).__name__}, 值={value}")
                    # 尝试转换为数值
                    try:
                        num_value = float(value) if value is not None else None
                        print(f"       ✓ 可以转换为数值: {num_value}")
                    except (ValueError, TypeError):
                        print(f"       ✗ 无法转换为数值")
                    
                    # 检查标签是否在obs_conversions中
                    if label not in obs_conversions:
                        print(f"       ✗ 标签'{label}'不在obs_conversions字典中")
                    
                    # 模拟ExcelWeatherDataProvider中导致KeyError的代码
                    if label is None:
                        print(f"       ☠️  警告: label为None，这将导致KeyError: None!")
            
            row_num += 1
        
        # 4. 检查是否有隐藏的行或列
        print("\n4. 检查是否有隐藏的行或列...")
        
        # 检查数据标签行和数据开始行是否被隐藏
        if ws.row_dimensions[header_row].hidden:
            print(f"✗ 警告: 数据标签行（第{header_row}行）被隐藏")
        
        if ws.row_dimensions[data_start_row].hidden:
            print(f"✗ 警告: 数据开始行（第{data_start_row}行）被隐藏")
        
        # 检查数据列是否被隐藏
        for col, _ in header_columns:
            col_letter = openpyxl.utils.get_column_letter(col)
            if ws.column_dimensions[col_letter].hidden:
                print(f"✗ 警告: 数据列（{col_letter}列）被隐藏")
        
        print("\n===== 诊断完成 =====")
        print("\n问题分析:")
        
        # 5. 分析可能的问题
        # 检查是否有None标签
        has_none_label = any(label is None for _, label in header_columns)
        if has_none_label:
            print("1. ☠️  严重问题: 数据标签行中存在None值，这将导致KeyError: None!")
        
        # 检查是否有无效标签
        if invalid_labels:
            print("2. ⚠️  警告: 数据标签行中存在obs_conversions字典中没有的标签")
            print(f"   无效标签: {invalid_labels}")
            print(f"   建议: 只使用以下标签: 'DATE' + {list(obs_conversions.keys())}")
        
        # 检查是否有数据类型问题
        print("3. 数据类型检查:")
        print("   - DATE列: 应为YYYYMMDD格式的字符串或datetime对象")
        print("   - 数值列: 应为数字或可转换为数字的字符串")
        
        print("\n建议修复方案:")
        print("1. 确保数据标签行（通常是第12行）只包含以下标签:")
        print(f"   'DATE', 'IRRAD', 'TMIN', 'TMAX', 'VAP', 'WIND', 'RAIN'")
        print("2. 确保所有标签都是大写字母，没有额外的空格")
        print("3. 确保DATE列使用YYYYMMDD格式的字符串")
        print("4. 确保所有数值列都包含有效的数值")
        print("5. 确保没有隐藏的行或列")
        
        return 0
        
    except Exception as e:
        print(f"✗ 诊断过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python diagnose_pcse_provider.py <Excel文件路径>")
        return 1
    
    file_path = sys.argv[1]
    return diagnose_excel_file(file_path)


if __name__ == "__main__":
    sys.exit(main())