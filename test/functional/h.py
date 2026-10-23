import json,os,urllib.request,urllib.error,uuid
# URL de la API a probar. Por defecto, el backend local (Docker): http://localhost:3000/api
B=os.environ.get('API_URL','http://localhost:3000/api').rstrip('/')
def call(m,path,body=None,tok=None,raw=None,ctype=None):
    h={}
    data=None
    if body is not None: data=json.dumps(body).encode(); h['Content-Type']='application/json'
    if raw is not None: data=raw; h['Content-Type']=ctype
    if tok: h['Authorization']='Bearer '+tok
    r=urllib.request.Request(B+path,data=data,method=m,headers=h)
    try:
        with urllib.request.urlopen(r) as x: t=x.read().decode(); return x.status,(json.loads(t) if t else None)
    except urllib.error.HTTPError as e:
        t=e.read().decode()
        try: return e.code,json.loads(t)
        except: return e.code,t
