import math
# начальные условия
tintown = 70 # на входе из города - постоянная ---------------------------

tinhouse0 = 55 # температура начальная в контуре отопления ---------------

tinhouse_demand = 45 # требуемая температура подачи ----------------------

troom = 18 # температура в помещении, от нее зависит рассеяние энергии

cw = 4200 # теплоемкость воды

qhouse_chas = 3 # расход куб/час в отоплении -----------------------------
qhouse = qhouse_chas/3.6 # расход кг/сек в доме постоянный.

cwq = qhouse*cw # так короче

qtown_chas_max = 3 # мах расход куб/час из города ------------------------
qtown_max = qtown_chas_max/3.6 # секундный из города

tservak = 120 # время разворота сервака ---------------------------------
proport = 20 # полоса пропорциональности температуры

btermo=1200 # теплоотдача батарей НЕ трогать
ato = 3000 # теплопередача ТО тоже не трогать

square=1 # Площадь ТО в кв.м.-----------------------
tau=2 # шаг по времени сек

real_time = 0
ugolserv = 1
tinhouse = tinhouse0
t_rettown = tintown-10
print(t_rettown)
i = 0
atos=ato * square

#--------------------------------------
while abs(tinhouse-tinhouse_demand) > 1 and tinhouse * t_rettown > 0 and i<400:
    # не больше i шагов и температуры положительные 
   
    i +=1

    qtown0 = qtown_max * ugolserv
    x = (tinhouse_demand-tinhouse)/proport
    # расчет расхода из города
    if abs(x)>1 :
        ugolserv = ugolserv + (x/abs(x))*tau/tservak
    else :
        ugolserv = ugolserv + x*tau/tservak
    if ugolserv < 0 : ugolserv = 0
    if ugolserv > 1 : ugolserv = 1
       
    qtown = qtown_max * ugolserv # расход из города при данном угле сервака
    d_qtown=qtown-qtown0
    
    print(x,"ugol %.3f." % ugolserv, "qtown %.3f." % qtown, d_qtown)   
    j=0
    d_trettown = 10
    d_tinhouse = 0
    #and abs(d_trettown) >0.1
    teta0=0
    d_teta = 1
    ddt0 = 0
    
    while j<20 and d_teta>0.05 : # приращение Т обратки в город меньше 0,5
        print(j)
        t_rethouse = ((cwq - btermo/2)*tinhouse + btermo * troom)/(cwq+btermo/2) # обратка из дома - поглощение энергии
    
        d_tmax = tintown + t_rettown
        d_tmin = tinhouse + t_rethouse
        ddt = (d_tmax - d_tmin)/2
        d_ddt=ddt-ddt0
        ddt = 0
        # энергия которая передается через пластину
        d_power=atos*(d_qtown*ddt + qtown*d_ddt)    

        d_trettown = (d_qtown*(tintown - t_rettown)-d_power/cw)/qtown # прирост Т обр город d_power - прирост энергии d_qtown - прирост расхода
        if t_rettown+d_trettown > tintown:
            t_rettown = tintown
        else:    
            t_rettown = t_rettown + d_trettown
       
        etown=qtown*cw*(tintown - t_rettown)
        ehouse=qhouse*cw*(tinhouse-t_rethouse)
        #print(' город дoм', etown, ehouse)
    
        d_tinhouse = (etown-ehouse)/(cw*qhouse) #подача в дом - подсчет разности энергий
        
        # подача в дом
        if tinhouse+d_tinhouse > tintown:
            tinhouse = tintown
        else:    
            tinhouse = tinhouse+d_tinhouse

        teta=((tintown-tinhouse)/2 - (t_rettown-t_rethouse)/2)
        d_teta=abs(teta-teta0)
        teta0=teta
        etown=qtown*cw*(tintown - t_rettown)
        ehouse=qhouse*cw*(tinhouse-t_rethouse)
        j +=1
    
        #print('d_power %.2f.'% d_power, 'd_trettown %.3f.'% d_trettown,'power do TO %.2f.'% etown)
        #print('tinhouse %.2f.' % tinhouse, 'rethous %.2f.' % t_rethouse,'rettown %.2f.' % t_rettown, d_teta)
    print('tinhouse %.2f.' % tinhouse, 'rethous %.2f.' % t_rethouse,'rettown %.2f.' % t_rettown,'power %.2f.'% etown )     
    print(i,'шаг по времени ----------------------')
print('gameover', tau)    
