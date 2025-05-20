# начальные условия
tintown = 70 # на входе из города - постоянная
tinhouse0 = 24 # температура начальная в контуре отопления
tinhouse_demand = 60 # требуемая температура подачи
troom = 15
cw = 4200 # теплоемкость воды
qhouse_chas = 1.5 # расход куб в час в отоплении
qhouse = 1.5/3.6 # расход кг/сек в доме постоянный.
cwq = qhouse*cw # так короче
qtown_chas_max = 2 # мах расход куб в час из города
qtown_max = qtown_chas_max/3.6 # секундный из города
real_time = 0
tservak = 120 # время разворота сервака
proport = 20 # полоса пропорциональности температуры

btermo=500 # теплоотдача батарей НЕ трогать
ato = 4000 # теплопередача ТО тоже не трогать

tau=5 # шаг по времени сек

ugolserv = 0
tinhouse = tinhouse0
t_rettown = tintown

while abs(tinhouse-tinhouse_demand) > 1 and tinhouse * t_rettown > 0:
#i=1
#while i<10:
#    i +=1
    x = (tinhouse_demand-tinhouse)/proport
    # расчет расхода из города
    if x>1 :
        ugolserv = ugolserv + tau/tservak
    else :
        ugolserv = ugolserv + x*tau/tservak
    if ugolserv < 0 : ugolserv = 0
    if ugolserv > 1 : ugolserv = 1
       
    qtown = qtown_max * ugolserv # расход из города при данном угле сервака
    #print("ugol %.2f." % ugolserv, "qtown %.3f." % qtown)
    
    t_rethouse = ((cwq - btermo/2)*tinhouse + btermo * troom)/(cwq+btermo/2) # обратка из дома
    t_rettown = tintown-(ato * qtown/qtown_max)*((tintown+t_rettown)/2 - (tinhouse+t_rethouse)/2)/cw #обратка в город
    
    etown=tau*qtown*cw*(tintown - t_rettown)
    ehouse=tau*qhouse*cw*(tinhouse-t_rethouse)
    d_tinhouse = (etown-ehouse)/(cw*tau*qhouse) #подача в дом - подсчет разности энергий
    tinhouse = tinhouse + d_tinhouse # подача в дом
   # print('tinhouse %.2f.' % tinhouse, 'rethous %.2f.' % t_rethouse,'rettown %.2f.' % t_rettown, etown, ehouse)
    real_time += tau
    power = qtown*cw*(tintown-t_rettown) # подсчет текущей мощности теплопередачи ватт
    print('tinhouse %.2f.' % tinhouse, 'rethous %.2f.' % t_rethouse,'rettown %.2f.' % t_rettown,'power %.2f.'% power)
    print('-----------------------')
print('gameover', real_time, tau)    
