#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""从NASA POWER获取天气数据并生成符合ExcelWeatherDataProvider要求的Excel文件

这个脚本可以从NASA POWER API获取指定经纬度的气象数据，并将其转换为
符合PCSE库中ExcelWeatherDataProvider要求格式的Excel文件。"""

import os
import sys
import argparse
from datetime import datetime

import pandas as pd
import logging
# 导入必要的库
from openpyxl import Workbook
from openpyxl.styles import Font

# 导入PCSE的NASAPowerWeatherDataProvider
try:
    from pcse.input import NASAPowerWeatherDataProvider
    print("✓ PCSE模块 NASAPowerWeatherDataProvider 导入成功")
except ImportError as e:
    print(f"✗ PCSE模块 NASAPowerWeatherDataProvider 导入失败: {e}")
    print(f"请确保已在虚拟环境中安装PCSE: pip install pcse>=5.5.0")
    sys.exit(1)

# 设置默认参数
DEFAULT_ANGSTROM_A = 0.177639701
DEFAULT_ANGSTROM_B = 0.570986696
DEFAULT_HAS_SUNSHINE = False
NO_DATA_VALUE = -999.0
SITE_ROW = 9  # ExcelWeatherDataProvider直接使用9作为行号

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('nasa_to_excel_simple.log')
    ]
)
logger = logging.getLogger(__name__)


def get_nasa_weather_data(latitude, longitude, force_update=True, excel_path=None):
    """从NASA POWER获取天气数据，并可选择保存为Excel文件"""
    logger.info(f"从NASA POWER获取天气数据，经纬度: {latitude}, {longitude}")
    
    try:
        # 创建NASAPowerWeatherDataProvider实例
        weather = NASAPowerWeatherDataProvider(latitude, longitude, force_update=force_update)
        # weather = NASAPowerWeatherDataProvider(latitude, longitude, force_update=True)
        # df_weather = pd.DataFrame(weather.export())

        # r = pd.date_range(start=df_weather.DAY.min(), end=df_weather.DAY.max())
        # full_range_weather = df_weather.set_index('DAY').reindex(r).rename_axis('DAY').reset_index()
        # filled_weather = full_range_weather.fillna(method='ffill', axis=0)
        # weather._make_WeatherDataContainers(filled_weather.to_dict(orient="records"))
    
        # self.NASA_start_year = weather.first_date.year+1
        # self.NASA_last_year = weather.last_date.year-1
        # self.weather = weather
        # 获取数据
        data = weather.export()
        if not data or len(data) == 0:
            raise ValueError("从NASA获取的天气数据为空")
            
        # 转换为DataFrame
        df = pd.DataFrame(data)
        
        # 获取日期范围
        first_date = df['DAY'].iloc[0] if not df.empty else None
        last_date = df['DAY'].iloc[-1] if not df.empty else None
        print(first_date, last_date)
        logger.info(f"成功获取NASA天气数据，包含 {len(df)} 条记录")
        logger.info(f"日期范围: {first_date.strftime('%Y-%m-%d')} 到 {last_date.strftime('%Y-%m-%d')}")
        
        # 如果提供了保存路径，则保存为Excel文件
        if excel_path:
            try:
                df.to_excel(excel_path, index=False)
                logger.info(f"天气数据已成功保存到Excel文件: {excel_path}")
            except Exception as e:
                logger.error(f"保存Excel文件失败: {str(e)}")
        
        return weather, first_date, last_date
        
    except Exception as e:
        logger.error(f"获取NASA天气数据时出错: {str(e)}")
        raise


def create_excel_file(data, file_path, latitude, longitude, elevation=10):
    """创建符合ExcelWeatherDataProvider要求的Excel文件"""
    logger.info(f"开始创建Excel文件: {file_path}")
    
    # 创建工作簿
    wb = Workbook()
    sheet = wb.active
    sheet.title = "Weather Data"
    
    # 设置表头信息
    sheet["B2"] = "China"  # Country (B2)
    sheet["B3"] = f"Station_{latitude:.2f}N_{longitude:.2f}E"  # Station (B3)
    sheet["B4"] = "NASA POWER weather data"  # Description (B4)
    sheet["B5"] = "NASA POWER API"  # Source (B5)
    sheet["B6"] = "nasa_power@example.com"  # Contact (B6)
    sheet["B7"] = NO_DATA_VALUE  # NODATA (B7)
    
    # 添加表头标签
    sheet["A2"] = "Country:"
    sheet["A3"] = "Station:"
    sheet["A4"] = "Description:"
    sheet["A5"] = "Source:"
    sheet["A6"] = "Contact:"
    sheet["A7"] = "NODATA:"
    
    # 设置表头标题样式
    header_font = Font(bold=True)
    for cell in ['A2', 'A3', 'A4', 'A5', 'A6', 'A7']:
        sheet[cell].font = header_font
    
    # 设置站点信息
    sheet["A9"] = longitude  # 经度 (A9)
    sheet["B9"] = latitude  # 纬度 (B9)
    sheet["C9"] = elevation  # 海拔 (C9)
    sheet["D9"] = DEFAULT_ANGSTROM_A  # Angstrom A值 (D9)
    sheet["E9"] = DEFAULT_ANGSTROM_B  # Angstrom B值 (E9)
    sheet["F9"] = DEFAULT_HAS_SUNSHINE  # 是否有日照数据 (F9)
    
    # 添加列标题
    label_row = 12  # 标签行，对应Excel第13行
    sheet["A13"] = "DAY"
    sheet["B13"] = "TMAX"
    sheet["C13"] = "TMIN"
    sheet["D13"] = "IRRAD"
    sheet["E13"] = "VAP"
    sheet["F13"] = "WIND"
    sheet["G13"] = "RAIN"
    sheet["H13"] = "SNOWDEPTH"
    
    # 为标签行设置粗体
    for cell in ["A13", "B13", "C13", "D13", "E13", "F13", "G13", "H13"]:
        sheet[cell].font = header_font
    
    # 填充天气数据
    data_start_row = label_row + 2  # 数据开始行（第14行）
    
    # 检查数据类型并适当处理
    if isinstance(data, pd.DataFrame):
        # 如果数据是DataFrame格式
        for i, row in data.iterrows():
            current_row = data_start_row + i
            
            # 写入日期 - 使用Excel兼容的字符串格式
            date_value = row['DAY']
            if isinstance(date_value, datetime):
                # 使用ExcelWeatherDataProvider兼容的日期格式
                sheet[f"A{current_row}"] = date_value.strftime("%Y-%m-%d")
            else:
                # 确保日期是字符串格式
                sheet[f"A{current_row}"] = str(date_value)
            
            # 写入其他气象数据
            sheet[f"B{current_row}"] = row.get('TMAX', NO_DATA_VALUE)  # 最高温度
            sheet[f"C{current_row}"] = row.get('TMIN', NO_DATA_VALUE)  # 最低温度
            sheet[f"D{current_row}"] = row.get('IRRAD', NO_DATA_VALUE) # 辐射
            sheet[f"E{current_row}"] = row.get('VAP', NO_DATA_VALUE)  # 蒸汽压
            sheet[f"F{current_row}"] = row.get('WIND', NO_DATA_VALUE)  # 风速
            sheet[f"G{current_row}"] = row.get('RAIN', NO_DATA_VALUE)  # 降雨量
            sheet[f"H{current_row}"] = row.get('SNOWDEPTH', 0)  # 雪深（默认为0）
    elif isinstance(data, list) and data and isinstance(data[0], dict):
        # 如果数据是字典列表格式
        for i, record in enumerate(data):
            current_row = data_start_row + i
            
            # 写入日期 - 使用Excel兼容的字符串格式
            date_value = record['DAY']
            if isinstance(date_value, datetime):
                # 使用ExcelWeatherDataProvider兼容的日期格式
                sheet[f"A{current_row}"] = date_value.strftime("%Y-%m-%d")
            else:
                # 确保日期是字符串格式
                sheet[f"A{current_row}"] = str(date_value)
            
            # 写入其他气象数据
            sheet[f"B{current_row}"] = record.get('TMAX', NO_DATA_VALUE)  # 最高温度
            sheet[f"C{current_row}"] = record.get('TMIN', NO_DATA_VALUE)  # 最低温度
            sheet[f"D{current_row}"] = record.get('IRRAD', NO_DATA_VALUE) # 辐射
            sheet[f"E{current_row}"] = record.get('VAP', NO_DATA_VALUE)  # 蒸汽压
            sheet[f"F{current_row}"] = record.get('WIND', NO_DATA_VALUE)  # 风速
            sheet[f"G{current_row}"] = record.get('RAIN', NO_DATA_VALUE)  # 降雨量
            sheet[f"H{current_row}"] = record.get('SNOWDEPTH', 0)  # 雪深（默认为0）
    else:
        logger.error(f"不支持的数据格式: {type(data)}")
        raise ValueError(f"不支持的数据格式: {type(data)}")
    
    # 确保目录存在
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # 保存文件
    wb.save(file_path)
    logger.info(f"Excel文件已成功保存: {file_path}")
    
    return file_path

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='从NASA POWER获取天气数据并生成Excel文件'
    )
    
    parser.add_argument('--latitude', type=float, default=39.9042,
                        help='纬度 (默认: 39.9042)')
    parser.add_argument('--longitude', type=float, default=116.4074,
                        help='经度 (默认: 116.4074)')
    parser.add_argument('--output', type=str, default=None,
                        help='输出Excel文件路径')
    parser.add_argument('--elevation', type=float, default=10,
                        help='海拔高度 (默认: 10米)')
    parser.add_argument('--force-update', action='store_true',
                        help='强制更新数据，不使用缓存')
    
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_arguments()
    
    # 如果未指定输出文件，生成默认文件名
    if args.output is None:
        lat_str = f"{args.latitude:.2f}".replace('-', 'neg')
        lon_str = f"{args.longitude:.2f}".replace('-', 'neg')
        current_year = datetime.now().year
        default_filename = f"nasa_weather_{lat_str}_{lon_str}_{current_year}.xlsx"
        default_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "data", "meteo", default_filename)
        args.output = default_path
    
    try:
        # 获取NASA数据
        print('Update=',args.force_update)
        weather_provider, first_date, last_date = get_nasa_weather_data(
            args.latitude, args.longitude, args.force_update
        )
        
        # 从weather_provider获取实际的数据
        data = weather_provider.export()
        if not data or len(data) == 0:
            raise ValueError("从NASA获取的数据为空")
        
        # 转换为DataFrame格式
        if not isinstance(data, pd.DataFrame):
            data = pd.DataFrame(data)
        
        # 创建Excel文件
        excel_file = create_excel_file(
            data, args.output, args.latitude, args.longitude, args.elevation
        )
        
        # 输出结果摘要
        print(f"\n===== 处理完成！=====")
        print(f"- 经纬度: {args.latitude}, {args.longitude}")
        print(f"- 日期范围: {first_date.strftime('%Y-%m-%d')} 到 {last_date.strftime('%Y-%m-%d')}")
        print(f"- 数据记录数: {len(data)}")
        print(f"- 输出文件: {excel_file}")
        print(f"\n✓ 成功生成符合ExcelWeatherDataProvider格式要求的Excel文件！")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ 错误: {str(e)}")
        print("请查看日志文件(nasa_to_excel_simple.log)获取详细信息")
        return 1

if __name__ == "__main__":
    sys.exit(main())