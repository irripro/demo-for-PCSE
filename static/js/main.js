document.addEventListener('DOMContentLoaded', () => {
    // 获取模拟按钮元素（使用更安全的方式）
    const simulateBtn = document.getElementById('simulate-btn') || { addEventListener: () => {} };
    let biomassChart = null;
    let laiChart = null;
    let yieldChart = null;
    
    // 在DOM完全渲染后延迟显示示例数据
    setTimeout(() => {
        console.log('DOM完全渲染，显示示例数据');
        const mockData = generateMockData(30);
        updateCharts(mockData);
    }, 100);

    // 初始化生物量图表
    function initBiomassChart() {
        const ctx = document.getElementById('biomass-chart').getContext('2d');
        biomassChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: '生物量 (kg/ha)',
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.1)',
                        data: [],
                        tension: 0.1,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: '生物量 (kg/ha)'
                        },
                        beginAtZero: true
                    },
                    x: {
                        title: {
                            display: true,
                            text: '生长天数'
                        }
                    }
                }
            }
        });
    }

    // 初始化叶面积指数图表
    function initLaiChart() {
        const ctx = document.getElementById('lai-chart').getContext('2d');
        laiChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: '叶面积指数',
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.1)',
                        data: [],
                        tension: 0.1,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: '叶面积指数'
                        },
                        beginAtZero: true
                    },
                    x: {
                        title: {
                            display: true,
                            text: '生长天数'
                        }
                    }
                }
            }
        });
    }

    // 初始化产量图表
    function initYieldChart() {
        const ctx = document.getElementById('yield-chart').getContext('2d');
        yieldChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: '预估产量 (kg/ha)',
                        borderColor: 'rgb(54, 162, 235)',
                        backgroundColor: 'rgba(54, 162, 235, 0.1)',
                        data: [],
                        tension: 0.1,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: '预估产量 (kg/ha)'
                        },
                        beginAtZero: true
                    },
                    x: {
                        title: {
                            display: true,
                            text: '生长天数'
                        }
                    }
                }
            }
        });
    }

    // 生成示例数据用于显示
    function generateMockData(days) {
        const mockData = [];
        for (let i = 0; i < days; i++) {
            mockData.push({
                day: i + 1,
                date: new Date(Date.now() + i * 86400000).toISOString().split('T')[0],
                biomass: 10 * Math.exp(0.05 * i),
                lai: 5 / (1 + Math.exp(-0.1 * (i - 15))),
                yield: 3 * Math.exp(0.05 * i) * (1 - Math.exp(-0.03 * i)),
                height: 60 * (1 - Math.exp(-0.05 * i)),
                roots: 5 * Math.exp(0.04 * i),
                water_stress: 0.8 + 0.2 * Math.sin(i/8),
                is_day_130: 0
            });
        }
        return mockData;
    }
    
    // 更新三个图表数据
    function updateCharts(data) {
        console.log('更新图表数据，共', data.length, '条记录');
        
        // 初始化所有图表（如果尚未初始化）
        if (!biomassChart) initBiomassChart();
        if (!laiChart) initLaiChart();
        if (!yieldChart) initYieldChart();

        // 准备标签数据
        const labels = data.map(item => item.day || '');

        // 安全地获取和处理数据，避免类型错误
        // 安全地获取和处理数据，确保返回数字类型
        function safeGetData(field) {
            return data.map(item => {
                const value = item[field];
                if (value === undefined || value === null) return 0;
                // 确保值是数字
                const numValue = parseFloat(value);
                const result = isNaN(numValue) ? 0 : numValue;
                
                // 对于生物量数据，需要从g/m²转换为kg/ha (1 g/m² = 10 kg/ha)
                if (field === 'biomass') {
                    return result ;
                }
                
                return result;
            });
        }

        // 更新生物量图表
        biomassChart.data.labels = labels;
        biomassChart.data.datasets[0].data = safeGetData('biomass');
        biomassChart.update();

        // 更新叶面积指数图表
        laiChart.data.labels = labels;
        laiChart.data.datasets[0].data = safeGetData('lai');
        laiChart.update();

        // 更新产量图表
        yieldChart.data.labels = labels;
        yieldChart.data.datasets[0].data = safeGetData('yield');
        yieldChart.update();
    }

    // 更新品种选项
    function updateVarietyOptions() {
        // 获取选中的作物
        const cropSelect = document.getElementById('crop_name');
        const selectedCrop = cropSelect.value;
        const varietySelect = document.getElementById('variety_name');
        
        // 清空当前的品种选项
        varietySelect.innerHTML = '';
        
        // 作物种类及其对应的品种字典
        const dict_of_crop_sorts = {
            'barley':'Spring_barley_301', 
            'cassava':'Cassava_VanHeemst_1988', 
            'chickpea':'Chickpea_VanHeemst_1988', 
            'cotton':'Cotton_VanHeemst_1988', 
            'cowpea':'Cowpea_VanHeemst_1988', 
            'fababean':'Faba_bean_801', 
            'groundnut':'Groundnut_VanHeemst_1988', 
            'maize':'Maize_VanHeemst_1988', 
            'millet':'Millet_VanHeemst_1988', 
            'mungbean':'Mungbean_VanHeemst_1988', 
            'pigeonpea':'Pigeonpea_VanHeemst_1988', 
            'potato':'Potato_701', 
            'rapeseed':'Oilseed_rape_1001', 
            'rice':'Rice_501', 
            'sorghum':'Sorghum_VanHeemst_1988', 
            'soybean':'Soybean_901', 
            'sugarbeet':'Sugarbeet_601', 
            'sugarcane':'Sugarcane_VanHeemst_1988', 
            'sunflower':'Sunflower_1101', 
            'sweetpotato':'Sweetpotato_VanHeemst_1988', 
            'tobacco':'Tobacco_VanHeemst_1988', 
            'wheat':'Winter_wheat_101'
        };
        
        // 获取选中作物对应的品种
        let varieties = [];
        
        if (dict_of_crop_sorts.hasOwnProperty(selectedCrop)) {
            // 为每种作物至少提供一个默认品种
            varieties = [dict_of_crop_sorts[selectedCrop]];
            
            // 对特定作物可以添加额外的品种选项
            if (selectedCrop === 'potato') {
                varieties.push('Potato_702');
            }
        } else {
            // 如果作物不在字典中，提供一些通用品种选项
            varieties = ['Default_1', 'Default_2'];
        }
        
        // 添加品种选项
        varieties.forEach(variety => {
            let opt = document.createElement('option');
            opt.value = variety;
            opt.textContent = variety;
            varietySelect.appendChild(opt);
        });
    }

    // 发送模拟请求
    async function runSimulation() {
        const days = document.getElementById('days').value;
        const initial_biomass = document.getElementById('initial_biomass').value;
        const growth_rate = document.getElementById('growth_rate').value;
        const crop_name = document.getElementById('crop_name').value;
        const variety_name = document.getElementById('variety_name').value;
        const weather_file_input = document.getElementById('weather_file');
        const weather_file = weather_file_input && weather_file_input.files && weather_file_input.files.length > 0 ? weather_file_input.files[0] : null;

        try {
            // 安全地获取所有表单元素
            const start_date_input = document.getElementById('start_date');
            const end_date_input = document.getElementById('end_date');
            const days_input = document.getElementById('days');
            const initial_biomass_input = document.getElementById('initial_biomass');
            const growth_rate_input = document.getElementById('growth_rate');
            const crop_name_input = document.getElementById('crop_name');
            const variety_name_input = document.getElementById('variety_name');
            const weather_file_input = document.getElementById('weather_file');
            
            // 获取值，如果元素不存在则使用默认值
            const start_date = start_date_input ? start_date_input.value : '2020-03-01';
            const end_date = end_date_input ? end_date_input.value : '2020-09-01';
            const days = days_input ? days_input.value : 30;
            const initial_biomass = initial_biomass_input ? initial_biomass_input.value : 0;
            const growth_rate = growth_rate_input ? growth_rate_input.value : 0.03;
            const crop_name = crop_name_input ? crop_name_input.value : 'potato';
            const variety_name = variety_name_input ? variety_name_input.value : 'Potato_701';
            const weather_file = weather_file_input && weather_file_input.files && weather_file_input.files.length > 0 ? weather_file_input.files[0] : null;
            
            // 如果选择了天气文件，先上传文件
            let weather_filename = 'example_weather.xlsx'; // 默认天气文件
            if (weather_file) {
                const formData = new FormData();
                formData.append('weather_file', weather_file);
                
                const uploadResponse = await fetch('/upload_weather_file', {
                    method: 'POST',
                    body: formData
                });
                
                const uploadResult = await uploadResponse.json();
                if (uploadResult.success) {
                    weather_filename = uploadResult.filename;
                    console.log('天气文件上传成功:', weather_filename);
                } else {
                    console.warn('天气文件上传失败，将使用默认天气数据:', uploadResult.error);
                }
            } else {
                console.log('未选择天气文件，将使用默认天气数据:', weather_filename);
            }
            
            const params = {
                days: days,
                initial_biomass: initial_biomass,
                growth_rate: growth_rate,
                crop_name: crop_name,
                variety_name: variety_name,
                weather_file: weather_filename,
                start_date: start_date, // 添加开始日期参数
                end_date: end_date      // 添加结束日期参数
            };
            
            console.log('发送模拟请求参数:', params);

            const response = await fetch('/simulate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(params)
            });

            // 检查响应状态
            if (!response.ok) {
                console.error('服务器返回错误状态:', response.status, response.statusText);
                // 尝试获取错误详情
                let errorText;
                try {
                    // 尝试解析可能的JSON错误信息
                    const errorData = await response.json();
                    errorText = errorData.error || `服务器错误: ${response.status}`;
                } catch (jsonError) {
                    // 如果无法解析JSON，假设返回的是HTML
                    errorText = `服务器返回非JSON内容，请检查服务器日志`;
                }
                throw new Error(errorText);
            }

            const result = await response.json();
            console.log('从服务器获取的完整结果:', result);
            
            // 检查结果数据结构
            if (result && result.results && Array.isArray(result.results) && result.results.length > 0) {
                console.log('找到有效的结果数据，共', result.results.length, '条记录');
                updateCharts(result.results);
            } else {
                // 检查是否有其他格式的结果数据
                if (result && Array.isArray(result) && result.length > 0) {
                    console.log('使用替代格式的结果数据');
                    updateCharts(result);
                } else {
                    console.warn('没有找到有效的结果数据，显示示例数据');
                    // 生成示例数据用于显示
                    const mockData = generateMockData(30);
                    updateCharts(mockData);
                }
            }
        } catch (error) {
            console.error('模拟出错:', error);
            alert(`模拟过程中出现错误: ${error.message}`);
            
            // 显示示例数据，确保用户至少能看到图表
            console.log('显示示例数据代替真实数据');
            const mockData = generateMockData(30);
            updateCharts(mockData);
        }
    }

    // 添加模拟按钮点击事件监听器
    simulateBtn.addEventListener('click', runSimulation);
    
    // 添加作物选择变化事件监听器
    const cropSelect = document.getElementById('crop_name');
    if (cropSelect) {
        cropSelect.addEventListener('change', updateVarietyOptions);
        // 页面加载完成后立即初始化品种选项
        updateVarietyOptions();
    }
});