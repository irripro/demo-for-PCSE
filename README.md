# PCSE作物生长模型演示平台

## 项目概述
PCSE作物生长模型演示平台是一个基于Python Crop Simulation Environment (PCSE)的Web应用程序，用于模拟和预测多种作物的生长过程。该平台提供直观的用户界面，允许用户设置各种参数（如作物类型、品种、地理位置、日期范围等），并通过图表可视化模拟结果，包括生物量变化、叶面积指数变化和预估产量变化。

## 系统架构

### 技术栈
- **后端**：Python 3.8+, Flask, PCSE 5.5.0+ 
- **前端**：HTML5, CSS3, JavaScript, Chart.js
- **数据处理**：pandas, openpyxl, numpy, PyYAML

### 核心组件
1. **PCSESimulator类**：模拟引擎核心，负责管理各类数据提供器和运行作物生长模型
2. **Web服务器**：基于Flask框架，提供RESTful API和Web界面
3. **数据处理模块**：负责解析和处理天气数据、作物数据、土壤数据和农业管理数据
4. **可视化模块**：使用Chart.js实现模拟结果的图表展示
5. **错误修复工具**：针对PCSE ExcelWeatherDataProvider常见问题的自动修复工具

### 项目结构
```
├── .gitignore            # Git忽略文件配置
├── .vs/                  # Visual Studio配置目录
├── LICENSE               # 开源许可证
├── README.md             # 项目说明文档
├── angstrom_results.csv  # Angstrom参数结果数据
├── app.py                # 主应用程序文件，包含Flask路由和PCSE模拟实现
├── data/                 # 数据文件目录
│   ├── Wofost71_WLP_FD.conf # WOFOST模型配置文件
│   ├── agro/             # 农业管理数据文件
│   ├── crop/             # 作物数据文件
│   ├── meteo/            # 气象数据文件
│   ├── obs/              # 观测数据文件
│   ├── output/           # 输出数据目录
│   ├── site/             # 站点数据文件
│   ├── soil/             # 土壤数据文件
│   ├── wofost_npk.site   # WOFOST NPK站点配置
│   └── wofost_npk.soil   # WOFOST NPK土壤配置
├── nasa_to_excel_simple.py # NASA天气数据转换工具
├── requirements.txt      # 项目依赖列表
├── static/               # 静态资源文件
│   ├── css/              # CSS样式文件
│   └── js/               # JavaScript文件（包含图表和交互逻辑）
├── templates/            # HTML模板文件
│   ├── datainput.html    # 数据输入页面
│   ├── index.html        # 主页面模板
│   ├── layout.html       # 布局模板
│   └── weather_input.html # 天气数据输入页面
└── yaml_agro_writer.py   # YAML格式农业管理文件生成工具
```

## 功能特性

### 作物模拟功能
- 支持多种作物类型的生长模拟
- 每种作物提供至少一个品种选项
- 可设置模拟天数、开始日期和地理位置
- 支持上传自定义天气文件
- 可选择农业管理文件

### 数据可视化
- 实时显示生物量变化图表
- 展示叶面积指数变化趋势
- 显示预估产量变化曲线
- 所有图表支持响应式布局

### 数据处理
- 集成NASA POWER气象数据API
- 支持Excel格式天气数据导入
- 自动修复Excel天气文件中的Angstrom参数错误
- 提供YAML格式农业管理数据支持

### 错误处理
- 完善的异常捕获和错误提示机制
- 针对常见错误提供详细的诊断信息
- 自动备份原始数据以防数据丢失

## 安装与配置

### 系统要求
- Python 3.8或更高版本
- pip包管理器
- 网络连接（用于获取NASA气象数据）

### 安装步骤

1. **克隆或下载项目代码**

2. **创建虚拟环境（可选但推荐）**
```powershell
# Windows环境
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac环境
source .venv/bin/activate
```

3. **安装依赖包**
```powershell
pip install -r requirements.txt
```

4. **启动应用程序**
```powershell
python app.py
```

5. **访问Web界面**
打开浏览器，访问 `http://localhost:5000`

## 使用指南

### 基础模拟流程

1. **设置模拟参数**
   - 在"参数设置"面板中，选择作物名称和品种
   - 设置模拟天数（7-400天）
   - 输入地理位置的纬度和经度
   - 选择开始日期
   - （可选）上传自定义天气文件或农业管理文件

2. **运行模拟**
   - 点击"运行模拟"按钮
   - 等待模拟完成（时间取决于模拟天数）

3. **查看结果**
   - 模拟完成后，系统将自动显示三个图表：
     - 生物量变化（g/m²）
     - 叶面积指数变化
     - 预估产量变化

### 天气数据处理

1. **使用默认天气数据**
   - 系统会根据提供的经纬度自动从NASA获取天气数据
   - 如果无法获取，将使用本地的示例天气数据

2. **上传自定义天气数据**
   - 点击"浏览"按钮选择Excel格式的天气文件
   - 文件必须符合PCSE ExcelWeatherDataProvider的格式要求
   - 如果文件中存在Angstrom参数错误，可以使用提供的修复工具

### YAML农业管理文件生成

项目提供了`yaml_agro_writer.py`工具，用于生成符合PCSE格式的农业管理YAML文件：

```powershell
python yaml_agro_writer.py
```

## 支持的作物类型

平台支持多种作物类型的模拟，包括但不限于：

- barley (大麦)
- cassava (木薯)
- chickpea (鹰嘴豆)
- cotton (棉花)
- cowpea (豇豆)
- fababean (蚕豆)
- groundnut (花生)
- maize (玉米)
- millet (小米)
- mungbean (绿豆)
- pigeonpea (木豆)
- potato (土豆)
- rapeseed (油菜籽)
- rice (水稻)
- rye_grass (黑麦草)
- sorghum (高粱)
- soybean (大豆)
- sugarbeet (甜菜)
- sugarcane (甘蔗)
- sunflower (向日葵)
- sweetpotato (甘薯)
- tobacco (烟草)
- wheat (小麦)

## 常见问题解答

### 模拟过程中出现错误怎么办？
- 检查输入参数是否有效
- 确认上传的文件格式是否正确
- 查看浏览器控制台输出以获取详细错误信息
- 使用项目提供的测试工具检查数据文件

### 天气数据获取失败怎么办？
- 确认您的网络连接正常
- 检查经纬度值是否有效
- 尝试上传本地天气文件

### 如何查看或修改日志？
- 模拟过程中的日志会显示在服务器控制台
- 部分详细日志保存在debug_output.log文件中

## 开发说明

### 添加新的作物类型
要添加新的作物类型，需要修改app.py中的crop_names列表和variety_names字典，确保所有页面使用相同的作物定义。同时，确保data/crop/目录中存在相应的作物数据文件。

### 修改模拟模型参数
所有与PCSE模型相关的参数设置都在PCSESimulator类中实现，可以根据需要修改以下方法：
- get_crop_provider(): 设置作物相关参数
- get_soil_provider(): 设置土壤相关参数
- get_site_provider(): 设置站点相关参数
- get_agromanagement(): 设置农业管理相关参数

## 免责声明
本平台仅供研究和教育目的使用。模拟结果基于PCSE模型计算得出，可能与实际生长情况存在差异。在实际农业生产中，请结合当地实际情况和专家建议进行决策。

## 版权信息
本项目基于MIT许可证开源。