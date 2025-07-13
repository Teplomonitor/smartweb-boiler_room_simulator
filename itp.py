# импортируем модуль
# import time
import tkinter as tk
from tkinter import messagebox, StringVar, ttk
import math
import numpy as np

# начальные условия
tintown = 80 # на входе из города - постоянная ---------------------------
tinhouse_demand = 55 # требуемая температура подачи ----------------------

cw = 4200 # теплоемкость воды

qhouse = 1.5 # расход кг/сек в доме постоянный.
qtown_max = 2 # секундный из города

tservak = 120 # время разворота сервака ---------------------------------
proport = 20 # полоса пропорциональности температуры для сервака
tau=5 # шаг по времени сек

pdiss=100 # примерно равно мощности отопления
#ato = 3300 # теплопередача ТО тоже не трогать
ato = 500
square=1 # Площадь ТО в кв.м.-----------------------

ddt=0
real_time = 0
ugolserv_0 = 0
ugolserv_max=1
qtown = 0 # расход из города при данном угле сервака 
tinhouse = 20 #температура начальная в контуре отопления ---------------
t_rethouse = 0
t_rettown = 0
calc_number=0
igss=0
bt5="q"
bt6="q"
etown=0
ehouse=0
mid_temp=30
d_ratio=1
correction = 1

def viewtemp():

    bt12 = str(round(t_rettown, 0))
    bt11 = 'от котла Т '+ str(round(tintown, 0)) + '   обратка ' + bt12 +'  '
    beg11 = tk.Label(master=frm_form, text=bt11)
    beg11.grid(column=1, row=9, pady=2, padx=2)

    bt21 = str(round(tinhouse, 0))
    bt22 = str(round(t_rethouse, 0))
    bt12 = ' после ТО ' + bt21 + '   обратка в ТО ' + bt22 + '  ' 
    beg12 = tk.Label(master=frm_form, text=bt12)
    beg12.grid(column=1, row=10, pady=2, padx=2)
    
def ddtf():
    global ddt, d_ratio
    # тепловой напор - http://ispu.ru/files/u2/Teplovoy_raschet_rekuperativnogo_teploobmennogo_apparata.pdf
    d1 = tintown - tinhouse 
    d2 = t_rettown - t_rethouse
    if abs(d1)>abs(d2):
        d_tmax=d1
        d_tmin=d2
    else:
        d_tmax=d2
        d_tmin=d1
    d_ratio = d_tmax/d_tmin
    if  d_ratio > 2: #!!!!!!!!!!!!!!!!!!!!!!!!!!!
        ddt = (d_tmax - d_tmin) / math.log( d_tmax/d_tmin )
    else :    
        ddt = (d_tmax + d_tmin)/2 
    return ddt

def fenergy():
    # для контроля считаем баланс энергии до ТО и после. должно примерно совпадать.
    global etown, ehouse
    etown=qtown*cw*(tintown - t_rettown)
    ehouse=qhouse*cw*(tinhouse-t_rethouse)

def gss_solver():
    global t_rettown, tinhouse, t_rethouse
    # Reading number of unknowns
    n = 3

    # Making numpy array of n x n+1 size and initializing 
    # to zero for storing augmented matrix
    a = np.zeros((n,n+1))

    # Making numpy array of n size and initializing 
    # to zero for storing solution vector
    x = np.zeros(n)

    # Reading augmented matrix coefficients

    a[0][0]= -qtown*cw
    a[0][1]= -qhouse*cw
    a[0][2]= qhouse*cw
    
    a[0][3]= -qtown*cw*tintown

    a[1][0]= 0
    a[1][1]= qhouse*cw-pdiss*1000/2/mid_temp
    a[1][2]= -qhouse*cw-pdiss*1000/2/mid_temp

    a[1][3]=0

    a[2][0]= -qtown*cw - square * ato*correction/2
    a[2][1]= square*ato*correction/2
    a[2][2]= square*ato*correction/2 

    a[2][3]= (square*ato*correction/2 - qtown*cw)*tintown

    # Applying Gauss Elimination
    for i in range(n):
        if a[i][i] == 0.0:
            sys.exit('Divide by zero detected!')
        
        for j in range(i+1, n):
            ratio = a[j][i]/a[i][i]
        
            for k in range(n+1):
                a[j][k] = a[j][k] - ratio * a[i][k]

    # Back Substitution
    x[n-1] = a[n-1][n]/a[n-1][n-1]

    for i in range(n-2,-1,-1):
        x[i] = a[i][n]
    
        for j in range(i+1,n):
            x[i] = x[i] - a[i][j]*x[j]
    
        x[i] = x[i]/a[i][i]
    t_rettown = x[0]
    tinhouse = x[1]
    t_rethouse = x[2]
    # Displaying solution 
    return
#----------------------------------------------
def squareinp():
    global square
    res = entry.get()
    square = float(res)
    result.configure(text=res)
def consinp():
    global qtown_max
    res = entry1.get()
    qtown_max = float(res)
    result1.configure(text=res)
def temptown():
    global tintown
    res = entry2.get()
    tintown = float(res)
    result2.configure(text=str(tintown))
def conshouse():
    global qhouse
    res = entry3.get()
    qhouse = float(res)
    result3.configure(text=res)
def powerhouse():
    global pdiss
    res = entry4.get()
    pdiss = float(res)
    result4.configure(text=res)
def t_demand():
    global tinhouse_demand
    res = entry5.get()
    tinhouse_demand = float(res)
    result5.configure(text=res)    
def midl_temp():
    global mid_temp
    res = entry6.get()
    mid_temp = float(res)
    if mid_temp > tinhouse_demand:
        mid_temp = tinhouse_demand-2
    result6.configure(text=str(mid_temp))
    
def initialcond():
    # начальные условия    
    squareinp()
    consinp()
    temptown()
    conshouse()
    powerhouse()
    t_demand()
    midl_temp()

def ugolserv_calc():
    global ugolserv
    x = (tinhouse_demand-tinhouse)/proport
    # расчет расхода из города ----------------------
    if abs(x)>1 :
        ugolserv = ugolserv + (x/abs(x))*tau/tservak
    else :
        ugolserv = ugolserv + x*tau/tservak
    if ugolserv < 0 : ugolserv = 0
    if ugolserv > 1 : ugolserv = 1
    
def mainframe_servo():
    global tintown, tinhouse, t_rethouse, t_rettown, qtown, ugolserv, calc_number, igss, d_ratio, correction, ato
    calc_number +=1
    igss=0
    tinhouse = 20
    ugolserv = ugolserv_0
    qtown = 0
    while  igss<200 and tinhouse < tinhouse_demand - 0.5 and qtown < qtown_max:
        # не больше i шагов и температуры положительные  
        igss +=1
        ugolserv_calc()           
        qtown = qtown_max * ugolserv # расход из города при данном угле сервака 
        correction = 1
        corr=1
        df = qtown/square
        ato = 300 + 3500*math.tanh(df) # !!!корректируем коэффициент теплопередачи по расходу/площадь
        
        gss_solver()
        
        fenergy()
        ddtf()
        
        print(igss,' ddt %.2f.' % ddt,' d_ratio %.2f.' % d_ratio, ' ugol %.2f.' % ugolserv, 'qtown/S %.2f.' % df, ' rettown %.1f.' % t_rettown,'tinhouse %.2f.' % tinhouse, 'rethous %.1f.' % t_rethouse)

        if d_ratio > 2.1:
            k = 0
            correction = 1-(d_ratio - 2)/(2.549*d_ratio+2.78) # коэффициент для корректировки среднего логарифмического
            while abs(corr - correction) > 0.05:
                k +=1
                
                gss_solver()
                ddtf()
                print(k, 'corr %.2f.' % correction,' d_ratio %.2f.' % d_ratio, ' ddt %.2f.' % ddt, ' rettown %.1f.' % t_rettown,'tinhouse %.2f.' % tinhouse, 'rethous %.1f.' % t_rethouse)
                corr = correction
                correction = 1-(d_ratio - 2)/(2.549*d_ratio+2.78)
                print('corr 2 %.2f.' % correction, ' ------------------')
        
        viewtemp()
    print('-------------------------------------')         
    mfs= ' мощность ТО квт ' + str(round(etown/1000, 0)) +'  ddt  ' + str(round(ddt, 1))+'  '  
    calc_mfs = tk.Label(master=clc_form, text=mfs)
    calc_mfs.grid(column=0, row=17, pady=2, padx=2)
      
    mfs= '  угол поворота  ' + str(round(ugolserv, 2)) +'  расход от котла ' + str(round(qtown, 2))+'  '  
    calc_mfs = tk.Label(master=clc_form, text=mfs)
    calc_mfs.grid(column=1, row=17, pady=2, padx=2)
    cnum= '   расчет ' + str(calc_number)+'  '  
    calc_mfs = tk.Label(master=clc_form, text=cnum)
    calc_mfs.grid(column=1, row=12, pady=2, padx=2)

    if ugolserv == ugolserv_max:
        mfs= 'температура  ' + str(tinhouse_demand) + '  НЕ достигнута '
        color = "red"
    else:
        mfs= 'температура  ' + str(tinhouse_demand) + '  достигнута    '
        color = "black"
    calc_mfs = tk.Label(master=clc_form, text=mfs, fg=color)
    calc_mfs.grid(column=0, row=18, pady=2, padx=2)
    
        
# создаем корневое окно
window = tk.Tk()

# заголовок
window.title("ввод начальных данных")

# размеры
window.geometry('500x500')

frm_form = tk.Frame(relief=tk.RAISED, borderwidth=5)
clc_form = tk.Frame(relief=tk.SUNKEN, borderwidth=5)
# Помещает рамку в окно приложения.
frm_form.pack()
clc_form.pack()

# ввод начальных данных----------------------------------
lbl = tk.Label(master=frm_form, text="площадь ТО")
lbl.grid(column=0, row=1)
entry = tk.Entry(master=frm_form, width=5)  
entry.grid(column=1, row=1)
entry.insert(0, square)
entry.focus()
result = tk.Label(master=frm_form, text=str(square))
result.grid(column=3, row=1, padx=10)

lbl1 = tk.Label(master=frm_form, text="расход от котла л/с")
lbl1.grid(column=0, row=2)
entry1 = tk.Entry(master=frm_form, width=5)  
entry1.grid(column=1, row=2)
entry1.insert(0, qtown_max)
result1 = tk.Label(master=frm_form, text=str(qtown_max))
result1.grid(column=3, row=2, padx=10)

lbl2 = tk.Label(master=frm_form, text="темп подачи от котла")
lbl2.grid(column=0, row=3)
entry2 = tk.Entry(master=frm_form, width=5)  
entry2.grid(column=1, row=3)
entry2.insert(0, tintown)
result2 = tk.Label(master=frm_form, text=str(tintown))
result2.grid(column=3, row=3, padx=10)

lbl3 = tk.Label(master=frm_form, text="расход в доме")
lbl3.grid(column=0, row=4)
entry3 = tk.Entry(master=frm_form, width=5)  
entry3.grid(column=1, row=4)
entry3.insert(0, qhouse)
result3 = tk.Label(master=frm_form, text=str(qhouse))
result3.grid(column=3, row=4, padx=10)

lbl4 = tk.Label(master=frm_form, text="мощь рассеивания, квт")
lbl4.grid(column=0, row=5)
entry4 = tk.Entry(master=frm_form, width=5)  
entry4.grid(column=1, row=5)
entry4.insert(0, pdiss)
result4 = tk.Label(master=frm_form, text=str(pdiss))
result4.grid(column=3, row=5, padx=10)

lbl5 = tk.Label(master=frm_form, text="требуемая темп. после ТО")
lbl5.grid(column=0, row=6)
entry5 = tk.Entry(master=frm_form, width=5)  
entry5.grid(column=1, row=6)
entry5.insert(0, tinhouse_demand)
result5 = tk.Label(master=frm_form, text=str(tinhouse_demand))
result5.grid(column=3, row=6, padx=10)

lbl6 = tk.Label(master=frm_form, text="ожидаемая средн Т после ТО")
lbl6.grid(column=0, row=7)
entry6 = tk.Entry(master=frm_form, width=5)  
entry6.grid(column=1, row=7)
entry6.insert(0, mid_temp)
result6 = tk.Label(master=frm_form, text=str(mid_temp))
result6.grid(column=3, row=7, padx=10)
#---------------------------------------------------------
btn_recalc = tk.Button( master=frm_form, text="обновить нач. данные", command=initialcond)
btn_recalc.grid(row=8, column=1, pady=2, padx=5)

#---------------------------------
btn_mf = tk.Button(master=clc_form, text="расчет Т потоков", command = mainframe_servo)
btn_mf.grid(row=12, column=0, pady=2, padx=10)
window.after(1000, initialcond)  # Обновлять каждую секунду
# ----------------------------------------
window.mainloop()
     
realtime=tau*igss
print('gameover ', realtime, ' время = шаг х колво шагов')    

