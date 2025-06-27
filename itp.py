import math
# начальные условия
tintown = 70 # на входе из города - постоянная ---------------------------

tinhouse_demand = 45 # требуемая температура подачи ----------------------

troom = 18 # температура в помещении, от нее зависит рассеяние энергии

cw = 4200 # теплоемкость воды

qhouse = 1 # расход кг/сек в доме постоянный.

cwq = qhouse*cw # так короче

qtown_max = 1.5 # секундный из города

tservak = 120 # время разворота сервака ---------------------------------
proport = 20 # полоса пропорциональности температуры

btermo=1000 # теплоотдача батарей НЕ трогать
ato = 3500 # теплопередача ТО тоже не трогать

square=1 # Площадь ТО в кв.м.-----------------------
tau=2 # шаг по времени сек

ddt=0
real_time = 0
ugolserv = 1

tinhouse = troom #температура начальная в контуре отопления ---------------
t_rethouse = troom
t_rettown = tintown-30

t_rett=0
i = 0
atos=ato * square

def initialcond():
    # начальные условия
    global t_rettown, tinhouse, t_rethouse
    t_rettown = ugolserv * (tintown-15-troom) + troom # линейно меняем от Тподачи - 15 до Тroom
    tinhouse = ugolserv * (tintown-25-troom) + troom # линейно меняем от Тподачи - 25 до Тroom
    t_rethouse = ((cwq - btermo/2)*tinhouse + btermo * troom)/(cwq+btermo/2) # начальное прибдижение обратка из дома - поглощение энергии    
    print('!!! initial tinhouse %.2f.' % tinhouse, 'rethous %.2f.' % t_rethouse,'rettown %.2f.' % t_rettown, 'tinhouse demand %.2f.' % tinhouse_demand )
    
def ddtf():
    global ddt
    # тепловой напор - http://ispu.ru/files/u2/Teplovoy_raschet_rekuperativnogo_teploobmennogo_apparata.pdf
    d1 = tintown - tinhouse 
    d2 = t_rettown - t_rethouse
    d_tmax=d1
    d_tmin=d2
    d = d_tmin/d_tmax
    if  d > 20: #!!!!!!!!!!!!!!!!!!!!!!!!!!!
        ddt = (d_tmax - d_tmin) / math.log( d_tmax/d_tmin )
    else :    
        ddt = (d_tmax + d_tmin)/2 
    return ddt

def ft_rettown():
    # обратка в город
    global t_rettown
    t_rettown = tintown - atos*ddt/(cw*qtown)
    if t_rettown < t_rethouse:
        #print('!!!!!', t_rettown)
        t_rettown = t_rethouse
    return t_rettown

def frettdom():
    # подача и обратка дома
    global t_rethouse
    t_rethouse = ((cwq - btermo/2)*tinhouse + btermo * troom)/(cwq+btermo/2) # обратка из дома - поглощение энергии
    
def findom():
    # подача и обратка дома
    global tinhouse
    tinhouse = qtown*(tintown - t_rettown)/qhouse + t_rethouse

def fenergy():
    # для контроля считаем баланс энергии до ТО и после. должно примерно совпадать.
    global etown, ehouse
    etown=qtown*cw*(tintown - t_rettown)
    ehouse=qhouse*cw*(tinhouse-t_rethouse)
    
def mainframe():
    # тело основной программы
    global tinhouse, t_rethouse, t_rettown
    j=0
    d_teta = 10
    ddtf() # температурный напор
    while j<20 and abs(d_teta) > 0.5 : # утрясаем температуры при изменении расхода
        
        ddt0=ddt
        findom()
        
        #ddtf()
        ft_rettown()
              
        #ddtf()
        frettdom()
        
        ddtf()
        d_teta=ddt-ddt0
        
        #fenergy() # вроде нормально все с энергией - проверку можно выключить
        
        j +=1
        #print('j', j, 'd_teta %.2f.'% d_teta, ddt)    
    #print('i',i, 'энергия города', etown, ' дом ', ehouse,'----------------------') 
    return

initialcond() # - initial conditions calculate, depends on ugolserv
while  i<100:
    # не больше i шагов и температуры положительные  
    i +=1
    qtown0 = qtown_max * ugolserv
    x = (tinhouse_demand-tinhouse)/proport
    # расчет расхода из города ----------------------
    if abs(x)>1 :
        ugolserv = ugolserv + (x/abs(x))*tau/tservak
    else :
        ugolserv = ugolserv + x*tau/tservak
    if ugolserv < 0 : ugolserv = 0
    if ugolserv > 1 : ugolserv = 1
       
    qtown = qtown_max * ugolserv # расход из города при данном угле сервака 
    d_qtown=qtown-qtown0
    #--------------------------------------------------------------
    print("ugol %.3f." % ugolserv, "qtown %.3f." % qtown, d_qtown)

    mainframe()
 
    # здесь можно вставить изменение внешних условий по температуре. НЕ слишком резко! -
    ddt0 = ddt
    
    if i<20 : #меняем входящую из города
        tintown=tintown + 0.1
        if tintown >85 : tintown = 85
    else :    
        tintown=tintown - 0.07
        if tintown < 55 : tintown = 55
    #-----------------------------------------

    mainframe()

    print('tintown %.2f.' % tintown, ' rettown %.2f.' % t_rettown,'tinhouse %.2f.' % tinhouse, 'rethous %.2f.' % t_rethouse)     
    print(i,'шаг по времени ------')
    
print('gameover', 'realtime', tau*i, tau)    
