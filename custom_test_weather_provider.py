#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自定义的测试天气数据提供器，用于替代不存在的TestWeatherDataProvider
"""

import os
import sys
from datetime import datetime, timedelta

# 添加虚拟环境的site-packages目录到sys.path
site_packages = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.venv', 'Lib', 'site-packages')
sys.path.append(site_packages)

# 导入必要的PCSE模块
from pcse.base import WeatherDataContainer
from pcse.base import WeatherDataProvider

class CustomTestWeatherDataProvider(WeatherDataProvider):
    """
    自定义的测试天气数据提供器
    提供模拟的天气数据，用于测试和开发目的
    继承自PCSE的WeatherDataProvider基类
    """
    
    def __init__(self, start_date=None, days=365, year=2020):
        """
        初始化测试天气数据提供器
        
        Args:
            start_date: 开始日期，如果为None则使用指定年份的1月1日
            days: 生成的天数
            year: 指定的年份，如果start_date为None，则使用该年份的1月1日作为开始日期
        """
        # 调用父类构造函数
        super().__init__()
        
        # 如果没有提供开始日期，默认使用指定年份的1月1日
        if start_date is None:
            # 默认使用2020年1月1日作为开始日期，因为测试脚本使用的是2020年的数据
            start_date = datetime(year, 1, 1)
        
        # 设置基本参数
        self.latitude = 52.0  # 示例纬度（荷兰）
        self.longitude = 5.0  # 示例经度
        self.elevation = 10.0  # 示例海拔高度
        
        # 生成测试天气数据
        self._store = {}
        self._generate_test_data(start_date, days)
        
        # 保存日期范围（使用不同的变量名，避免与父类的属性冲突）
        if self._store:
            self._first_date = min(self._store.keys())
            self._last_date = max(self._store.keys())
        else:
            self._first_date = self._last_date = start_date
    
    def _generate_test_data(self, start_date, days):
        """生成测试天气数据"""
        # 打印生成数据的信息
        print(f"生成测试天气数据: 从 {start_date} 开始，共 {days} 天")
        
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            
            # 特别标记我们关心的日期（2020-04-09）
            is_target_date = False
            if current_date.year == 2020 and current_date.month == 4 and current_date.day == 9:
                is_target_date = True
                print(f"✓ 正在生成目标日期 {current_date} 的数据")
            
            # 根据月份生成不同的天气模式
            month = current_date.month
            
            # 生成季节相关的温度（摄氏度）
            if month in [12, 1, 2]:  # 冬季
                tmin = -2 + (i % 5) - 2  # -4 到 2
                tmax = 5 + (i % 5) - 2  # 3 到 8
            elif month in [3, 4, 5]:  # 春季
                tmin = 5 + (i % 6) - 3  # 2 到 8
                tmax = 15 + (i % 6) - 3  # 12 到 18
            elif month in [6, 7, 8]:  # 夏季
                tmin = 12 + (i % 7) - 3  # 9 到 16
                tmax = 22 + (i % 7) - 3  # 19 到 26
            else:  # 秋季
                tmin = 7 + (i % 6) - 3  # 4 到 10
                tmax = 17 + (i % 6) - 3  # 14 到 20
            
            # 生成其他天气参数
            day_of_year = current_date.timetuple().tm_yday
            
            # 太阳辐射 (J/m²/day) - 季节性变化
            base_rad = 2000000  # 基础辐射
            seasonal_factor = 1 + 0.6 * (month - 1) if month <= 7 else 1 + 0.6 * (13 - month)
            daily_variation = (i % 7 - 3) * 100000  # 日变化
            irrad = base_rad * seasonal_factor + daily_variation
            
            # 水汽压 (hPa)
            vap = 10 + (tmax - 10) * 0.8
            
            # 风速 (m/s)
            wind = 2 + (i % 5) / 2
            
            # 降雨量 (cm) - 随机但有季节性模式
            if month in [4, 5, 6, 7]:  # 少雨季节
                rain = 0.1 if i % 10 == 0 else 0  # 10% 概率下雨
            elif month in [10, 11, 12]:  # 多雨季节
                rain = 0.3 if i % 5 == 0 else 0  # 20% 概率下雨
            else:  # 其他季节
                rain = 0.2 if i % 7 == 0 else 0  # 14% 概率下雨
            
            # 创建天气数据字典 - 只包含基本必需的字段
            weather_data = {
                'DAY': current_date,
                'IRRAD': irrad,
                'TMIN': tmin,
                'TMAX': tmax,
                'VAP': vap,
                'WIND': wind,
                'RAIN': rain
            }
            
            # 创建WeatherDataContainer
            wdc = WeatherDataContainer(
                LAT=self.latitude,
                LON=self.longitude,
                ELEV=self.elevation,
                **weather_data
            )
            
            # 存储数据
            self._store[current_date] = wdc
            
            # 如果是目标日期，打印详细信息
            if is_target_date:
                print(f"  目标日期数据已存储: {current_date}")
                print(f"  存储的键数量: {len(self._store)}")
                print(f"  前5个键: {list(self._store.keys())[:5]}")
    
    def __getitem__(self, date):
        """按日期获取天气数据"""
        if date in self._store:
            return self._store[date]
        else:
            return None
    
    def __contains__(self, date):
        """检查是否包含某日期的天气数据"""
        return date in self._store
    
    def __iter__(self):
        """迭代所有日期"""
        return iter(sorted(self._store.keys()))
    
    def __len__(self):
        """返回数据记录数"""
        return len(self._store)
    
    def keys(self):
        """返回所有日期的列表"""
        return sorted(self._store.keys())
    
    def get_site_parameters(self):
        """获取站点参数"""
        return {
            'LAT': self.latitude,
            'LON': self.longitude,
            'ELEV': self.elevation
        }
    
    # 重写父类的属性获取方法
    @property
    def first_date(self):
        return self._first_date
    
    @property
    def last_date(self):
        return self._last_date

# 添加一个方法来验证是否包含特定日期的数据
    def has_date(self, date):
        """检查是否包含特定日期的数据"""
        # 处理不同格式的日期输入
        if isinstance(date, str):
            try:
                # 尝试将字符串解析为datetime对象
                date = datetime.strptime(date, '%Y-%m-%d')
            except ValueError:
                print(f"无法解析日期字符串: {date}")
                return False
        
        # 检查日期是否在存储中
        # 注意：我们需要考虑日期的时间部分是否会影响匹配
        # 为了安全起见，我们将检查日期部分是否匹配，忽略时间
        for stored_date in self._store.keys():
            if (stored_date.year == date.year and 
                stored_date.month == date.month and 
                stored_date.day == date.day):
                return True
        return False
    
    def get_date_data(self, date):
        """获取特定日期的数据，如果存在"""
        if isinstance(date, str):
            try:
                date = datetime.strptime(date, '%Y-%m-%d')
            except ValueError:
                print(f"无法解析日期字符串: {date}")
                return None
        
        # 查找匹配的日期（忽略时间部分）
        for stored_date, wdc in self._store.items():
            if (stored_date.year == date.year and 
                stored_date.month == date.month and 
                stored_date.day == date.day):
                return wdc
        return None
    
    def verify_target_date(self):
        """验证是否包含目标日期（2020-04-09）的数据"""
        target_date = datetime(2020, 4, 9)
        has_target = self.has_date(target_date)
        print(f"是否包含目标日期 {target_date}: {has_target}")
        
        if has_target:
            wdc = self.get_date_data(target_date)
            if wdc:
                print(f"  目标日期数据详情:")
                print(f"  TMIN: {wdc.TMIN}°C")
                print(f"  TMAX: {wdc.TMAX}°C")
                print(f"  IRRAD: {wdc.IRRAD} J/m²/day")
                print(f"  RAIN: {wdc.RAIN} cm")
    
# 测试代码
if __name__ == "__main__":
    print("创建自定义测试天气数据提供器...")
    provider = CustomTestWeatherDataProvider(year=2020)
    print(f"成功创建提供器，包含 {len(provider)} 条数据")
    print(f"日期范围: {provider.first_date} 到 {provider.last_date}")
    print(f"站点参数: {provider.get_site_parameters()}")
    
    # 验证是否包含目标日期（2020-04-09）的数据
    print("\n验证目标日期...")
    provider.verify_target_date()
    
    # 打印前5天的数据
    print("\n前5天的天气数据示例:")
    for i, date in enumerate(sorted(provider.keys())[:5]):
        wdc = provider[date]
        print(f"\n第{i+1}天 ({date}):")
        print(f"  最低温度: {wdc.TMIN:.1f}°C")
        print(f"  最高温度: {wdc.TMAX:.1f}°C")
        print(f"  太阳辐射: {wdc.IRRAD/1000:.1f} kJ/m²")
        print(f"  降雨量: {wdc.RAIN:.2f} cm")
        print(f"  风速: {wdc.WIND:.1f} m/s")
    
    # 测试has_date和get_date_data方法
    print("\n测试日期查找方法...")
    print(f"是否包含2020-04-09: {provider.has_date('2020-04-09')}")
    print(f"是否包含2020-04-10: {provider.has_date('2020-04-10')}")
    print(f"是否包含2021-01-01: {provider.has_date('2021-01-01')}")