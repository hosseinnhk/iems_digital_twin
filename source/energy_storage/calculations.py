from scipy.integrate import quad
import numpy as np


def f_soc(Q, Qmax):

    soc = Q / Qmax
    return soc

def f_soc_avg(Qt_1, Qt, Qmax):
    
    delta_Qt = Qt - Qt_1
    soc_avg, _ = quad(lambda Q: f_soc(Q, Qmax), Qt_1, Qt)
    soc_avg = soc_avg / delta_Qt
    return soc_avg

def f_soc_dev(Qt_1, Qt, Qmax):
    
    delta_Qt = Qt - Qt_1
    soc_avg = f_soc_avg(Qt_1, Qt, Qmax)
    integral_result, _ = quad(lambda Q: (f_soc(Q, Qmax) - soc_avg) ** 2, Qt_1, Qt)
    soc_dev = np.sqrt(abs((3 / delta_Qt) * integral_result))
    return soc_dev

def f_Fi(soc_dev, soc_avg):
    
    F = (ess.k_s1 * soc_dev * np.exp(ess.k_s2 * soc_avg) + ess.k_s3 * np.exp(ess.k_s4 * soc_dev))
    return F

def f_c_cycle(F, Q, Ea, R, T, T_ref):

    c_cycle = sum(F[i] * abs(Q[i]-Q[i-1]) * np.exp(( -Ea / R ) * (1 / T - 1 / T_ref)) for i in range(len(F)))
    return c_cycle

def f_c_cal_1h(soc_1h_avg):

    c_cal_1h = (6.6148 * soc_1h_avg + 4.6404) * 10**-6
    return c_cal_1h

def f_c_cal(c_cal_1h_list):

    c_cal = sum(c_cal_1h_list)
    return c_cal

def f_c_cycle_day(c_cycle_1h_list):

    c_cycle_day= sum(c_cycle_1h_list)
    return c_cycle_day

def f_soh(c_cal, c_cycel, c_nm):
    c_fd = c_cal + 100 * c_cycel/c_nm
    # soh = 100 - c_fd
    return c_fd


def soh_daily_change(Qt, Qmax):
    
    c_cal_day = []
    c_cycle_day = []
    
    for i in range(int(len(Qt)/24)): # 0-23
        Fi = []
        Qi = []
        socAvg_1h = 0.0
        
        # first we calculate for each hour: 
        for j in range(12): # 0-11
            if i*12+j-1 > 0 : 
                socAvg = f_soc_avg(Qt[i*12+j-1], Qt[i*12+j], Qmax)
                socDev = f_soc_dev(Qt[i*12+j-1], Qt[i*12+j], Qmax)
                Fi.append(f_Fi(socAvg, socDev))
                Qi.append(Qt[i*12+j])
                socAvg_1h += socAvg 
                  
        c_cycle_1h  = f_c_cycle(Fi, Qi, ess.E_a, ess.R, ess.T_i, ess.T_ref)
        c_cal_1h = f_c_cal_1h(socAvg_1h/12)
        c_cal_day.append(c_cal_1h)
        c_cycle_day.append(c_cycle_1h)
        
    c_cal = f_c_cal(c_cal_day)
    c_cycle = f_c_cycle_day(c_cycle_day)
    delta_soh = f_soh(c_cal, c_cycle, Qmax)       
    if delta_soh< 0: 
        delta_soh = 0
    return delta_soh



def ess_soc_to_voltage (model):
    soc = value(model.ess_soc(t))
    voltage = (soc+735)/250
    voltage = int(voltage*100)
    # voltage = 330
    return voltage