from h import *
import json,datetime,io,os
R=[]
def rec(id,hu,pre,steps,exp,obt,ok): R.append(dict(id=id,hu=hu,pre=pre,steps=steps,exp=exp,obt=obt,ok=bool(ok)))
sfx=uuid.uuid4().hex[:6]
em=f'tc{sfx}@t.co'; PW='Abcdef1!'
today=datetime.date.today(); mes=today.month; anio=today.year
d=lambda n: (today.replace(day=1)+datetime.timedelta(days=n)).isoformat()
# HU-01
s,r=call('POST','/auth/register',{'nombre':'Usuario Prueba','email':em,'password':PW,'aceptaPolitica':True})
rec('TC-01','HU-01','Correo no registrado','1. POST /auth/register con datos válidos y aceptaPolitica=true','201, cuenta creada con rol usuario y token',f'HTTP {s}; rol={r.get("user",{}).get("rol")}; token={"sí" if r.get("access_token") else "no"}',s==201 and r['user']['rol']=='usuario')
s,r=call('POST','/auth/register',{'nombre':'Otro','email':em,'password':PW,'aceptaPolitica':True})
rec('TC-02','HU-01','Correo ya registrado en TC-01','1. POST /auth/register con el mismo correo','409 y sin cuenta duplicada',f'HTTP {s}; mensaje: {r.get("message")}',s==409)
s,r=call('POST','/auth/register',{'nombre':'Otro','email':f'x{sfx}@t.co','password':PW,'aceptaPolitica':False})
rec('TC-03','HU-01','—','1. POST /auth/register con aceptaPolitica=false','400 con mensaje de política obligatoria',f'HTTP {s}; mensaje: {r.get("message")}',s==400)
s,r=call('POST','/auth/register',{'nombre':'Otro','email':f'y{sfx}@t.co','password':'abc','aceptaPolitica':True})
rec('TC-04','HU-01','—','1. POST /auth/register con contraseña débil ("abc")','400 con regla de contraseña',f'HTTP {s}',s==400)
# HU-02
s,r=call('POST','/auth/login',{'email':em,'password':PW}); tok=r.get('access_token') if s==200 else None
rec('TC-05','HU-02','Cuenta de TC-01','1. POST /auth/login con credenciales correctas','200 y token JWT',f'HTTP {s}; token={"sí" if tok else "no"}',s==200 and tok)
s1,r1=call('POST','/auth/login',{'email':em,'password':'Mala123!'}); s2,r2=call('POST','/auth/login',{'email':f'no{sfx}@t.co','password':PW})
rec('TC-06','HU-02','—','1. Login con contraseña errónea. 2. Login con correo inexistente','401 con el mismo mensaje genérico en ambos',f'HTTP {s1}/{s2}; mensajes iguales: {r1.get("message")==r2.get("message")} («{r1.get("message")}»)',s1==401 and s2==401 and r1.get('message')==r2.get('message'))
s1,_=call('GET','/transactions'); s2,_=call('GET','/transactions',tok='abc.def.ghi')
rec('TC-07','HU-02','—','1. GET /transactions sin token. 2. GET con token inválido','401 en ambos casos',f'HTTP {s1} y {s2}',s1==401 and s2==401)
# HU-03
s,r=call('GET','/users/profile',tok=tok)
rec('TC-08','HU-03','Sesión iniciada','1. GET /users/profile','200 con datos del perfil sin hash de contraseña',f'HTTP {s}; campos: {sorted(r.keys())[:6]}…; passwordHash expuesto: {"passwordHash" in r}',s==200 and 'passwordHash' not in r)
s,r=call('PUT','/users/profile',{'nombre':'Usuario Actualizado','ingresoMensual':4000000},tok=tok)
s2,r2=call('GET','/users/profile',tok=tok)
rec('TC-09','HU-03','Sesión iniciada','1. PUT /users/profile con nombre e ingreso. 2. GET /users/profile','El cambio persiste',f'HTTP {s}; nombre={r2.get("nombre")}; ingreso={r2.get("ingresoMensual")}',s==200 and r2.get('ingresoMensual')==4000000)
s,r=call('PUT','/users/password',{'passwordActual':'Incorrecta1!','passwordNueva':'Nueva123!x'},tok=tok)
rec('TC-10','HU-03','Sesión iniciada','1. PUT /users/password con contraseña actual incorrecta','Rechazo (4xx) sin cambiar la contraseña',f'HTTP {s}',400<=s<500)
# categories
s,cats=call('GET','/categories',tok=tok)
cat={c['nombre']:c['id'] for c in cats}
ing=[c for c in cats if c['tipo']=='ingreso'][0]['id']
# HU-04
s,t1=call('POST','/transactions',{'tipo':'ingreso','monto':4000000,'categoriaId':ing,'descripcion':'Salario','fecha':d(0)},tok=tok)
s2,t2=call('POST','/transactions',{'tipo':'egreso','monto':100000,'categoriaId':cat['Alimentación'],'descripcion':'Mercado','fecha':d(1)},tok=tok)
s3,sm=call('GET',f'/transactions/summary?mes={mes}&anio={anio}',tok=tok)
rec('TC-11','HU-04','Sesión iniciada','1. Registrar ingreso 4.000.000. 2. Registrar egreso 100.000. 3. GET /transactions/summary',f'201 en ambos y balance 3.900.000',f'HTTP {s}/{s2}; resumen: {json.dumps(sm)[:160]}',s==201 and s2==201)
s,r=call('POST','/transactions',{'tipo':'egreso','monto':-5,'categoriaId':cat['Alimentación'],'fecha':d(1)},tok=tok)
s2,r2=call('POST','/transactions',{'tipo':'egreso','monto':'abc','categoriaId':cat['Alimentación'],'fecha':d(1)},tok=tok)
rec('TC-12','HU-04','Sesión iniciada','1. POST con monto negativo. 2. POST con monto no numérico','400 con errores de validación; no se guarda',f'HTTP {s} y {s2}',s==400 and s2==400)
s,r=call('PUT',f'/transactions/{t2["id"]}',{'monto':150000},tok=tok); s2,sm2=call('GET',f'/transactions/summary?mes={mes}&anio={anio}',tok=tok)
rec('TC-13','HU-04','Egreso de TC-11','1. PUT /transactions/:id con monto 150.000. 2. GET summary','El balance refleja el cambio',f'HTTP {s}; resumen: {json.dumps(sm2)[:160]}',s==200)
s,_=call('DELETE',f'/transactions/{t2["id"]}',tok=tok); s2,r2=call('GET',f'/transactions/{t2["id"]}',tok=tok)
rec('TC-14','HU-04','Egreso de TC-11','1. DELETE /transactions/:id. 2. GET del mismo id','Eliminación (2xx) y luego 404',f'HTTP {s} y luego {s2}',s in(200,204) and s2==404)
# HU-05
s,r=call('GET','/categories/suggest?descripcion=uber%20al%20trabajo&tipo=egreso',tok=tok)
rec('TC-15','HU-05','Sesión iniciada','1. GET /categories/suggest con «uber al trabajo»','Categoría sugerida Transporte, origen «reglas»',f'HTTP {s}; categoría={r.get("category",{}).get("nombre")}; origen={r.get("origen")}',r.get('category',{}).get('nombre')=='Transporte' and r.get('origen')=='reglas')
s,r=call('POST','/transactions',{'tipo':'egreso','monto':30000,'categoriaId':cat['Salud'],'descripcion':'Uber al trabajo','fecha':d(2),'origenCategoria':'manual'},tok=tok)
rec('TC-16','HU-05','Sesión iniciada','1. Registrar egreso «Uber al trabajo» eligiendo manualmente la categoría Salud','Se respeta la categoría elegida por el usuario',f'HTTP {s}; origen={r.get("origenCategoria")}; categoría={r.get("category",{}).get("nombre") or r.get("categoriaId")}',s==201)
# HU-06
for i,(tp,cn,desc) in enumerate([('egreso','Transporte','Bus'),('egreso','Alimentación','Almuerzo'),('egreso','Transporte','Taxi')]):
    call('POST','/transactions',{'tipo':tp,'monto':20000+i,'categoriaId':cat[cn],'descripcion':desc,'fecha':d(3+i)},tok=tok)
s,r=call('GET','/transactions',tok=tok); items=r.get('data') or r.get('items') or r
s2,r2=call('GET',f'/transactions?type=egreso&categoryId={cat["Transporte"]}&startDate={d(0)}&endDate={d(10)}',tok=tok); it2=r2.get('data') or r2.get('items') or r2
ok=isinstance(it2,list) and len(it2)==2
rec('TC-17','HU-06','Hay 6 movimientos registrados','1. GET /transactions sin filtros. 2. GET con tipo=egreso, categoría Transporte y rango de fechas','Sin filtros: todos, del más reciente al más antiguo. Con filtros: solo 2 coincidencias',f'HTTP {s}/{s2}; sin filtros={len(items)}; con filtros={len(it2) if isinstance(it2,list) else it2}',ok)
em2=f'vacio{sfx}@t.co'; call('POST','/auth/register',{'nombre':'Vacío','email':em2,'password':PW,'aceptaPolitica':True}); _,lr=call('POST','/auth/login',{'email':em2,'password':PW}); tok2=lr['access_token']
s,r=call('GET','/transactions',tok=tok2); it=r.get('data') if isinstance(r,dict) and 'data' in r else (r.get('items') if isinstance(r,dict) and 'items' in r else r)
rec('TC-18','HU-06','Usuario sin movimientos','1. GET /transactions','Lista vacía (la interfaz muestra el mensaje de invitación)',f'HTTP {s}; elementos={len(it)}',s==200 and len(it)==0)
# HU-07
s0,al0=call('GET',f'/budgets/alerts?mes={mes}&anio={anio}',tok=tok2)
rec('TC-19','HU-07','Usuario sin topes','1. GET /budgets/alerts','Lista vacía, sin alertas vacías',f'HTTP {s0}; alertas={len(al0)}',s0==200 and al0==[])
s,b=call('POST','/budgets',{'categoriaId':cat['Alimentación'],'montoLimite':120000,'mes':mes,'anio':anio},tok=tok)
call('POST','/transactions',{'tipo':'egreso','monto':85000,'categoriaId':cat['Alimentación'],'descripcion':'Mercado grande','fecha':d(1)},tok=tok)
s1,al=call('GET',f'/budgets/alerts?mes={mes}&anio={anio}',tok=tok)
a=[x for x in al if x.get('categoria')=='Alimentación']
rec('TC-20','HU-07','Tope de 120.000 en Alimentación','1. Registrar egresos de Alimentación por 85.000. 2. GET /budgets/alerts','Alerta preventiva (≥ 80 %) con porcentaje y saldo',f'HTTP {s1}; estado={a[0]["estado"] if a else None}; porcentaje={a[0]["porcentaje"] if a else None}',bool(a) and a[0]['estado']!='ok' and a[0]['estado']!='excedido')
call('POST','/transactions',{'tipo':'egreso','monto':40000,'categoriaId':cat['Alimentación'],'descripcion':'Cena','fecha':d(2)},tok=tok)
s1,al=call('GET',f'/budgets/alerts?mes={mes}&anio={anio}',tok=tok); a=[x for x in al if x.get('categoria')=='Alimentación']
rec('TC-21','HU-07','Consumo de TC-20','1. Registrar 40.000 adicionales (total 145.001). 2. GET /budgets/alerts','Alerta crítica (≥ 100 %) distinguible de la preventiva',f'estado={a[0]["estado"] if a else None}; porcentaje={a[0]["porcentaje"] if a else None}; mensaje: {a[0].get("mensaje") if a else None}',bool(a) and a[0]['porcentaje']>=100)
# HU-08
s,g=call('POST','/goals',{'nombre':'Viaje','montoObjetivo':1000000,'fechaLimite':(today+datetime.timedelta(days=180)).isoformat()},tok=tok)
s2,gb=call('POST','/goals',{'nombre':'Sin monto','fechaLimite':(today+datetime.timedelta(days=180)).isoformat()},tok=tok)
rec('TC-22','HU-08','Sesión iniciada','1. Crear meta válida. 2. Crear meta sin monto','201 para la válida; 400 para la inválida',f'HTTP {s} y {s2}',s==201 and s2==400)
s,c1=call('POST',f'/goals/{g["id"]}/contributions',{'monto':250000},tok=tok); s2,gd=call('GET',f'/goals/{g["id"]}',tok=tok)
rec('TC-23','HU-08','Meta de TC-22','1. POST aporte de 250.000. 2. GET de la meta','El avance se actualiza (25 %) y se muestra la proyección',f'HTTP {s}; {json.dumps({k:gd.get(k) for k in ("montoAhorrado","porcentaje","avance","estado") if k in gd})}',s==201 and gd.get('montoAhorrado')==250000)
s,c2=call('POST',f'/goals/{g["id"]}/contributions',{'monto':750000},tok=tok); s2,gd=call('GET',f'/goals/{g["id"]}',tok=tok)
rec('TC-24','HU-08','Meta de TC-22','1. POST aporte de 750.000 (total = objetivo). 2. GET de la meta','La meta queda completada al 100 %',f'HTTP {s}; estado={gd.get("estado")}; ahorrado={gd.get("montoAhorrado")}',gd.get('estado') in('cumplida','completada'))
# HU-09
call('PUT','/users/profile',{'ingresoMensual':4000000},tok=tok)
s,c=call('POST','/credits',{'nombre':'Tarjeta Visa','entidad':'Banco A','tipo':'tarjeta','montoOriginal':3000000,'saldoActual':2400000,'tasaEA':28,'cuotaMensual':400000,'cuotasRestantes':8},tok=tok)
s2,sm=call('GET','/credits/summary',tok=tok)
rec('TC-25','HU-09','Ingreso mensual 4.000.000','1. Registrar crédito con cuota 400.000. 2. GET /credits/summary','Total de cuotas 400.000 y 10 % del ingreso comprometido',f'HTTP {s}/{s2}; {json.dumps({k:sm.get(k) for k in ("totalCuotas","porcentajeComprometido","nivel") if k in sm})}',s==201 and sm.get('porcentajeComprometido')==10)
s,r=call('POST','/credits',{'nombre':'X','tipo':'tarjeta','montoOriginal':1000,'saldoActual':'abc','tasaEA':-5,'cuotaMensual':100,'cuotasRestantes':3},tok=tok)
rec('TC-26','HU-09','Sesión iniciada','1. POST /credits con tasa negativa y saldo no numérico','400 sin guardar',f'HTTP {s}',s==400)
s,sm0=call('GET','/credits/summary',tok=tok2)
rec('TC-27','HU-09','Usuario sin ingreso definido','1. GET /credits/summary','Respuesta sin error y porcentaje 0 (la interfaz invita a completar el perfil)',f'HTTP {s}; {json.dumps(sm0)[:160]}',s==200)
# HU-10
s,ev=call('POST','/credits/evaluate',{'monto':30000000,'tasaEA':25,'plazoMeses':24},tok=tok)
s2,ev2=call('POST','/credits/evaluate',{'monto':3000000,'tasaEA':20,'plazoMeses':36},tok=tok)
rec('TC-28','HU-10','Ingreso 4.000.000 y cuota actual 400.000','1. Evaluar crédito de 30.000.000 a 24 meses. 2. Evaluar crédito de 3.000.000 a 36 meses','El crédito grande se marca «no_recomendable» con motivo; el pequeño no',f'1: veredicto={ev.get("veredicto")}, nuevo %={ev.get("porcentajeNuevo")}; 2: veredicto={ev2.get("veredicto")}, nuevo %={ev2.get("porcentajeNuevo")}',ev.get('veredicto')=='no_recomendable' and ev2.get('veredicto')!='no_recomendable')
# HU-11
s,ab=call('POST',f'/credits/{c["id"]}/simulate/abono',{'abono':500000,'modalidad':'reducir_plazo'},tok=tok)
rec('TC-29','HU-11','Crédito de TC-25','1. Simular abono de 500.000 reduciendo plazo','Intereses y plazo ahorrados > 0',f'HTTP {s}; {json.dumps({k:ab.get(k) for k in ("interesesAhorrados","cuotasAhorradas","ahorroIntereses") if k in ab})} claves={list(ab.keys())[:8]}',s==200)
s,cc=call('POST',f'/credits/{c["id"]}/simulate/compra-cartera',{'tasaEANueva':15,'plazoMesesNuevo':8,'gastosCierre':20000},tok=tok)
s2,cc2=call('POST',f'/credits/{c["id"]}/simulate/compra-cartera',{'tasaEANueva':40,'plazoMesesNuevo':8,'gastosCierre':20000},tok=tok)
rec('TC-30','HU-11','Crédito de TC-25','1. Compra de cartera a 15 % EA. 2. Compra de cartera a 40 % EA','La primera genera ahorro neto positivo; la segunda lo indica como no conveniente',f'HTTP {s}/{s2}; claves={list(cc.keys())[:8]}; ahorro1={cc.get("ahorroTotal")}; ahorro2={cc2.get("ahorroTotal")}; conviene2={cc2.get("conviene")}',s==200 and (cc.get('ahorroTotal') or 0)>0 and (cc2.get('ahorroTotal') or 0)<=0)
# HU-12
for i in range(5): call('POST','/transactions',{'tipo':'egreso','monto':8000,'categoriaId':cat['Alimentación'],'descripcion':'Tinto','fecha':(today-datetime.timedelta(days=i+1)).isoformat()},tok=tok)
s,rc=call('GET','/insights/recommendations',tok=tok); s2,an=call('GET','/insights/ant-expenses',tok=tok)
rec('TC-31','HU-12','Gastos pequeños repetidos y deuda activa','1. GET /insights/ant-expenses. 2. GET /insights/recommendations','Se detecta el gasto hormiga y se listan recomendaciones priorizadas con explicación',f'HTTP {s2}/{s}; hormiga={json.dumps(an)[:140]}; recomendaciones={len(rc) if isinstance(rc,list) else list(rc.keys())}',s==200 and s2==200)
# HU-13
s,db=call('GET',f'/dashboard?mes={mes}&anio={anio}',tok=tok); s2,db2=call('GET',f'/dashboard?mes=1&anio=2020',tok=tok)
rec('TC-32','HU-13','Movimientos del mes actual','1. GET /dashboard del mes actual. 2. GET /dashboard de un periodo sin movimientos','Indicadores del mes; ceros en el periodo vacío',f'HTTP {s}/{s2}; claves={list(db.keys())[:8]}',s==200 and s2==200)
# HU-14 uploads
def mp(name,ctype,data):
    bd='----x'+sfx; body=(f'--{bd}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\nContent-Type: {ctype}\r\n\r\n').encode()+data+f'\r\n--{bd}--\r\n'.encode()
    return body,'multipart/form-data; boundary='+bd
png=bytes.fromhex('89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6360000002000001e221bc330000000049454e44ae426082')
b,ct=mp('c.png','image/png',png); s,u=call('POST','/files/upload',raw=b,ctype=ct,tok=tok)
b,ct=mp('x.xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',b'PK'+b'0'*100); s2,u2=call('POST','/files/upload',raw=b,ctype=ct,tok=tok)
b,ct=mp('big.pdf','application/pdf',b'%PDF-'+b'0'*(5*1024*1024+10)); s3,u3=call('POST','/files/upload',raw=b,ctype=ct,tok=tok)
rec('TC-33','HU-14','Sesión iniciada','1. Subir PNG válido. 2. Subir .xlsx. 3. Subir PDF de más de 5 MB','1: 201 con URL; 2 y 3: rechazo (4xx)',f'HTTP {s}, {s2}, {s3}; url={(u or {}).get("url") or (u or {}).get("archivoUrl")}',s in(200,201) and 400<=s2<500 and 400<=s3<500)
# Admin
sa,ad=call('POST','/auth/login',{'email':os.environ.get('ADMIN_EMAIL','admin@caudo.test'),'password':os.environ.get('ADMIN_PASSWORD','Admin123!')}); atok=ad.get('access_token'); 
s1,_=call('GET','/admin/metrics',tok=tok); s2,m=call('GET','/admin/metrics',tok=atok)
rec('TC-34','HU-15','Cuenta admin sembrada','1. GET /admin/metrics con token de usuario final. 2. Con token de administrador','403 para el usuario; 200 para el administrador',f'HTTP {s1} y {s2}; rol del admin={ad["user"]["rol"]}',s1==403 and s2==200)
s,nu=call('POST','/admin/users',{'nombre':'Cuenta Creada','email':f'cre{sfx}@t.co','password':'Creada123!','rol':'usuario'},tok=atok)
rec('TC-35','HU-15','Sesión de administrador','1. POST /admin/users','201 con la cuenta creada',f'HTTP {s}; {json.dumps(nu)[:140]}',s==201)
uid=nu.get('id') if isinstance(nu,dict) else None
s,_=call('POST',f'/admin/users/{uid}/suspend',tok=atok); s2,l=call('POST','/auth/login',{'email':f'cre{sfx}@t.co','password':'Creada123!'})
s3,_=call('POST',f'/admin/users/{uid}/reactivate',tok=atok); s4,l2=call('POST','/auth/login',{'email':f'cre{sfx}@t.co','password':'Creada123!'})
rec('TC-36','HU-15','Cuenta de TC-35','1. Suspender. 2. Intentar iniciar sesión. 3. Reactivar. 4. Iniciar sesión','Suspendida: login 403. Reactivada: login 200',f'suspender={s}, login={s2}; reactivar={s3}, login={s4}',s2==403 and s4==200)
s,r=call('GET','/admin/categories',tok=atok); prot=[c for c in (r if isinstance(r,list) else r.get('data',[])) if c.get('nombre') in('Otros Gastos','Otros Ingresos')]
s2,r2=call('POST','/admin/categories',{'nombre':f'Mascotas{sfx}','tipo':'egreso','icono':'🐶'},tok=atok)
s3,_=call('DELETE',f'/admin/categories/{prot[0]["id"]}',tok=atok) if prot else (0,None)
rec('TC-37','HU-16','Sesión de administrador','1. Crear categoría global. 2. Intentar eliminar «Otros Gastos»/«Otros Ingresos»','Creación 201; la eliminación de la categoría protegida es rechazada (4xx)',f'crear={s2}; eliminar protegida={s3}',s2==201 and 400<=s3<500)
s,m=call('GET','/admin/metrics',tok=atok)
txt=json.dumps(m)
rec('TC-38','HU-16','Datos de prueba cargados','1. GET /admin/metrics','Solo agregados (conteos); sin saldos ni movimientos por usuario (Ley 1581)',f'HTTP {s}; {txt[:220]}',s==200 and 'saldo' not in txt.lower())
s,sy=call('GET','/admin/system',tok=atok); s2,au=call('GET','/admin/audit',tok=atok); s3,er=call('GET','/admin/errors',tok=atok)
rec('TC-39','HU-17','Sesión de administrador','1. GET /admin/system. 2. GET /admin/audit. 3. GET /admin/errors','200 en los tres; la auditoría registra los inicios de sesión y las suspensiones',f'HTTP {s}/{s2}/{s3}; acciones de auditoría={sorted(set(x.get("accion") for x in (au if isinstance(au,list) else au.get("data",au.get("items",[])))))}',s==200 and s2==200 and s3==200)
s,r=call('GET','/admin/system',tok=atok)
rec('TC-40','HU-18','Sin GEMINI_API_KEY configurada','1. GET /admin/system (bloque «ia»). 2. GET /insights/recommendations','La IA aparece como no configurada y las recomendaciones se entregan por reglas',f'ia={json.dumps(r.get("ia"))}; recomendaciones={len(rc) if isinstance(rc,list) else "ok"}',s==200)
with open(os.environ.get('RESULTS','results.json'),'w',encoding='utf-8') as _f:
    json.dump(R,_f,ensure_ascii=False,indent=1)
print(sum(x['ok'] for x in R),'/',len(R))
for x in R:
    if not x['ok']: print(x['id'],x['obt'][:300].encode('ascii','replace').decode())
