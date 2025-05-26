import math
# начальные условия
tintown = 70 # на входе из города - постоянная ---------------------------

tinhouse0 = 24 # температура начальная в контуре отопления ---------------

tinhouse_demand = 80 # требуемая температура подачи ----------------------

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
ugolserv = 0
tinhouse = tinhouse0
t_rettown = tinhouse
i = 0
atos=ato * square

#--------------------------------------

while abs(tinhouse-tinhouse_demand) > 1 and tinhouse * t_rettown > 0 and i<100:
    # не больше i шагов и температуры положительные 
   
    i +=1

    qtown0 = qtown_max * ugolserv
    x = (tinhouse_demand-tinhouse)/proport
    # расчет расхода из города
    if x>1 :
        ugolserv = ugolserv + tau/tservak
    else :
        ugolserv = ugolserv + x*tau/tservak
    if ugolserv < 0 : ugolserv = 0
    if ugolserv > 1 : ugolserv = 1
       
    qtown = qtown_max * ugolserv # расход из города при данном угле сервака
    d_qtown=qtown-qtown0
    
    print("ugol %.2f." % ugolserv, "qtown %.3f." % qtown, d_qtown)   
    j=0
    d_trettown=10
    while j<10 and abs(d_trettown) >0.5: # приращение Т обратки в город меньше 0,5
        
        t_rethouse = ((cwq - btermo/2)*tinhouse + btermo * troom)/(cwq+btermo/2) # обратка из дома - поглощение энергии
    
        d_tmax = tintown + t_rettown
        d_tmin = tinhouse + t_rethouse
    
        # энергия которая передается через пластину
        d_power=atos*d_qtown*(d_tmax - d_tmin)/2
    
        d_trettown = (d_qtown*(tintown - t_rettown)-d_power/cw)/qtown # прирост Т обр город d_power - прирост энергии d_qtown - прирост расхода
        t_rettown = t_rettown + d_trettown
       
        etown=qtown*cw*(tintown - t_rettown)
        ehouse=qhouse*cw*(tinhouse-t_rethouse)
        d_tinhouse = (etown-ehouse)/(cw*qhouse) #подача в дом - подсчет разности энергий
        # подача в дом 
        tinhouse = tinhouse+d_tinhouse

        power1 = cw * qtown * (tintown - t_rettown)
        j +=1

        #print('d_power %.2f.'% d_power, 'd_trettown %.3f.'% d_trettown,'power doTO %.2f.'% power1)
        #print('tinhouse %.2f.' % tinhouse, 'rethous %.2f.' % t_rethouse,'rettown %.2f.' % t_rettown)
    print('tinhouse %.2f.' % tinhouse, 'rethous %.2f.' % t_rethouse,'rettown %.2f.' % t_rettown,'power %.2f.'% power1 )     
    print(i,'шаг по времени ----------------------')
print('gameover', tau)    
