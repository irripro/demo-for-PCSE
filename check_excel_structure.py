#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查Excel天气数据文件结构是否符合ExcelWeatherDataProvider要求"""

import os
import sys
from openpyxl import load_workbook


class ExcelStructureChecker:
    """Excel文件结构检查器"""
    
    def __init__(self, file_path):
        """初始化检查器"""
        self.file_path = file_path
        self.workbook = None
        self.worksheet = None
        
    def load_file(self):
        """加载Excel文件"""
        print(f"正在加载Excel文件: {self.file_path}")
        
        # 检查文件是否存在
        if not os.path.exists(self.file_path):
            print(f"✗ 错误: 文件不存在: {self.file_path}")
            return False
        
        # 检查文件大小
        file_size = os.path.getsize(self.file_path)
        print(f"文件大小: {file_size} 字节")
        
        # 加载文件
        try:
            self.workbook = load_workbook(self.file_path)
            print(f"工作簿包含 {len(self.workbook.sheetnames)} 个工作表")
            print(f"工作表名称: {', '.join(self.workbook.sheetnames)}")
            
            # 使用第一个工作表
            self.worksheet = self.workbook.active
            print(f"当前活动工作表: {self.worksheet.title}")
            
            return True
        except Exception as e:
            print(f"✗ 错误: 加载文件失败: {str(e)}")
            return False
    
    def check_basic_cells(self):
        """检查基本单元格的内容"""
        if not self.worksheet:
            print("✗ 错误: 工作表未加载")
            return False
        
        print("\n===== 检查基本单元格内容 ====")
        
        # 检查一些简单的单元格
        cells_to_check = ["A1", "A2", "A3", "A4", "B2", "B3", "B4", "B5", "B6", "B7", 
                         "A9", "B9", "C9", "D9", "E9", "F9", 
                         "A13", "B13", "C13", "D13", "E13", "F13", "G13", "H13"]
        
        for cell in cells_to_check:
            try:
                value = self.worksheet[cell].value
                print(f"{cell}: {value} (类型: {type(value) if value is not None else 'None'})")
            except Exception as e:
                print(f"{cell}: 无法访问 ({str(e)})")
        
        # 检查是否有数据行
        print("\n===== 检查数据行 ====")
        data_found = False
        for row in range(1, 20):  # 只检查前20行
            cell_a = f"A{row}"
            try:
                value = self.worksheet[cell_a].value
                if value is not None:
                    print(f"行 {row}, 单元格 {cell_a}: {value}")
                    data_found = True
            except Exception as e:
                print(f"行 {row}, 单元格 {cell_a}: 无法访问 ({str(e)})")
        
        if not data_found:
            print("没有找到任何非空单元格")
        
        return True
    
    def check_structure(self):
        """检查文件结构是否符合要求"""
        print("\n===== 检查文件结构 ====")
        
        # 这里是原始的结构检查逻辑
        print("\n检查表头信息 (B2-B7):")
        print(f"  Country (B2): {self.get_cell_value('B2')}")
        print(f"  Station (B3): {self.get_cell_value('B3')}")
        print(f"  Description (B4): {self.get_cell_value('B4')}")
        print(f"  Source (B5): {self.get_cell_value('B5')}")
        print(f"  Contact (B6): {self.get_cell_value('B6')}")
        print(f"  NODATA (B7): {self.get_cell_value('B7')}")
        
        print("\n检查站点信息 (A9-F9):")
        print(f"  经度 (Longitude) (A9): {self.get_cell_value('A9')}")
        print(f"  纬度 (Latitude) (B9): {self.get_cell_value('B9')}")
        print(f"  海拔 (Elevation) (C9): {self.get_cell_value('C9')}")
        print(f"  Angstrom A (D9): {self.get_cell_value('D9')}")
        print(f"  Angstrom B (E9): {self.get_cell_value('E9')}")
        print(f"  Has Sunshine Data (F9): {self.get_cell_value('F9')}")
        
        print("\n检查列标题 (第13行):")
        headers = [
            ("A13", "DAY"),
            ("B13", "TMAX"),
            ("C13", "TMIN"),
            ("D13", "IRRAD"),
            ("E13", "VAP"),
            ("F13", "WIND"),
            ("G13", "RAIN"),
            ("H13", "SNOWDEPTH")
        ]
        
        for cell, header in headers:
            value = self.get_cell_value(cell)
            status = "✓" if value == header else "✗"
            print(f"  {status} {header} ({cell}): {value}")
        
        # 检查数据行数
        print("\n  检查数据行数...")
        data_rows = 0
        for row in range(14, 200):  # 检查前200行数据
            if self.get_cell_value(f"A{row}") is not None:
                data_rows += 1
        print(f"  找到 {data_rows} 行数据")
        
        return True
    
    def get_cell_value(self, cell):
        """获取单元格的值"""
        try:
            return self.worksheet[cell].value
        except:
            return None
    
    def run_checks(self):
        """运行所有检查"""
        print(f"\n===== 检查文件: {self.file_path} ====")
        
        # 加载文件
        if not self.load_file():
            return False
        
        # 检查基本单元格
        self.check_basic_cells()
        
        # 检查结构
        self.check_structure()
        
        print("\n✓ 结构检查完成!")
        return True


def main():
    """主函数"""
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("用法: python check_excel_structure.py <excel_file_path>")
        return 1
    
    # 获取文件路径
    file_path = sys.argv[1]
    
    # 创建检查器并运行检查
    checker = ExcelStructureChecker(file_path)
    success = checker.run_checks()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())