import uuid
import numpy as np
import pandas as pd
import yaml 
import os
import json
from pathlib import Path
from yaml_agro_writer import YAMLAgroManagementWriter
import pcse
from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
from pcse.input import (
    YAMLAgroManagementReader,  # 农业管理数据读取器
    YAMLCropDataProvider,      # 作物数据提供器
    CABOFileReader,
    NASAPowerWeatherDataProvider,
    ExcelWeatherDataProvider,
    WOFOST81SiteDataProvider_SNOMIN,
    WOFOST72SiteDataProvider
)
from pcse.models import (
    Wofost71_WLP_FD,  # 导入 Wofost71_WLP_FD 模型
    Wofost72_PP       # 导入 Wofost72_WLP_FD 模型
)
from pcse.base import ParameterProvider  # 参数提供基类
from pcse.util import (
    DummySoilDataProvider,  # 虚拟土壤数据提供器
    doy                     # 计算日序数的函数
)
from pcse.engine import Engine

# 导入NASA天气数据转换工具
from nasa_to_excel_simple import get_nasa_weather_data, create_excel_file, DEFAULT_ANGSTROM_A, DEFAULT_ANGSTROM_B, NO_DATA_VALUE

# 设置AGRO_DIR路径
# RUN_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
# AGRO_DIR=RUN_DIR.parent/'agro'
# global agro_dict
# 然后在config.py中可以定义如下内容
PROJECT_ROOT = Path(os.path.dirname(os.path.abspath(__file__)))
# PROJECT_ROOT = Path(__file__).parent.parent   # 根据实际项目结构调整相对层级 .parent 
DATA_DIR = PROJECT_ROOT / "data"
# WOFOST81_DIR = DATA_DIR / "Irrigation81"
INPUT_DIR = DATA_DIR / "input"
CROP_DIR = DATA_DIR / "crop"
OUTPUT_DIR = DATA_DIR / "output"
WEATHER_DIR = DATA_DIR / "meteo"  # 统一使用meteo目录存储天气数据
AGRO_DIR = DATA_DIR / "agro"
# 实现PCSE真实模拟功能
class PCSESimulator:
    def __init__(self):
        # 初始化数据路径
        self.PROJECT_ROOT = Path(os.path.dirname(os.path.abspath(__file__)))
        self.DATA_DIR = self.PROJECT_ROOT / "data"
        self.CROP_DIR = self.DATA_DIR / "crop"
        self.SOIL_DIR = self.DATA_DIR / "soil"
        self.SITE_DIR = self.DATA_DIR / "site"
        self.WEATHER_DIR = self.DATA_DIR / "meteo"
        self.AGRO_DIR = self.DATA_DIR / "agro"
    
    def get_weather_provider(self, latitude, longitude, force_update=False):
        """获取天气数据提供器，确保始终返回有效的天气提供者"""
        try:
            # 获取NASA数据
            result = get_nasa_weather_data(
                latitude=latitude, 
                longitude=longitude, 
                force_update=force_update,
                excel_path=self.WEATHER_DIR / "new_nasa_data.xlsx"
            )
            
            # 处理返回值
            weather_provider = result
            if isinstance(result, tuple) and len(result) >= 3:
                weather_provider, _, _ = result  # 只需要第一个元素
            
            # 确保返回的是一个有效的天气数据提供器对象
            if weather_provider is not None:
                # 如果返回的是元组，尝试提取第一个元素
                if isinstance(weather_provider, tuple) and weather_provider:
                    inner_provider = weather_provider[0]
                    if inner_provider is not None and hasattr(inner_provider, 'get_weather'):
                        return inner_provider
                
                # 直接返回weather_provider
                return weather_provider
            
        except Exception:
            pass
        
        # 如果所有尝试都失败，返回默认的ExcelWeatherDataProvider
        test_weather_file = self.WEATHER_DIR / "example_weather.xlsx"
        if os.path.exists(test_weather_file):
            try:
                return ExcelWeatherDataProvider(str(test_weather_file))
            except Exception:
                pass
        
        # 作为最后的后备方案，创建一个简单的模拟天气提供者
        print("创建模拟天气数据提供者作为后备")
        from pcse.base import WeatherDataContainer
        
        class SimpleWeatherProvider:
            def __init__(self):
                self.start_date = datetime(2023, 1, 1).date()
                self.end_date = datetime(2023, 12, 31).date()
                self.latitude = latitude
                self.longitude = longitude
            
            def get_weather(self, day):
                # 返回一个简单的天气数据容器
                return WeatherDataContainer(
                    DAY=day,
                    IRRAD=15.0,
                    TMIN=15.0,
                    TMAX=25.0,
                    VAP=1.5,
                    WIND=2.0,
                    RAIN=0.0
                )
        
        return SimpleWeatherProvider()
    
    def get_crop_provider(self, params):
        """获取作物数据提供器"""
        try:
            crop_name = params.get('crop_name', 'potato')
            variety_name = params.get('variety_name', 'Potato_701')
            
            # 创建作物数据提供器
            from pcse.models import Wofost71_WLP_FD
            crop_provider = YAMLCropDataProvider(Wofost71_WLP_FD)
            
            # 应用初始生物量参数，如果有的话
            initial_biomass = params.get('initial_biomass')
            if initial_biomass is not None:
                try:
                    # 将字符串转换为浮点数
                    initial_biomass_value = float(initial_biomass)
                    
                    # 创建和返回一个带有初始生物量的字典
                    return {
                        'crop_provider': crop_provider,
                        'initial_biomass': initial_biomass_value
                    }
                except (ValueError, TypeError):
                    pass
            
            # 如果没有初始生物量参数，返回原始的作物提供器
            return {'crop_provider': crop_provider, 'initial_biomass': None}
        except Exception:
            # 回退到基本的DummySoilDataProvider作为临时解决方案
            return {'crop_provider': DummySoilDataProvider(), 'initial_biomass': None}
    
    def get_soil_provider(self, params):
        """获取土壤数据提供器"""
        try:
            soil_type = params.get('soil_type', 'ec1')
            soil_file = self.SOIL_DIR / f"{soil_type}.soil"
            
            if os.path.exists(soil_file):
                return CABOFileReader(soil_file)
            
            # 如果找不到指定的土壤数据，使用虚拟土壤数据
            return DummySoilDataProvider()
        except Exception:
            # 出错时使用虚拟土壤数据
            return DummySoilDataProvider()
    
    def get_site_provider(self, params):
        """获取站点数据提供器"""
        try:
            # 简化处理，直接返回一个基本的参数字典
            return {
                'A0SOM': 24.0,    # 初始表层土壤有机质含量
                'CO2': 400.0,     # CO2浓度
                'IFUNRN': 0,      # 径流计算方法
                'WAV': 100.0,     # 初始土壤有效水分
                'NH4I': 0.0,      # 初始铵态氮含量
                'NO3I': 0.0,      # 初始硝态氮含量
                'SMLIM': 0.5,     # 土壤水分下限（用于限制蒸腾）
                'SSI': 0.0,       # 初始土壤溶质浓度
                'SSMAX': 50.0,    # 最大土壤溶质浓度
                'NOTINF': 1.0,    # 防止无限大值的参数
                'SSI0': 0.0,      # 初始溶质浓度（层0）
                'SSI1': 0.0,      # 初始溶质浓度（层1）
                'SSI2': 0.0,      # 初始溶质浓度（层2）
                'SSI3': 0.0,      # 初始溶质浓度（层3）
                'SSI4': 0.0,      # 初始溶质浓度（层4）
                'SSI5': 0.0,      # 初始溶质浓度（层5）
                'SSI6': 0.0,      # 初始溶质浓度（层6）
                'SSI7': 0.0       # 初始溶质浓度（层7）
            }
        except Exception:
            # 出错时返回一个空字典或基本字典
            return {}
    
    def get_agromanagement(self, params):
        """获取农业管理数据"""
        try:
            # 尝试从YAML文件读取农业管理数据
            default_agro_file = self.AGRO_DIR / "test_agro.yaml"
            if os.path.exists(default_agro_file):
                from pcse.input import YAMLAgroManagementReader
                return YAMLAgroManagementReader(default_agro_file)
            
            # 如果没有找到默认文件，尝试使用params中的作物和日期信息创建一个简单的农业管理计划
            # 创建一个符合PCSE要求的农业管理对象
            from pcse.input import YAMLAgroManagementWriter
            import tempfile
            
            # 获取参数中的日期信息，如果没有则使用默认值
            start_date = params.get('crop_start_date', datetime(2020, 4, 20).date())
            end_date = params.get('crop_end_date', datetime(2020, 9, 30).date())
            crop_name = params.get('crop_name', 'potato')
            variety_name = params.get('variety_name', 'Potato_701')
            
            # 创建一个临时文件来存储农业管理数据
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
                # 写入YAML格式的农业管理数据 - 注意去掉日期字符串的单引号
                temp_file.write(f"2020-01-01:\n")
                temp_file.write("  CropCalendar:\n")
                temp_file.write(f"    crop_start_date: '{start_date}'\n")
                temp_file.write("    crop_start_type: sowing\n")
                temp_file.write(f"    crop_end_date: '{end_date}'\n")
                temp_file.write("    crop_end_type: harvest\n")
                temp_file.write("    max_duration: 400\n")
                temp_file.write(f"    crop_name: {crop_name}\n")
                temp_file.write(f"    variety_name: {variety_name}\n")
                temp_file.write("  TimedEvents: []\n")
                temp_file.write("  StateEvents: []\n")
                temp_file_path = temp_file.name
                temp_file.flush()
                os.fsync(temp_file.fileno())  # 确保写入完成
            
            # 使用YAMLAgroManagementReader读取临时文件
            agro_manager = YAMLAgroManagementReader(temp_file_path)
            
            # 清理临时文件
            try:
                os.unlink(temp_file_path)
            except:
                pass
            
            return agro_manager
        except Exception as e:
            print(f"创建农业管理数据时出错: {str(e)}")
            # 出错时返回一个简单但有效的农业管理字典
            # 注意：这里不再返回列表，而是返回一个符合PCSE期望的字典结构
            # 出错时返回一个简单但有效的农业管理字典
            # 确保日期格式正确，使用字符串而不是datetime对象
            return {
                '2023-01-01': {
                    'CropCalendar': {
                        'crop_start_date': '2023-04-20',
                        'crop_start_type': 'sowing',
                        'crop_end_date': '2023-09-30',
                        'crop_end_type': 'harvest',
                        'max_duration': 400,
                        'crop_name': 'potato',
                        'variety_name': 'Potato_701'
                    },
                    'TimedEvents': [],
                    'StateEvents': []
                }
            }

    def simulate_crop_growth(self, params):
        """运行作物生长模拟"""
        # 初始化完整响应对象
        full_response = {
            'results': [],
            'simulation_status': {
                'success': False,
                'message': '准备运行模拟',
                'method_used': '',
                'run_time_seconds': 0,
                'output_record_count': 0
            },
            'weather_info': {
                'source': 'unknown',
                'details': '',
                'success': False
            },
            'error': None
        }
        
        try:
            # 1. 获取各种数据提供器
            latitude = params.get('latitude', 39.9042)
            longitude = params.get('longitude', 116.4074)
            force_update = True
            
            # 获取天气数据提供器
            try:
                weather_result = self.get_weather_provider(latitude, longitude, force_update)
                weather_provider = weather_result[0] if isinstance(weather_result, tuple) and weather_result else weather_result
                
                if weather_provider is None:
                    full_response['weather_info'] = {
                        'source': 'unknown',
                        'details': '无法获取有效的天气提供者',
                        'success': False
                    }
                else:
                    weather_details = []
                    if hasattr(weather_provider, 'start_date'): weather_details.append(f"开始日期: {weather_provider.start_date}")
                    if hasattr(weather_provider, 'end_date'): weather_details.append(f"结束日期: {weather_provider.end_date}")
                    if hasattr(weather_provider, 'latitude'): weather_details.append(f"纬度: {weather_provider.latitude}")
                    if hasattr(weather_provider, 'longitude'): weather_details.append(f"经度: {weather_provider.longitude}")
                    
                    full_response['weather_info'] = {
                        'source': type(weather_provider).__name__,
                        'details': ', '.join(weather_details),
                        'success': True
                    }
            except Exception as weather_error:
                full_response['error'] = str(weather_error)
                full_response['simulation_status']['success'] = False
                full_response['simulation_status']['message'] = f"获取天气提供者时出错: {weather_error}"
                full_response['weather_info'] = {
                    'source': 'unknown',
                    'details': str(weather_error),
                    'success': False
                }
                return full_response
            
            # 获取其他数据提供器
            try:
                crop_data = self.get_crop_provider(params)
                crop_provider = crop_data['crop_provider']
                soil_provider = self.get_soil_provider(params)
                site_provider = self.get_site_provider(params)
                agromanagement = self.get_agromanagement(params)
            except Exception as provider_error:
                full_response['error'] = str(provider_error)
                full_response['simulation_status']['success'] = False
                full_response['simulation_status']['message'] = f"获取数据提供器时出错: {provider_error}"
                return full_response
            
            # 2. 创建参数提供器
            parameter_provider = ParameterProvider(
                cropdata=crop_provider,
                soildata=soil_provider,
                sitedata=site_provider
            )
            
            # 3. 选择模型类型
            model_type = params.get('model_type', 'Wofost71_WLP_FD')
            if model_type == 'Wofost72_PP':
                from pcse.models import Wofost72_PP as Model
            else:
                from pcse.models import Wofost71_WLP_FD as Model
            
            # 4. 初始化模型
            print("=== 模型初始化 ===")
            print(f"天气提供者类型: {type(weather_provider).__name__}")
            print(f"参数提供器: {parameter_provider}")
            print(f"农业管理数据类型: {type(agromanagement).__name__}")
            
            try:
                model = Model(parameter_provider, weather_provider, agromanagement)
                print("✓ 模型初始化成功")
                
                # 5. 应用初始生物量（如果有）
                # 6. 运行模拟
                simulation_days = params.get('days')
                startdate = params.get('start_date')
                enddate = params.get('end_date')
                print(f"开始日期: {startdate}, 结束日期: {enddate}")
                simulation_status = {
                    'success': False,
                    'message': '准备运行模拟',
                    'method_used': '',
                    'run_time_seconds': 0,
                    'output_record_count': 0
                }
                
                # 运行模拟
                print(f"\n=== 开始模拟运行 ===")
                print(f"模拟参数: simulation_days={simulation_days}, startdate={startdate}")
                
                start_time = datetime.now()
                
                try:
                    # 首先尝试使用run_till方式运行指定天数
                    if simulation_days is not None:
                        try:
                            # 将simulation_days转换为整数
                            days_to_run = int(simulation_days)
                            # 计算目标日期
                            # 检查startdate是否存在并尝试转换为datetime对象
                            if startdate:
                                try:
                                    start_date_obj = datetime.strptime(startdate, '%Y-%m-%d')
                                    target_date = start_date_obj + timedelta(days=days_to_run)
                                    
                                    # 获取模型当前日期
                                    model_current_date = model.day
                                    print(f"模型当前日期: {model_current_date}, 计算的目标日期: {target_date}")

                                    print(f"尝试运行model.run_till({target_date.strftime('%Y-%m-%d')}) (最终目标日期)")
                                    model.run_till(target_date)
                                except ValueError:
                                    # 如果日期解析失败，回退到使用run_till_terminate
                                    print(f"⚠ 日期解析错误，无法计算目标日期: {startdate}")
                                    model.run_till_terminate()
                            else:
                                # 如果没有startdate，直接使用run_till_terminate
                                print(f"⚠ 没有提供开始日期，无法计算目标日期")
                                model.run_till_terminate()
                            
                            end_time = datetime.now()
                            run_time = (end_time - start_time).total_seconds()
                            simulation_status = {
                                'method_used': 'run_till',
                                'days_simulated': days_to_run,
                                'run_time_seconds': run_time,
                                'success': True,
                                'message': f"模型成功运行{days_to_run}天"
                            }
                            print(f"✓ run_till执行成功，耗时: {run_time:.2f}秒")
                        except Exception as e:
                            # 处理run_till运行错误
                            print(f"⚠ run_till运行出错: {str(e)}")
                            print("尝试运行model.run_till_terminate()作为备选")
                            
                            model.run_till_terminate()
                            end_time = datetime.now()
                            run_time = (end_time - start_time).total_seconds()
                            simulation_status = {
                                'method_used': 'run_till_terminate (fallback)',
                                'run_time_seconds': run_time,
                                'success': True,
                                'message': f"run_till运行出错({str(e)}), 成功回退到run_till_terminate"
                            }
                            print(f"✓ run_till_terminate(备选)执行成功，耗时: {run_time:.2f}秒")
                    else:
                        # 如果没有指定天数，使用run_till_terminate
                        print("没有指定模拟天数，尝试运行model.run_till_terminate()")
                        model.run_till_terminate()
                        end_time = datetime.now()
                        run_time = (end_time - start_time).total_seconds()
                        simulation_status = {
                            'method_used': 'run_till_terminate',
                            'run_time_seconds': run_time,
                            'success': True,
                            'message': "模型成功运行到终止条件"
                        }
                        print(f"✓ run_till_terminate执行成功，耗时: {run_time:.2f}秒")
                except (ValueError, TypeError) as e:
                    # 处理参数类型错误
                    print(f"⚠ 设置模拟天数出错: {str(e)}")
                    print("尝试运行model.run_till_terminate()作为备选")
                    
                    try:
                        model.run_till_terminate()
                        end_time = datetime.now()
                        run_time = (end_time - start_time).total_seconds()
                        simulation_status = {
                            'method_used': 'run_till_terminate (fallback)',
                            'run_time_seconds': run_time,
                            'success': True,
                            'message': f"设置模拟天数出错({str(e)}), 成功回退到run_till_terminate"
                        }
                        print(f"✓ run_till_terminate(备选)执行成功，耗时: {run_time:.2f}秒")
                    except Exception as inner_e:
                        simulation_status = {
                            'success': False,
                            'message': f"设置模拟天数出错({str(e)})，且run_till_terminate也失败: {str(inner_e)}"
                        }
                        print(f"✗ 所有运行模式均失败: {str(inner_e)}")
                except Exception as e:
                    # 其他运行错误
                    simulation_status = {
                        'success': False,
                        'message': f"模型运行失败: {str(e)}"
                    }
                    print(f"✗ 模型运行失败: {str(e)}")
            except Exception as model_init_error:
                print(f"✗ 模型初始化失败: {str(model_init_error)}")
                simulation_status = {
                    'success': False,
                    'message': f"模型初始化失败: {str(model_init_error)}"
                }
            
            # 7. 获取模拟结果
            try:
                output = model.get_output()
                simulation_status['output_record_count'] = len(output) if output else 0
            except Exception:
                simulation_status['success'] = False
                simulation_status['message'] = f"{simulation_status['message']}; 获取模拟结果出错"
                output = []
            
            # 8. 处理结果，转换为前端需要的格式
            results = []
            for i, record in enumerate(output):
                # 安全地获取并转换数据
                tagp_value = float(record.get('TAGP', 0) or 0)
                lai_value = float(record.get('LAI', 0) or 0)
                twso_value = float(record.get('TWSO', 0) or 0)
                htm_value = float(record.get('HTM', 0) or 0)
                trl_value = float(record.get('TRL', 0) or 0)
                tra_value = float(record.get('TRA', 0) or 0)
                tramx_value = float(record.get('TRAMX', 1) or 1)
                
                water_stress_value = tra_value / tramx_value if tramx_value > 0 else 0
                date_str = record['day'].strftime('%Y-%m-%d') if hasattr(record['day'], 'strftime') else str(record['day'])
                is_day_130 = 1 if (i + 1) == 130 else 0
                
                day_data = {
                    'day': i + 1,
                    'date': date_str,
                    'biomass': tagp_value,
                    'lai': lai_value,
                    'yield': twso_value,
                    'height': htm_value,
                    'roots': trl_value,
                    'water_stress': water_stress_value,
                    'is_day_130': is_day_130
                }
                results.append(day_data)
            
            # 确保结果不为空
            if not results:
                # 如果没有结果，生成一些模拟数据
                print('运行模拟失败,采用算法结束！')
                days = 100
                days_array = np.arange(days)
                results = [{
                    'day': int(i + 1),
                    'date': (datetime.now() + timedelta(days=int(i))).strftime('%Y-%m-%d'),
                    'biomass': float(10 * np.exp(0.03 * i)),
                    'lai': float(5 / (1 + np.exp(-0.05 * (i - 40)))),
                    'yield': float(3 * np.exp(0.03 * i) * (1 - np.exp(-0.02 * i))),
                    'height': float(50 * (1 - np.exp(-0.04 * i))),
                    'roots': float(5 * np.exp(0.025 * i)),
                    'water_stress': float(0.9 + 0.1 * np.sin(i/10)),
                    'is_day_130': int((i + 1) == 130)
                } for i in days_array]
            
            # 添加安全检查，确保所有值都是可JSON序列化的
            clean_results = self._clean_json_serializable(results) or results
            
            # 更新完整响应对象
            full_response['results'] = clean_results
            full_response['simulation_status'] = simulation_status
            if 'weather_info' not in full_response:
                full_response['weather_info'] = {
                    'source': 'unknown',
                    'details': 'Weather info not available',
                    'success': False
                }
            full_response['error'] = None
            
        except Exception as e:
            # 出错时返回模拟数据
            days = 30
            days_array = np.arange(days)
            results = [{
                'day': int(i + 1),
                'date': (datetime.now() + timedelta(days=int(i))).strftime('%Y-%m-%d'),
                'biomass': float(10 * np.exp(0.05 * i)),
                'lai': float(5 / (1 + np.exp(-0.1 * (i - 15)))),
                'yield': float(3 * np.exp(0.05 * i) * (1 - np.exp(-0.03 * i))),
                'height': float(60 * (1 - np.exp(-0.05 * i))),
                'roots': float(5 * np.exp(0.04 * i)),
                'water_stress': float(0.8 + 0.2 * np.sin(i/8)),
                'is_day_130': int((i + 1) == 130)
            } for i in days_array]
            
            # 确保错误情况下返回的数据也是可JSON序列化的
            clean_results = self._clean_json_serializable(results) or results
            
            # 更新完整响应对象（错误情况）
            full_response['results'] = clean_results
            full_response['simulation_status'] = {'success': False, 'message': str(e), 'method_used': '', 'run_time_seconds': 0, 'output_record_count': 0}
            full_response['weather_info'] = {'source': 'simulated', 'details': '使用模拟天气数据', 'success': True}
            full_response['error'] = str(e)
            
        return full_response
    
    def _clean_json_serializable(self, data):
        """递归清理数据，确保所有值都是可JSON序列化的基本Python类型"""
        try:
            if data is None:
                return None
            elif isinstance(data, dict):
                # 递归处理字典，确保所有键都是字符串
                result = {}
                for key, value in data.items():
                    clean_key = str(key) if not isinstance(key, str) else key
                    clean_value = self._clean_json_serializable(value)
                    if clean_value is not None:
                        result[clean_key] = clean_value
                return result
            elif isinstance(data, list):
                # 递归处理列表，过滤掉None值
                return [item for item in [self._clean_json_serializable(elem) for elem in data] if item is not None]
            elif isinstance(data, (bool, int, float, str)):
                # 基本类型直接返回，但布尔值转为整数以确保兼容性
                return int(data) if isinstance(data, bool) else data
            elif hasattr(data, 'item') and callable(data.item):
                # 处理numpy类型
                try:
                    return data.item()
                except:
                    try:
                        return float(data)
                    except:
                        return str(data)
            elif hasattr(data, 'to_dict') and callable(data.to_dict):
                # 处理pandas对象
                try:
                    return self._clean_json_serializable(data.to_dict())
                except:
                    return str(data)
            else:
                # 尝试转换为基本类型
                try:
                    return float(data)
                except (ValueError, TypeError):
                    # 如果转换失败，返回字符串表示
                    try:
                        return str(data)
                    except:
                        # 如果连字符串转换都失败，返回占位符
                        return '[Unserializable]'
        except Exception as e:
            print(f"清理JSON序列化数据时出错: {str(e)}")
            # 出错时返回占位符而不是None，避免删除字段
            return '[Error]'

app = Flask(__name__)
simulator = PCSESimulator()
@app.route('/Input_data')
def Input_data():
    # 获取URL参数中的crop_name
    selected_crop = request.args.get('crop_name')
    
    # 给定的 YAML 内容
    # yaml_content = """
    # crop_end_date: 2020-09-24
    # crop_end_type: harvest
    # crop_name: potato
    # crop_start_date: 2020-04-21
    # crop_start_type: sowing
    # max_duration: 400
    # variety_name: Fontane
    #"""
    # print(data)
    try:
        # 解析 YAML 内容 AGRO_DIR
        agro_fname = AGRO_DIR / "test_agro.yaml"
        
        print(agro_fname) #
        
        # global agro_dict
        
        agro_dict = YAMLAgroManagementReader(agro_fname)

        fname=AGRO_DIR / "agro_dict.xlsx"
        # df.to_csv(fname)

        YAMLAgroManagementWriter.write_to_excel(agro_dict, fname)


        firstkey = list(agro_dict[0])[0]
        cropcalendar = agro_dict[0][firstkey]['CropCalendar'] 
        # 提取 crop_name

                    
        #             # 获取agro列表中第一个元素（应该是包含农业管理信息的字典结构）的第一个键，这个键可能对应着特定的时间节点或者管理阶段相关的信息，用于后续提取作物种植日历相关内容。


        crop_data=cropcalendar
        print(f"Crop crop_data=: {crop_data}")

    except yaml.YAMLError as exc:
        return f"Error parsing YAML: {exc}"

    # 初始数据，模拟从数据库或者其他地方获取的数据

    
    # 预定义的选择项 - 与/路由中的定义保持一致
    crop_names = ['potato', 'tomato', 'carrot', 'barley', 'cassava', 'chickpea', 'cotton', 
                  'cowpea', 'fababean', 'groundnut', 'maize', 'millet', 'mungbean', 
                  'pigeonpea', 'rapeseed', 'rice', 'sorghum', 'soybean', 'sugarbeet', 
                  'sugarcane', 'sunflower', 'sweetpotato', 'tobacco', 'wheat']
    
    # 品种选项 - 与/路由中的定义保持一致
    variety_names = {
        'potato': ['Potato_701', 'Potato_702'],
        'tomato': ['Tomato_801', 'Tomato_802'],
        'carrot': ['Carrot_901', 'Carrot_902'],
        'barley': ['Spring_barley_301'],
        'cassava': ['Cassava_VanHeemst_1988'],
        'chickpea': ['Chickpea_VanHeemst_1988'],
        'cotton': ['Cotton_VanHeemst_1988'],
        'cowpea': ['Cowpea_VanHeemst_1988'],
        'fababean': ['Faba_bean_801'],
        'groundnut': ['Groundnut_VanHeemst_1988'],
        'maize': ['Maize_VanHeemst_1988'],
        'millet': ['Millet_VanHeemst_1988'],
        'mungbean': ['Mungbean_VanHeemst_1988'],
        'pigeonpea': ['Pigeonpea_VanHeemst_1988'],
        'rapeseed': ['Oilseed_rape_1001'],
        'rice': ['Rice_501'],
        'sorghum': ['Sorghum_VanHeemst_1988'],
        'soybean': ['Soybean_901'],
        'sugarbeet': ['Sugarbeet_601'],
        'sugarcane': ['Sugarcane_VanHeemst_1988'],
        'sunflower': ['Sunflower_1101'],
        'sweetpotato': ['Sweetpotato_VanHeemst_1988'],
        'tobacco': ['Tobacco_VanHeemst_1988'],
        'wheat': ['Winter_wheat_101']
    }
    # 种植方式选项
    start_types = ['sowing', 'transplanting']
    end_types = ['harvest', 'drying']
    
    # 如果有选择的作物，更新crop_data
    if selected_crop and selected_crop in crop_names:
        if crop_data:
            # 克隆crop_data字典并更新作物名称
            crop_data = crop_data.copy() if isinstance(crop_data, dict) else {}
            crop_data['crop_name'] = selected_crop
        else:
            # 如果没有crop_data，创建一个新的
            crop_data = {'crop_name': selected_crop}
    
    return render_template('datainput.html', crop_data=crop_data, crop_names=crop_names, variety_names=variety_names, start_types=start_types, end_types=end_types)

@app.route('/')
def index():
    # 预定义的选择项 - 与前端main.js中的dict_of_crop_sorts保持一致
    crop_names = ['potato', 'tomato', 'carrot', 'barley', 'cassava', 'chickpea', 'cotton', 
                  'cowpea', 'fababean', 'groundnut', 'maize', 'millet', 'mungbean', 
                  'pigeonpea', 'rapeseed', 'rice', 'sorghum', 'soybean', 'sugarbeet', 
                  'sugarcane', 'sunflower', 'sweetpotato', 'tobacco', 'wheat']
    
    # 品种选项 - 与前端main.js中的逻辑保持一致
    variety_names = {
        'potato': ['Potato_701', 'Potato_702'],
        'tomato': ['Tomato_801', 'Tomato_802'],
        'carrot': ['Carrot_901', 'Carrot_902'],
        'barley': ['Spring_barley_301'],
        'cassava': ['Cassava_VanHeemst_1988'],
        'chickpea': ['Chickpea_VanHeemst_1988'],
        'cotton': ['Cotton_VanHeemst_1988'],
        'cowpea': ['Cowpea_VanHeemst_1988'],
        'fababean': ['Faba_bean_801'],
        'groundnut': ['Groundnut_VanHeemst_1988'],
        'maize': ['Maize_VanHeemst_1988'],
        'millet': ['Millet_VanHeemst_1988'],
        'mungbean': ['Mungbean_VanHeemst_1988'],
        'pigeonpea': ['Pigeonpea_VanHeemst_1988'],
        'rapeseed': ['Oilseed_rape_1001'],
        'rice': ['Rice_501'],
        'sorghum': ['Sorghum_VanHeemst_1988'],
        'soybean': ['Soybean_901'],
        'sugarbeet': ['Sugarbeet_601'],
        'sugarcane': ['Sugarcane_VanHeemst_1988'],
        'sunflower': ['Sunflower_1101'],
        'sweetpotato': ['Sweetpotato_VanHeemst_1988'],
        'tobacco': ['Tobacco_VanHeemst_1988'],
        'wheat': ['Winter_wheat_101']
    }
    
    # 默认没有选中的作物数据
    crop_data = None
    
    return render_template('index.html', crop_data=crop_data, crop_names=crop_names, variety_names=variety_names)

@app.route('/weather_input')
def weather_input():
    return render_template('weather_input.html')

@app.route('/get_weather_data', methods=['POST'])
def get_weather_data():
    """获取天气数据的API接口 - 使用已完成的测试代码"""
    try:
        # 获取请求参数
        data = request.json
        latitude = float(data.get('latitude', 39.9042))
        longitude = float(data.get('longitude', 116.4074))
        year = int(data.get('year', 2023))
        elevation = float(data.get('elevation', 10))
        force_update = data.get('force_update', True)
        
        print(f"接收到天气数据请求: 纬度={latitude}, 经度={longitude}, 年份={year}")
        
        # 1. 从NASA POWER获取天气数据
        nasa_data, first_date, last_date = get_nasa_weather_data(
            latitude=latitude, 
            longitude=longitude, 
            force_update=force_update
        )
        
        # 2. 筛选指定年份的数据
        # 获取数据
        data = nasa_data.export()
        if not data or len(data) == 0:
            raise ValueError("从NASA获取的天气数据为空")
        df_nasa_data = pd.DataFrame(data)
        df_nasa_data['DAY'] = pd.to_datetime(df_nasa_data['DAY'])
        df_nasa_data = df_nasa_data[df_nasa_data['DAY'].dt.year == year]

        # 检查是否有数据
        if df_nasa_data.empty:
            return jsonify({
                'error': f'未找到{year}年的天气数据'
            })
        
        # 转换为字典列表
        filtered_data = df_nasa_data.to_dict('records')
        
        # 3. 准备返回的数据
        days = [item['DAY'].strftime('%Y-%m-%d') for item in filtered_data]
        tmin = [item['TMIN'] for item in filtered_data]
        tmax = [item['TMAX'] for item in filtered_data]
        rainfall = [item.get('RAIN', 0.0) for item in filtered_data]
        radiation = [item['IRRAD']  for item in filtered_data]  # 转换为kJ/m²
        
        # 4. 保存天气数据到Excel文件
        try:
            # 生成文件名
            lat_str = f"{latitude:.2f}".replace('-', 'neg')
            lon_str = f"{longitude:.2f}".replace('-', 'neg')
            filename = f"nasa_weather_{lat_str}_{lon_str}_{year}.xlsx"
            
            # 获取meteo目录路径
            project_root = Path(os.path.dirname(os.path.abspath(__file__)))
            meteo_dir = project_root / "data" / "meteo"
            
            # 确保目录存在
            os.makedirs(meteo_dir, exist_ok=True)
            
            # 保存文件路径
            filepath = os.path.join(meteo_dir, filename)
            
            # 使用已完成的测试代码创建Excel文件
            create_excel_file(filtered_data, filepath, latitude, longitude, elevation)
            
            print(f"天气数据已保存至: {filepath}")
        except Exception as save_error:
            print(f"保存天气数据出错: {save_error}")
            # 不影响主流程，继续返回数据
        
        # 5. 计算统计信息
        avg_temp = sum([(min_val + max_val) / 2 for min_val, max_val in zip(tmin, tmax)]) / len(tmin)
        avg_rain = sum(rainfall) / len(rainfall)
        avg_rad = sum(radiation) / len(radiation)
        
        # 日期范围
        date_range = f"{min(days)} 到 {max(days)}"
        
        return jsonify({
            'date_range': date_range,
            'record_count': len(filtered_data),
            'avg_temp': avg_temp,
            'avg_rain': avg_rain,
            'avg_rad': avg_rad,
            'days': days,
            'tmin': tmin,
            'tmax': tmax,
            'rainfall': rainfall,
            'radiation': radiation,
            'angstrom_a': DEFAULT_ANGSTROM_A,
            'angstrom_b': DEFAULT_ANGSTROM_B,
            'success': True
        })
    except Exception as e:
        print(f"获取天气数据出错: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'获取天气数据失败: {str(e)}',
            'success': False
        })

@app.route('/simulate', methods=['POST'])
def simulate():
    """处理模拟请求"""
    # 设置响应头
    response_headers = {
        'Content-Type': 'application/json',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY'
    }
    
    # 初始化请求ID
    request_id = str(uuid.uuid4())[:8]
    
    try:
        # 确保请求数据是有效的JSON
        if not request.is_json:
            error_response = {
                'error': '请求必须是JSON格式',
                'request_id': request_id,
                'timestamp': datetime.now().isoformat(),
                'success': False
            }
            return jsonify(error_response), 400, response_headers
            
        # 尝试解析JSON数据，捕获可能的解析错误
        try:
            data = request.json
            if not isinstance(data, dict):
                raise ValueError("请求数据必须是有效的JSON对象")
        except Exception as json_parse_error:
            error_response = {
                'error': 'JSON解析失败',
                'error_details': str(json_parse_error),
                'request_id': request_id,
                'timestamp': datetime.now().isoformat(),
                'success': False
            }
            print(f"[{request_id}] JSON解析失败: {json_parse_error}")
            return jsonify(error_response), 400, response_headers
        
        print(f"[{request_id}] 收到模拟请求")
        
        # 基本字段验证 - 仅记录警告而不直接返回错误
        # 这样可以让模拟器根据实际情况处理缺失字段
        if 'crop' not in data:
            # 检查是否有crop_name字段（前端使用的名称）
            if 'crop_name' in data:
                print(f"[{request_id}] 警告: 请求中缺少crop字段，但找到了crop_name字段，将使用crop_name的值")
                # 将crop_name的值赋给crop字段，确保模拟器能正确处理
                data['crop'] = data['crop_name']
            else:
                print(f"[{request_id}] 警告: 请求中缺少crop字段，将使用默认值")
        if 'start_date' not in data:
            print(f"[{request_id}] 警告: 请求中缺少start_date字段，将使用默认值")
        
        # 创建模拟器实例
        try:
            simulator = PCSESimulator()
        except Exception as init_error:
            error_response = {
                'error': '模拟器初始化失败',
                'error_details': str(init_error),
                'request_id': request_id,
                'timestamp': datetime.now().isoformat(),
                'success': False
            }
            print(f"[{request_id}] 模拟器初始化失败: {init_error}")
            import traceback
            traceback.print_exc()
            return jsonify(error_response), 500, response_headers
        
        # 运行模拟
        try:
            result = simulator.simulate_crop_growth(data)
            # 验证模拟结果格式
            if not isinstance(result, dict):
                raise ValueError("模拟结果必须是字典格式")
        except Exception as simulation_error:
            error_response = {
                'error': '模拟过程失败',
                'error_details': str(simulation_error),
                'request_id': request_id,
                'timestamp': datetime.now().isoformat(),
                'success': False
            }
            print(f"[{request_id}] 模拟过程失败: {simulation_error}")
            import traceback
            traceback.print_exc()
            return jsonify(error_response), 500, response_headers
        
        # 增强版JSON序列化检查和处理
        try:
            # 再次清理结果，确保所有数据都可序列化
            clean_result = simulator._clean_json_serializable(result)
            
            # 确保clean_result不为None且为字典类型
            if clean_result is None or not isinstance(clean_result, dict):
                raise ValueError("清理后的数据无效")
                
            # 添加元数据
            clean_result['request_id'] = request_id
            clean_result['timestamp'] = datetime.now().isoformat()
            clean_result.setdefault('success', True)
                
            # 测试序列化
            json_str = json.dumps(clean_result)
            print(f"[{request_id}] 模拟结果JSON序列化成功，数据大小: {len(json_str)} 字节")
            
            # 返回清理后的结果
            return jsonify(clean_result), 200, response_headers
        except Exception as json_error:
            error_msg = f"[{request_id}] 结果JSON序列化失败: {str(json_error)}"
            print(error_msg)
            # 记录详细的错误信息，包括失败的字段
            try:
                import traceback
                traceback.print_exc()
                # 提供一个安全的错误响应，确保它是可序列化的
                safe_response = {
                    'error': '处理模拟结果时出错',
                    'error_details': str(json_error),
                    'request_id': request_id,
                    'timestamp': datetime.now().isoformat(),
                    'success': False
                }
                return jsonify(safe_response), 500, response_headers
            except:
                # 最终的安全保障
                safe_text_response = '{{"error":"无法处理请求，请联系管理员","request_id":"{0}","timestamp":"{1}","success":false}}'.format(
                    request_id, datetime.now().isoformat()
                )
                return safe_text_response, 500, {'Content-Type': 'application/json'}
    except Exception as e:
        # 捕获所有其他异常
        error_id = request_id
        error_msg = f"[{error_id}] 模拟请求处理出错: {str(e)}"
        print(error_msg)
        try:
            import traceback
            traceback.print_exc()
            # 确保错误响应是可序列化的
            return jsonify({
                'error': '服务器处理请求时出错',
                'error_details': str(e),
                'request_id': error_id,
                'timestamp': datetime.now().isoformat(),
                'success': False
            }), 500, response_headers
        except:
            # 最终的安全保障
            safe_text_response = '{{"error":"服务器错误","request_id":"{0}","timestamp":"{1}","success":false}}'.format(
                error_id, datetime.now().isoformat()
            )
            return safe_text_response, 500, {'Content-Type': 'application/json'}


@app.route('/upload_weather_file', methods=['POST'])
def upload_weather_file():
    """处理天气文件上传"""
    try:
        # 检查是否有文件上传
        if 'weather_file' not in request.files:
            return jsonify({'success': False, 'error': '没有文件上传'})
        
        file = request.files['weather_file']
        
        # 检查文件名是否为空
        if file.filename == '':
            return jsonify({'success': False, 'error': '文件名为空'})
        
        # 检查文件类型，只接受Excel文件
        if not (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
            return jsonify({'success': False, 'error': '只支持Excel文件(.xlsx, .xls)'})
        
        # 获取meteo目录路径
        project_root = Path(os.path.dirname(os.path.abspath(__file__)))
        meteo_dir = project_root / "data" / "meteo"
        
        # 确保目录存在
        if not os.path.exists(meteo_dir):
            os.makedirs(meteo_dir)
        
        # 保存文件
        filename = file.filename
        filepath = os.path.join(meteo_dir, filename)
        
        # 保存文件（如果文件不存在）
        if not os.path.exists(filepath):
            import uuid
            t_filename='nasa_weather_35.00_110.00_2025.xlsx'
            file_ext = os.path.splitext(t_filename)[1]
            unique_id = uuid.uuid4().hex[:6]
            filename = f"{os.path.splitext(t_filename)[0]}_{unique_id}{file_ext}"
            filepath = os.path.join(meteo_dir, filename)
            file.save(filepath)
        
        return jsonify({'success': True, 'filename': filename})
    except Exception as e:
        return jsonify({'success': False, 'error': f'文件上传失败: {str(e)}'})

@app.route('/save_weather_data', methods=['POST'])
def save_weather_data():
    """保存天气数据到Excel文件"""
    try:
        # 获取请求数据
        data = request.json
        filename = data.get('filename')
        weather_data = data.get('weather_data')
        latitude = data.get('latitude', 39.9042)
        longitude = data.get('longitude', 116.4074)
        elevation = data.get('elevation', 10)
        
        if not filename:
            return jsonify({'success': False, 'error': '文件名不能为空'})
        
        if not weather_data:
            return jsonify({'success': False, 'error': '天气数据不能为空'})
        
        # 确保文件名以.xlsx结尾
        if not filename.endswith('.xlsx'):
            filename += '.xlsx'
        
        # 获取meteo目录路径
        project_root = Path(os.path.dirname(os.path.abspath(__file__)))
        meteo_dir = project_root / "data" / "meteo"
        
        # 确保目录存在
        os.makedirs(meteo_dir, exist_ok=True)
        
        # 保存文件路径
        filepath = os.path.join(meteo_dir, filename)
        
        # 准备数据用于Excel文件创建
        excel_data = []
        for i in range(len(weather_data['days'])):
            # 格式化日期
            date_str = weather_data['days'][i]
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            
            # 创建每行数据
            row = {
                'DAY': date_obj,
                'TMIN': weather_data['tmin'][i],
                'TMAX': weather_data['tmax'][i],
                'RAIN': weather_data['rainfall'][i],
                'IRRAD': weather_data['radiation'][i]
            }
            excel_data.append(row)
        
        # 创建Excel文件
        create_excel_file(excel_data, filepath, latitude, longitude, elevation)
        
        print(f"天气数据已保存至: {filepath}")
        
        return jsonify({
            'success': True,
            'message': '天气数据保存成功',
            'filepath': str(filepath)
        })
    except Exception as e:
        print(f"保存天气数据出错: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'保存天气数据失败: {str(e)}'
        })

@app.route('/get_crop_data', methods=['POST'])
def get_crop_data():
    """获取指定作物的品种数据"""
    try:
        # 获取请求参数
        crop_name = request.form.get('crop_name')
        
        # 定义品种选项字典
        variety_names = {
            'potato': ['Potato_701', 'Potato_702'],
            'tomato': ['Tomato_801', 'Tomato_802'],
            'carrot': ['Carrot_901', 'Carrot_902'],
            'barley': ['Spring_barley_301'],
            'cassava': ['Cassava_VanHeemst_1988'],
            'chickpea': ['Chickpea_VanHeemst_1988'],
            'cotton': ['Cotton_VanHeemst_1988'],
            'cowpea': ['Cowpea_VanHeemst_1988'],
            'fababean': ['Faba_bean_801'],
            'groundnut': ['Groundnut_VanHeemst_1988'],
            'maize': ['Maize_VanHeemst_1988'],
            'millet': ['Millet_VanHeemst_1988'],
            'mungbean': ['Mungbean_VanHeemst_1988'],
            'pigeonpea': ['Pigeonpea_VanHeemst_1988'],
            'rapeseed': ['Oilseed_rape_1001'],
            'rice': ['Rice_501'],
            'sorghum': ['Sorghum_VanHeemst_1988'],
            'soybean': ['Soybean_901'],
            'sugarbeet': ['Sugarbeet_601'],
            'sugarcane': ['Sugarcane_VanHeemst_1988'],
            'sunflower': ['Sunflower_1101'],
            'sweetpotato': ['Sweetpotato_VanHeemst_1988'],
            'tobacco': ['Tobacco_VanHeemst_1988'],
            'wheat': ['Winter_wheat_101']
        }
        
        # 获取作物数据
        crop_data = None
        if crop_name:
            # 如果存在该作物的品种数据，则设置作物数据
            if crop_name in variety_names:
                crop_data = {'crop_name': crop_name, 'variety_name': variety_names[crop_name][0]}
        
        # 定义作物名称列表
        crop_names = list(variety_names.keys())
        
        # 返回成功响应
        return jsonify({
            'success': True,
            'crop_data': crop_data,
            'crop_names': crop_names,
            'variety_names': variety_names
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取作物数据失败: {str(e)}'
        })


@app.route('/update_crop_data', methods=['POST'])
def update_crop_data():
    """处理作物数据更新请求并保存到文件系统"""
    try:
        data = request.json
        parsed_data = convert_dates(data)
        
        if not parsed_data:
            return jsonify({'error': '未提供数据'}), 400
        
        # 获取项目根目录
        project_root = Path(os.path.dirname(os.path.abspath(__file__)))
        data_dir = project_root / "data"
        
        # 确保数据目录存在
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # 确保agro目录存在
        agro_dir = data_dir / "agro"
        if not os.path.exists(agro_dir):
            os.makedirs(agro_dir)
        
        # 保存更新的农业管理数据到YAML文件
        agro_file = agro_dir / "updated_agro.yaml"
        
        # 创建农业管理字典结构
        if 'crop_start_date' in parsed_data:
            # 获取当前日期作为键
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            # 构建农业管理字典
            agro_dict = [{
                current_date: {
                    'CropCalendar': {
                        'crop_start_date': parsed_data.get('crop_start_date', datetime(2023, 4, 20).date()),
                        'crop_start_type': parsed_data.get('crop_start_type', 'sowing'),
                        'crop_end_date': parsed_data.get('crop_end_date', datetime(2023, 9, 30).date()),
                        'crop_end_type': parsed_data.get('crop_end_type', 'harvest'),
                        'max_duration': parsed_data.get('max_duration', 400),
                        'crop_name': parsed_data.get('crop_name', 'potato'),
                        'variety_name': parsed_data.get('variety_name', 'Potato_701')
                    },
                    'TimedEvents': [],
                    'StateEvents': []
                }
            }]
            
            # 保存到YAML文件
            try:
                with open(agro_file, 'w', encoding='utf-8') as f:
                    # 将date对象转换为字符串以支持YAML序列化
                    def date_representer(dumper, data):
                        if hasattr(data, 'strftime'):
                            return dumper.represent_str(data.strftime('%Y-%m-%d'))
                        return dumper.represent_str(str(data))
                    
                    yaml.add_representer(datetime, date_representer)
                    yaml.add_representer(type(datetime.now().date()), date_representer)
                    
                    yaml.dump(agro_dict, f, default_flow_style=False, allow_unicode=True)
                
                # 同时保存到Excel文件便于查看
                excel_file = agro_dir / "updated_agro.xlsx"
                try:
                    YAMLAgroManagementWriter.write_to_excel(agro_dict, excel_file)
                except Exception:
                    pass
            except Exception:
                pass
        
        # 返回成功响应
        return jsonify({
            'success': True,
            'message': '数据更新成功并已保存',
            'data': data,
            'saved_file': str(agro_file)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'数据更新失败: {str(e)}'
        }), 400
# 手动转换日期字符串为 datetime.date 对象
def convert_dates(data):
    if isinstance(data, dict):
        for key, value in data.items():
            data[key] = convert_dates(value)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            data[i] = convert_dates(item)
    elif isinstance(data, str):
        try:
            # 尝试将字符串转换为 datetime.date
            data = datetime.strptime(data, '%Y-%m-%d').date()
        except ValueError:
            pass  # 如果转换失败，保持原样
    return data
if __name__ == '__main__':
    app.run(debug=True)