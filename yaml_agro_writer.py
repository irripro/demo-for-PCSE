__author__ = 'wit015'
import sys, os
import yaml
from pcse import exceptions as exc
import datetime as dt
import pandas as pd

class YAMLAgroManagementWriter(list):
    """Reads PCSE agromanagement files in the YAML format.

    :param fname: filename of the agromanagement file. If fname is not provided as a absolute or
        relative path the file is assumed to be in the current working directory.
    """

    def __init__(self, fname,agro_dict):
        fname_fp = os.path.normpath(os.path.abspath(fname))
        if not os.path.exists(fname_fp):
            msg = "Cannot find agromanagement file: %s" % fname_fp
            raise exc.PCSEError(msg)

        with open(fname, 'w') as fp:
            try:
                # r = yaml.safe_load(fp)
                # with open(fp, 'w') as file:
                # r=yaml.dump(agro_dict, fp)
                r=yaml.safe_dump_all(agro_dict, fp)
                # yaml.()
                print('YAMLAgroManagementWriter=',agro_dict)
            except yaml.YAMLError as e:
                msg = "Failed parsing agromanagement file %s: %s" % (fname_fp, e)
                raise exc.PCSEError(msg)

        # list.__init__(self, r['AgroManagement'])

    def __str__(self):
        return yaml.dump(self, default_flow_style=False)

    def agromanager_writer(self, crop_name, dates_irrigation, dates_npk, amounts, npk_list):
        """ 
        Fun to add new irrigation events in agrocalendar
        
        Input: dates - list of date in str format (ex. 2006-07-10)
            amounts - list of water mm in str format (ex. '10')
            
        Example: #add example
        
        """
        #  这段代码定义了一个名为`agromanager_writer`的函数，用于向农业日历（agrocalendar）中添加新的灌溉事件。函数的输入参数包括：作物名称（crop_name）、灌溉日期列表（dates_irrigation）、氮磷钾施肥日期列表（dates_npk）、灌溉水量（amounts）和氮磷钾施肥量列表（npk_list）。

        # 函数首先导入`datetime`模块，并将开始日期（date_start）设置为作物开始日期（date_crop_start）的前两天。然后，创建一个名为`dict_of_crop_sorts`的字典，用于将作物名称映射到相应的英文名称。

        # 接下来，函数创建一个名为`crop_data`的字典，用于存储作物参数。然后，检查灌溉事件和氮磷钾施肥事件是否在同一日期有多个事件，如果有，则删除重复的事件。

        # 最后，函数使用`yaml`模块加载一个模板，并将`crop_data`字典中的数据插入到模板中。同时，将开始日期和结束日期转换为`datetime`对象，并将它们插入到农业管理计划（agromanagement）中。最后，返回生成的农业管理计划。

        # 以下是一个使用`agromanager_writer`函数的示例：

        # ```python
        # crop_name = "wheat"
        # dates_irrigation = ["2022-01-01", "2022-01-02", "2022-01-03"]
        # amounts = [10, 20, 30]
        # dates_npk = ["2022-01-01", "2022-01-02", "2022-01-03"]
        # npk_list = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]

        # agromanagement = agromanager_writer(crop_name, dates_irrigation, dates_npk, amounts, npk_list)
        # print(agromanagement)
        # ```

        # 注意：在实际使用中，需要根据具体需求修改`dict_of_crop_sorts`字典中的作物名称和英文名称。

        # import datetime as dt
        self.date_start = (dt.datetime.strptime(self.date_crop_start, '%Y-%m-%d') - dt.timedelta(days=2)).strftime(format='%Y-%m-%d')

        dict_of_crop_sorts = {'barley':'Spring_barley_301',
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
                    'wheat':'Winter_wheat_101'}

        english_crop_name = crop_name

        english_sort_name = dict_of_crop_sorts[english_crop_name]

        # Generate crop parameters dict for future process
        crop_data = {
        'start_moment':self.date_start,
        'crop_name': english_crop_name,
        'crop_full_name':english_sort_name,
        'crop_start_date': self.date_crop_start,
        'crop_end_date': self.date_crop_end,
        'events_irrigation': [],
        'events_npk':[]
        }

        # check two or more irrigation events for one day - it's problem for model

        if len(set(dates_irrigation)) != len(dates_irrigation):
            dates_irrigation=list(set(dates_irrigation))
            amounts = amounts[:len(set(dates_irrigation))]

        if len(set(dates_npk)) != len(dates_npk):
            dates_npk=list(set(dates_npk))
            amounts = amounts[:len(set(dates_npk))]

        crop_data['events_irrigation'] = [{date: amount for (date, amount) in zip(dates_irrigation, amounts)}]

        crop_data['events_npk']=[{date: npk for (date, npk) in zip(dates_npk, npk_list)}]

        template = """        
- 2000-01-01:
    CropCalendar:
        crop_name: sugarbeet
        variety_name: Sugarbeet_601
        crop_start_date: 2000-02-02
        crop_start_type: emergence
        crop_end_date: 2000-03-03
        crop_end_type: harvest
        max_duration: 300
    TimedEvents:
    -   event_signal: irrigate
        name: Irrigation application table
        comment: All irrigation amounts in cm
        events_table: 
        - 2018-07-07: {amount: 10, efficiency: 0.7}
    -   event_signal: apply_npk
        name:  Timed N/P/K application table
        comment: All fertilizer amounts in kg/ha
        events_table:
        - 2000-01-10: {N_amount : 10, P_amount: 5, K_amount: 2}
    StateEvents: null""" 

        crop_start = yaml.safe_load(crop_data['crop_start_date'])
        crop_end = yaml.safe_load(crop_data['crop_end_date'])

        agromanag = yaml.safe_load(template)
        agromanag[0][crop_start - dt.timedelta(days=2)] = agromanag[0].pop(dt.date(2000, 1, 1)) 
        x = (list(agromanag[0].items())[0][0])
        agromanag[0][x]['CropCalendar']['crop_name'] = english_crop_name
        agromanag[0][x]['CropCalendar']['variety_name'] = english_sort_name
        agromanag[0][x]['CropCalendar']['crop_start_date'] = crop_start
        agromanag[0][x]['CropCalendar']['crop_end_date'] = crop_end
        agromanag[0][x]['TimedEvents'][0]['events_table'].clear()
        agromanag[0][x]['TimedEvents'][1]['events_table'].clear()

        if bool(crop_data['events_irrigation'][0]):
            for date,amount in zip(dates_irrigation, amounts):
                agromanag[0][x]['TimedEvents'][0]['events_table'].append({yaml.safe_load(date):{'amount': float(amount), 'efficiency': 0.7}})
            if bool(crop_data['events_npk'][0]):
                for date, npk in zip(dates_npk, npk_list):
                    agromanag[0][x]['TimedEvents'][1]['events_table'].append({yaml.safe_load(date):{'N_amount' : npk[0], 'P_amount': npk[1], 'K_amount': npk[2], 'N_recovery':0.7, 'P_recovery':0.7, 'K_recovery':0.7}})
            else:
                # agromanagement[0][x]['TimedEvents'][:1]
                agromanag[0][x]['TimedEvents'].pop()
        else:
            agromanag[0][x]['TimedEvents'] = None
        return agromanag
    def agro_writer( crop_name, dates_irrigation, dates_npk, amounts, npk_list):
        """ 
        Fun to add new irrigation events in agrocalendar
        
        Input: dates - list of date in str format (ex. 2006-07-10)
            amounts - list of water mm in str format (ex. '10')
            
        Example: #add example
        
        """

        #  这段代码定义了一个名为`agromanager_writer`的函数，用于向农业日历（agrocalendar）中添加新的灌溉事件。函数的输入参数包括：作物名称（crop_name）、灌溉日期列表（dates_irrigation）、氮磷钾施肥日期列表（dates_npk）、灌溉水量（amounts）和氮磷钾施肥量列表（npk_list）。

        # 函数首先导入`datetime`模块，并将开始日期（date_start）设置为作物开始日期（date_crop_start）的前两天。然后，创建一个名为`dict_of_crop_sorts`的字典，用于将作物名称映射到相应的英文名称。

        # 接下来，函数创建一个名为`crop_data`的字典，用于存储作物参数。然后，检查灌溉事件和氮磷钾施肥事件是否在同一日期有多个事件，如果有，则删除重复的事件。

        # 最后，函数使用`yaml`模块加载一个模板，并将`crop_data`字典中的数据插入到模板中。同时，将开始日期和结束日期转换为`datetime`对象，并将它们插入到农业管理计划（agromanagement）中。最后，返回生成的农业管理计划。

        # 以下是一个使用`agromanager_writer`函数的示例：

        # ```python
        # crop_name = "wheat"
        # dates_irrigation = ["2022-01-01", "2022-01-02", "2022-01-03"]
        # amounts = [10, 20, 30]
        # dates_npk = ["2022-01-01", "2022-01-02", "2022-01-03"]
        # npk_list = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]

        # agromanagement = agromanager_writer(crop_name, dates_irrigation, dates_npk, amounts, npk_list)
        # print(agromanagement)
        # ```

        # 注意：在实际使用中，需要根据具体需求修改`dict_of_crop_sorts`字典中的作物名称和英文名称。

        # 
        print(npk_list)

        # self.date_start = (dt.datetime.strptime(self.date_crop_start, '%Y-%m-%d') - dt.timedelta(days=2)).strftime(format='%Y-%m-%d')

        dict_of_crop_sorts = {'barley':'Spring_barley_301',
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
                    'wheat':'Winter_wheat_101'}

        english_crop_name = crop_name

        english_sort_name = dict_of_crop_sorts[english_crop_name]

        # Generate crop parameters dict for future process
        crop_data = {
        'start_moment':self.date_start,
        'crop_name': english_crop_name,
        'crop_full_name':english_sort_name,
        'crop_start_date': self.date_crop_start,
        'crop_end_date': self.date_crop_end,
        'events_irrigation': [],
        'events_npk':[]
        }

        # check two or more irrigation events for one day - it's problem for model

        if len(set(dates_irrigation)) != len(dates_irrigation):
            dates_irrigation=list(set(dates_irrigation))
            amounts = amounts[:len(set(dates_irrigation))]

        if len(set(dates_npk)) != len(dates_npk):
            dates_npk=list(set(dates_npk))
            amounts = amounts[:len(set(dates_npk))]

        crop_data['events_irrigation'] = [{date: amount for (date, amount) in zip(dates_irrigation, amounts)}]

        crop_data['events_npk']=[{date: npk for (date, npk) in zip(dates_npk, npk_list)}]

        template = """        
Version: 1.0
AgroManagement:
- 2020-04-09:
    CropCalendar:
      crop_name: potato
      variety_name: Potato_701
      crop_start_date: 2020-04-21
      crop_start_type: sowing
      crop_end_date: 2020-09-24
      crop_end_type: harvest
      max_duration: 400
    TimedEvents:
    - event_signal: irrigate
      name: Irrigation application table
      comment: All irrigation amounts in cm
      events_table:
      - 2020-04-09:
          amount: 0.0
          efficiency: 1
      - 2020-07-02:
          amount: 0.00
          efficiency: 1
      - 2020-08-01:
          amount: 0.00
          efficiency: 1
    - event_signal: apply_n_snomin
      name: Timed N application table
      comment: All fertilizer N amounts in kg/ha
      events_table:
      - 2020-04-09:
          amount: 125
          application_depth: 10
          cnratio: 0
          f_orgmat: 0
          f_NH4N: 0.5
          f_NO3N: 0.5
          initial_age: 0
      - 2020-05-01:
          amount: 85
          application_depth: 10
          cnratio: 0
          f_orgmat: 0
          f_NH4N: 0.5
          f_NO3N: 0.5
          initial_age: 0
      - 2020-06-16:
          amount: 110
          application_depth: 10
          cnratio: 0
          f_orgmat: 0
          f_NH4N: 0.5
          f_NO3N: 0.5
          initial_age: 0
    StateEvents: null
        """ 

        crop_start = yaml.safe_load(crop_data['crop_start_date'])
        crop_end = yaml.safe_load(crop_data['crop_end_date'])

        agromanag = yaml.safe_load(template)
        agromanag[0][crop_start - dt.timedelta(days=2)] = agromanag[0].pop(dt.date(2000, 1, 1)) 
        x = (list(agromanag[0].items())[0][0])
        agromanag[0][x]['CropCalendar']['crop_name'] = english_crop_name
        agromanag[0][x]['CropCalendar']['variety_name'] = english_sort_name
        agromanag[0][x]['CropCalendar']['crop_start_date'] = crop_start
        agromanag[0][x]['CropCalendar']['crop_end_date'] = crop_end
        agromanag[0][x]['TimedEvents'][0]['events_table'].clear()
        agromanag[0][x]['TimedEvents'][1]['events_table'].clear()

        if bool(crop_data['events_irrigation'][0]):
            for date,amount in zip(dates_irrigation, amounts):
                agromanag[0][x]['TimedEvents'][0]['events_table'].append({yaml.safe_load(date):{'amount': float(amount), 'efficiency': 0.7}})
            if bool(crop_data['events_npk'][0]):
                for date, npk in zip(dates_npk, npk_list):
                    agromanag[0][x]['TimedEvents'][1]['events_table'].append({yaml.safe_load(date):{'N_amount' : npk[0], 'P_amount': npk[1], 'K_amount': npk[2], 'N_recovery':0.7, 'P_recovery':0.7, 'K_recovery':0.7}})
            else:
                # agromanagement[0][x]['TimedEvents'][:1]
                agromanag[0][x]['TimedEvents'].pop()
        else:
            agromanag[0][x]['TimedEvents'] = None
        return agromanag
    def year_changer(self, obj, year):

        """
        Util function to change user year to new year
        
        
        Input: str - date event in format '%Y-%m-%d'
        
        Output: str - new date event in format '%Y-%m-%d'
        
        """
        #  这段Python代码定义了一个名为`year_changer`的函数，其功能是将用户指定的日期（格式为'%Y-%m-%d'）转换为新的年份。该函数的输入参数为一个日期字符串`obj`和一个年份`year`，输出参数为一个新的日期字符串。

        # 函数内部的实现原理如下：

        # 1. 首先，定义了一个日期格式字符串`type_of_dt`，用于指定输入和输出的日期格式。

        # 2. 计算了用户指定的年份与当前年份之间的差值`year_delta`。

        # 3. 使用`dt.datetime.strptime`将输入的日期字符串`obj`转换为`dt.datetime`对象，并使用`relativedelta`减去`year_delta`年。

        # 4. 使用`dt.datetime.strftime`将计算出的新的日期对象转换为新的日期字符串`updated_date`。

        # 5. 返回新的日期字符串`updated_date`。

        # 该函数可以用于将用户指定的日期转换为新的年份，例如，如果用户指定了一个日期`2021-01-01`，并且希望将其转换为`2022-01-01`，则可以使用该函数实现这一功能。

        # 在使用该函数时，需要注意以下几点：

        # 1. 输入的日期字符串`obj`必须符合`'%Y-%m-%d'`的格式，否则会抛出`ValueError`异常。

        # 2. 如果用户指定的年份与当前年份之间的差值`year_delta`为负数，则新的日期年份将为当前年份减去`year_delta`。

        # 3. 如果用户指定的年份与当前年份之间的差值`year_delta`为正数，则新的日期年份将为当前年份加上`year_delta`。

        type_of_dt = '%Y-%m-%d'
        updated_date=obj
        year_delta = int(self.user_parameters['crop_end'][:4]) - year

        if year_delta !=0:
            year_delta = abs(year_delta)
            dt_date_crop_start=dt.datetime.strptime(obj, type_of_dt) - relativedelta(years=year_delta)
            updated_date = dt.datetime.strftime(dt_date_crop_start, type_of_dt) 

        return updated_date

    # import pandas as pd
    # from datetime import date

    # 给定的字典数据
    # data = {
    #     'CropCalendar': {
    #         'crop_name': 'potato',
    #         'variety_name': 'Potato_701',
    #         'crop_start_date': date(2020, 4, 21),
    #         'crop_start_type': 'sowing',
    #         'crop_end_date': date(2020, 9, 24),
    #         'crop_end_type': 'harvest',
    #         'max_duration': 400
    #     },
    #     'TimedEvents': [
    #         {
    #             'event_signal': 'irrigate',
    #             'name': 'Irrigation application table',
    #             'comment': 'All irrigation amounts in cm',
    #             'events_table': [
    #                 {date(2020, 4, 9): {'amount': 0.0, 'efficiency': 1}},
    #                 {date(2020, 7, 2): {'amount': 0.0, 'efficiency': 1}},
    #                 {date(2020, 8, 1): {'amount': 0.0, 'efficiency': 1}}
    #             ]
    #         },
    #         {
    #             'event_signal': 'apply_n_snomin',
    #             'name': 'Timed N application table',
    #             'comment': 'All fertilizer N amounts in kg/ha',
    #             'events_table': [
    #                 {date(2020, 4, 9): {'amount': 125, 'application_depth': 10, 'cnratio': 0, 'f_orgmat': 0, 'f_NH4N': 0.5, 'f_NO3N': 0.5, 'initial_age': 0}},
    #                 {date(2020, 5, 1): {'amount': 85, 'application_depth': 10, 'cnratio': 0, 'f_orgmat': 0, 'f_NH4N': 0.5, 'f_NO3N': 0.5, 'initial_age': 0}},
    #                 {date(2020, 6, 16): {'amount': 110, 'application_depth': 10, 'cnratio': 0, 'f_orgmat': 0, 'f_NH4N': 0.5, 'f_NO3N': 0.5, 'initial_age': 0}}
    #             ]
    #         }
    #     ],
    #     'StateEvents': None
    # }

    # 提取 CropCalendar 数据
    def write_to_excel(data,fname):
        firstkey = list(data[0])[0]
        cropcalendar = data[0][firstkey]['CropCalendar'] 

        crop_calendar_df = pd.DataFrame([cropcalendar])
        print(crop_calendar_df)

        timedevents = data[0][firstkey]['TimedEvents'] 
        print(timedevents)

        # 提取 TimedEvents 数据
        timed_events_data = []
        for event in timedevents : #timedevents['TimedEvents']:
            event_signal = event['event_signal']
            name = event['name']
            comment = event['comment']
            for event_entry in event['events_table']:
                for event_date, details in event_entry.items():
                    timed_event = {
                        'event_signal': event_signal,
                        'name': name,
                        'comment': comment,
                        'event_date': event_date,
                        **details
                    }
                    timed_events_data.append(timed_event)

        timed_events_df = pd.DataFrame(timed_events_data)


        # print("1=",pd.DataFrame(data))
        # print("2=",pd.DataFrame(data[0]))
        # print(f"3 = {pd.DataFrame(data[0][firstkey])}") #"pd.DataFrame(data[0][0]))

        # crop_begin_df=pd.DataFrame(data[0][firstkey])
        crop_begin_df=pd.DataFrame(data[0])

        # 创建一个 Excel writer 对象'agricultural_data.xlsx' 
        with pd.ExcelWriter(fname) as writer:
            # 将 AgroData 数据写入 Excel 的第一个 sheet
            
            crop_begin_df.to_excel(writer, sheet_name='AgroData', index=False)

            # firstkey = list(agro_dict[0])[0]
            # 将 CropCalendar 数据写入 Excel 的第二个 sheet

            crop_calendar_df.to_excel(writer, sheet_name='CropCalendar', index=False)
    
            # 将 TimedEvents 数据写入 Excel 的第三个 sheet
            timed_events_df.to_excel(writer, sheet_name='TimedEvents', index=False)

        print("Excel file: agricultural_data.xlsx")

        return "Excel timed_events_df: agricultural_data.xlsx"

    def read_excel_file(filename):
        # import pandas as pd
        # from datetime import date

        # 读取 Excel 文件
        # file_path = 'agricultural_data.xlsx'

        # 读取 AgroData sheet
        crop_agrodata_df = pd.read_excel(filename, sheet_name='AgroData')

        # 读取 CropCalendar sheet
        crop_calendar_df = pd.read_excel(filename, sheet_name='CropCalendar')

        # 将 CropCalendar DataFrame 转换为字典
        crop_calendar_dict = crop_calendar_df.to_dict(orient='records')[0]

        # 读取 TimedEvents sheet
        timed_events_df = pd.read_excel(filename, sheet_name='TimedEvents')

        # 将 TimedEvents DataFrame 转换为字典列表
        timed_events_list = []
        current_event_signal = None
        current_timed_event = {}

        for index, row in timed_events_df.iterrows():
            event_signal = row['event_signal']
            name = row['name']
            comment = row['comment']
            event_date = row['event_date']

            if current_event_signal != event_signal or not current_timed_event:
                # 如果当前事件信号不同或为空，则创建一个新的事件条目
                if current_timed_event:
                    timed_events_list.append(current_timed_event)
        
                current_event_signal = event_signal
                current_timed_event = {
                    'event_signal': event_signal,
                    'name': name,
                    'comment': comment,
                    'events_table': []
                }
    
            # 添加具体的事件日期和详细信息
            event_details = {
                event_date: {
                    'amount': row['amount'],
                    'efficiency': row.get('efficiency', None),
                    'application_depth': row.get('application_depth', None),
                    'cnratio': row.get('cnratio', None),
                    'f_orgmat': row.get('f_orgmat', None),
                    'f_NH4N': row.get('f_NH4N', None),
                    'f_NO3N': row.get('f_NO3N', None),
                    'initial_age': row.get('initial_age', None)
                }
            }
    
            current_timed_event['events_table'].append(event_details)

        # 添加最后一个事件条目
        if current_timed_event:
            timed_events_list.append(current_timed_event)

        # 构建最终的字典
        final_data = {
            'AgroData': crop_agrodata_df.to_dict(orient='records')[0],
            'CropCalendar': crop_calendar_dict,
            'TimedEvents': timed_events_list,
            'StateEvents': None
        }

        # 打印恢复后的字典
        print(final_data)

        return final_data






