"""
Модуль для массового расчета скважин, оснащенных УЭЦН

Кобзарь О.С Хабибуллин Р.А. 21.08.2019
"""
calc_mark_str = "1354_big_run_5"
# TODO отрефакторить
# TODO перепад давления в насосе
# TODO сразу ошибка для определения дебита на фактических точках
# TODO интеграл
# TODO произведение калибровок
# TODO поверхность решения
# TODO принять ГФ газосодержанию?
# TODO изменение функции ошибки (деление на максимум, добавление линейного давления, добавления штуцера с другой стороны)
import description_generated.python_api as python_api
from scipy.optimize import minimize
import pandas as pd
UniflocVBA = python_api.API("UniflocVBA_7.xlam")
import sys
import xlwings as xw
sys.path.append("../")
import datetime
import time

class all_ESP_data():
    def __init__(self):
        self.esp_id = UniflocVBA.calc_ESP_id_by_rate(320)
        self.gamma_oil = 0.945
        self.gamma_gas = 0.9
        self.gamma_wat = 1.011
        self.rsb_m3m3 = 29.25
        self.tres_c = 16
        self.pb_atm = 40
        self.bob_m3m3 = 1.045
        self.muob_cp = 100

        self.psep_atm = 30
        self.tsep_c = 30

        self.d_choke_mm = 8
        self.dcas_mm = 160
        self.h_tube_m = 830
        self.d_tube_mm = 75

        self.Power_motor_nom_kWt = 140
        self.ESP_head_nom = 1500
        self.ESP_rate_nom = 320
        self.ESP_freq = 38

        self.rp_m3m3 = 30

        self.p_intake_data_atm = 29.93
        self.p_wellhead_data_atm = 22.70
        self.p_buf_data_atm = 27.0
        self.p_wf_atm = 29.93
        self.p_cas_data_atm = -1

        self.eff_motor_d = 0.89
        self.i_motor_nom_a = 6
        self.power_motor_nom_kwt = 140
        self.i_motor_data_a = 42.94
        self.cos_phi_data_d = 0.70818
        self.load_motor_data_d = 0.55957
        self.u_motor_data_v = 1546.65
        self.active_power_cs_data_kwt = 81.297297

        self.qliq_m3day = 122.2
        self.watercut_perc = 25.6
        self.p_buf_data_atm = 27
        self.h_perf_m = 831
        self.h_pump_m = 830
        self.udl_m = 72

        self.ksep_d = 0.7
        self.KsepGS_fr = 0.7
        self.c_calibr_head_d = None
        self.c_calibr_rate_d = 1
        self.c_calibr_power_d = 1
        self.hydr_corr = 1 # 0 - BB, 1 - Ansari
        self.result = None
        self.error_in_step = None


def mass_calculation(well_state, debug_print = False, restore_flow = False):
    this_state = well_state
    def calc_well_plin_pwf_atma_for_fsolve(minimaze_parameters):
        if restore_flow == False: #TODO изменить коэффициенты для восстановления дебита
            this_state.c_calibr_power_d = minimaze_parameters[1]
            this_state.c_calibr_head_d = minimaze_parameters[0]
            this_state.c_calibr_rate_d = this_state.c_calibr_rate_d
            if debug_print:
                print('c_calibr_power_d = ' + str(this_state.c_calibr_power_d))
                print('c_calibr_head_d = ' + str(this_state.c_calibr_head_d))
        else:
            this_state.qliq_m3day = minimaze_parameters[0]
            this_state.watercut_perc = minimaze_parameters[1]
            if debug_print:
                print('qliq_m3day = ' + str(this_state.qliq_m3day))
                print('watercut_perc = ' + str(this_state.watercut_perc))
        PVTstr = UniflocVBA.calc_PVT_encode_string(this_state.gamma_gas, this_state.gamma_oil,
                                                   this_state.gamma_wat, this_state.rsb_m3m3, this_state.rp_m3m3,
                                                   this_state.pb_atm, this_state.tres_c,
                                                   this_state.bob_m3m3, this_state.muob_cp,
                                                   ksep_fr=this_state.ksep_d, pksep_atma=this_state.psep_atm,
                                                   tksep_C=this_state.tsep_c)
        Wellstr = UniflocVBA.calc_well_encode_string(this_state.h_perf_m,
                                                     this_state.h_pump_m,
                                                     this_state.udl_m,
                                                     this_state.dcas_mm,
                                                     this_state.d_tube_mm,
                                                     this_state.d_choke_mm,
                                                     tbh_C=this_state.tsep_c)
        ESPstr = UniflocVBA.calc_ESP_encode_string(this_state.esp_id,
                                                   this_state.ESP_head_nom,
                                                   this_state.ESP_freq,
                                                   this_state.u_motor_data_v,
                                                   this_state.power_motor_nom_kwt,
                                                   this_state.tsep_c,
                                                   t_dis_C = -1,
                                                   KsepGS_fr=this_state.KsepGS_fr,
                                                   ESP_Hmes_m=this_state.h_tube_m,
                                                   c_calibr_head=this_state.c_calibr_head_d,
                                                   c_calibr_rate=this_state.c_calibr_rate_d,
                                                   c_calibr_power=this_state.c_calibr_power_d,
                                                   cos_phi=this_state.cos_phi_data_d)
        result = UniflocVBA.calc_well_plin_pwf_atma(this_state.qliq_m3day, this_state.watercut_perc,
                                                    this_state.p_wf_atm,
                                                    this_state.p_cas_data_atm, Wellstr,
                                                    PVTstr, ESPstr, this_state.hydr_corr,
                                                    this_state.ksep_d, this_state.c_calibr_head_d, this_state.c_calibr_power_d,
                                                    this_state.c_calibr_rate_d)



        this_state.result = result

        #print(this_state.result)
        p_wellhead_calc_atm = result[0][0]
        p_buf_calc_atm = result[0][2]
        power_CS_calc_W = result[0][16]
        power_regulatization = 1 / 1000
        result_for_folve = (p_buf_calc_atm - this_state.p_buf_data_atm) ** 2 + \
                           (power_regulatization * (power_CS_calc_W - this_state.active_power_cs_data_kwt)) ** 2
        #result_for_folve = (p_wellhead_calc_atm - this_state.p_wellhead_data_atm) ** 2 + \
        #                  (power_regulatization * (power_CS_calc_W - this_state.active_power_cs_data_kwt)) ** 2
        if debug_print:
            #print("this_state.result = \n")
            #print(this_state.result)
            print("power_CS_calc_W = " + str(power_CS_calc_W))
            print("active_power_cs_data_kwt = " + str(this_state.active_power_cs_data_kwt))
            print("ошибка на текущем шаге = " + str(result_for_folve))
        this_state.error_in_step = result_for_folve
        return result_for_folve
    if restore_flow == False:
        result = minimize(calc_well_plin_pwf_atma_for_fsolve, [0.5, 0.5], bounds=[[0, 20], [0, 20]])
    else:
        result = minimize(calc_well_plin_pwf_atma_for_fsolve, [100, 20], bounds=[[1, 150], [10, 35]])

    print(result)
    #print(result.x[0])
    true_result = this_state.result
    return true_result
    #for i in range(len(true_result[0])):
    #    print(str(true_result[1][i]) + " -  " + str(true_result[0][i]))

calc_option = True
debug_mode = True
vfm_calc_option = False
if calc_option == True:
    start = datetime.datetime(2018,8,18)
    end = datetime.datetime(2020,2,27)
    prepared_data = pd.read_csv("stuff_to_merge/1354 _input_data.csv")
    prepared_data.index = pd.to_datetime(prepared_data["Unnamed: 0"])
    prepared_data = prepared_data[(prepared_data.index >= start) & (prepared_data.index <= end)]
    del prepared_data["Unnamed: 0"]

    result_list = []
    result_dataframe = {'d':[2]}
    result_dataframe = pd.DataFrame(result_dataframe)
    start_time = time.time()
    for i in range(prepared_data.shape[0]):
    #for i in range(3):
        check = i % 2
        if check == 0 and i != 0:
            print('Перезапуск Excel и VBA')
            #close_f = UniflocVBA.book.macro('close_book_by_macro')
            #close_f()
            UniflocVBA.book.close()
            time.sleep(5)
            UniflocVBA.book = xw.Book("UniflocVBA_7.xlam")
        start_in_loop_time = time.time()
        row_in_prepared_data = prepared_data.iloc[i]
        print("Расчет для времени:")
        print(prepared_data.index[i])
        print('Итерация № ' + str(i) + ' из ' + str(prepared_data.shape[0]))
        this_state = all_ESP_data()
        this_state.qliq_m3day = row_in_prepared_data['Объемный дебит жидкости (СУ)']
        this_state.watercut_perc = row_in_prepared_data['Процент обводненности (СУ)']
        this_state.rp_m3m3 = row_in_prepared_data['ГФ (СУ)']

        this_state.p_buf_data_atm = row_in_prepared_data['Рбуф (Ш)']
        this_state.p_wellhead_data_atm = row_in_prepared_data['Рлин ТМ (Ш)']

        this_state.tsep_c = row_in_prepared_data['Температура на приеме насоса (пласт. жидкость) (СУ)']
        this_state.tres_c = 16
        this_state.p_intake_data_atm = row_in_prepared_data['Давление на приеме насоса (пласт. жидкость) (СУ)'] * 10
        this_state.psep_atm = row_in_prepared_data['Давление на приеме насоса (пласт. жидкость) (СУ)'] * 10
        this_state.p_wf_atm = row_in_prepared_data['Давление на приеме насоса (пласт. жидкость) (СУ)'] * 10

        this_state.d_choke_mm =  row_in_prepared_data['Dшт (Ш)']

        this_state.active_power_cs_data_kwt = row_in_prepared_data['Активная мощность (СУ)'] * 1000
        this_state.u_motor_data_v = row_in_prepared_data['Напряжение на выходе ТМПН (СУ)']
        this_state.cos_phi_data_d = row_in_prepared_data['Коэффициент мощности (СУ)']
        this_state.c_calibr_rate_d = 1
        if vfm_calc_option == True:
            this_state.c_calibr_head_d = row_in_prepared_data["Коэффициент калибровки по напору - множитель (Модель, вход)"]
            this_state.c_calibr_power_d = row_in_prepared_data["Коэффициент калибровки по мощности - множитель (Модель, вход)"]
        this_result = mass_calculation(this_state, debug_mode, vfm_calc_option)
        result_list.append(this_result)
        end_in_loop_time = time.time()
        print("Затрачено времени в итерации: " + str(i) + " - " + str(end_in_loop_time - start_in_loop_time))
        new_dict = {}
        for j in range(len(this_result[1])):
            new_dict[this_result[1][j]] = [this_result[0][j]]
            print(str(this_result[1][j]) + " -  " + str(this_result[0][j]))
        new_dict['ГФ (модель, вход)'] = [this_state.rp_m3m3]
        new_dict['Значение функции ошибки'] = [this_state.error_in_step]
        new_dict['Time'] = [prepared_data.index[i]]
        new_dataframe = pd.DataFrame(new_dict)
        new_dataframe.index = new_dataframe['Time']
        result_dataframe = result_dataframe.append(new_dataframe, sort=False)
        result_dataframe.to_csv("stuff_to_merge/" + calc_mark_str + "_current.csv")

    end_time = time.time()
    print("Затрачено всего: " + str(end_time - start_time))

    result_dataframe.to_csv("stuff_to_merge/" + calc_mark_str + "_finished.csv")
close_f = UniflocVBA.book.macro('close_book_by_macro')
close_f()