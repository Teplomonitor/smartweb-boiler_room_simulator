import math
# начальные условия
tintown = 70 # на входе из города - постоянная ---------------------------

tinhouse0 = 58 # температура начальная в контуре отопления ---------------

tinhouse_demand = 60 # требуемая температура подачи ----------------------

troom = 18 # температура в помещении, от нее зависит рассеяние энергии

cw = 4200 # теплоемкость воды

qhouse_chas = 2 # расход куб/час в отоплении -----------------------------
qhouse = 1.5/3.6 # расход кг/сек в доме постоянный.

cwq = qhouse*cw # так короче
qtown_chas_max = 3 # мах расход куб/час из города ------------------------
qtown_max = qtown_chas_max/3.6 # секундный из города

tservak = 120 # время разворота сервака ---------------------------------
proport = 20 # полоса пропорциональности температуры

btermo=1000 # теплоотдача батарей НЕ трогать
ato = 3000 # теплопередача ТО тоже не трогать

sqwear=1.5 # Площадь ТО в кв.м.-----------------------
tau=3 # шаг по времени сек

real_time = 0
ugolserv = 1
tinhouse = tinhouse0
t_rettown = tintown
i = 0
power1 = 100
atos=ato * sqwear
difftold = 0

#while abs(tinhouse-tinhouse_demand) > 1 and tinhouse * t_rettown > 0 and i<200:
while i < 20:
    # не больше 200 шагов и температуры положительные 
   
    i +=1
    cond = True
    x = (tinhouse_demand-tinhouse)/proport
    # расчет расхода из города
    if x>1 :
        ugolserv = ugolserv + tau/tservak
    else :
        ugolserv = ugolserv + x*tau/tservak
    if ugolserv < 0 : ugolserv = 0
    if ugolserv > 1 : ugolserv = 1
       
    qtown = qtown_max * ugolserv # расход из города при данном угле сервака
       
    j=1
    while cond:
        j +=1
        t_rethouse = ((cwq - btermo/2)*tinhouse + btermo * troom)/(cwq+btermo/2) # обратка из дома
        
        difft = (tintown+t_rettown)/2.0 - (tinhouse+t_rethouse)/2.0

        t_rettown = tintown - atos * qtown * difft/qtown_max/cw #обратка в город
            
        etown=qtown*cw*(tintown - t_rettown)
        ehouse=qhouse*cw*(tinhouse-t_rethouse)
        d_tinhouse = (etown-ehouse)/(cw*qhouse) #подача в дом - подсчет разности энергий
        tinhouse = tinhouse + d_tinhouse # подача в дом 

        power1 = qtown*cw*(tintown-t_rettown) # подсчет текущей мощности теплопередачи ватт
        
        if abs(difft-difftold)<0.2 or j>10: # условие выхода из внутреннего цикла. не больше 10 итераций 
            cond=False
        difftold=difft
        
        print('tmp: tinhouse %.2f.' % tinhouse, 'rethous %.2f.' % t_rethouse,'rettown %.2f.' % t_rettown)
        
    real_time += tau
    
    print('power town %.2f.'% power1)
   
    print('tinhouse %.2f.' % tinhouse, 'rethous %.2f.' % t_rethouse,'rettown %.2f.' % t_rettown)
    print(i,'шаг по времени ----------------------')
print('gameover', real_time, tau)    
