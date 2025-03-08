

from starlette import status
from fastapi import FastAPI, Request # Request -> Tarayıcıya istek gelirse gelen isteğin bütün detaylarını görmek için fastapi'nin Request sınıfını kullanıyorum.
from .models import Base, Todo # models.py'de tanımladığım Tod0 sınıfın import ile getirdim
from .database import engine, SessionLocal
from sqlalchemy.orm import Session
from .routers.auth import router as auth_router # routers package'ında oluşturduğum auth.py'nin routerını ekleyebilirim..!
from .routers.todo import router as todo_router # routers package'ında oluşturduğum tod0.py'nin routerını ekleyebilirim..!
from fastapi.staticfiles import StaticFiles # static dosyaları fastapi ile bağlayabilirim.
from starlette.responses import RedirectResponse
import os


app = FastAPI()

script_dir = os.path.dirname(__file__)
st_abs_file_path = os.path.join(script_dir, 'static/')

app.mount('/static', StaticFiles(directory=st_abs_file_path), name='static') # Burada (github'dan indirdiğim) static klasörünü app.mount() diyerek static klasörünün içindeki dosyaları app'in görmesi için bağladım.   # '/static' -> bağlamak istediğim klasörün adı. # StaticFiles() diyerek fastapi'nin staticfiles modülünü kullanıyorum. directory='static' -> klasör ismi static dedim. name='static' -> ismi de static olarak verdim. # Sonradan st_abs_file_path ile değiştirdim..!



@app.get('/') # Ana sayfa olarak nereye gidilsin onu burada belirledim. (Ana Sayfa)
def read_root(request: Request): # Tarayıcı tarafından gelen istekleri detaylıca görmek için yapıyorum ve Request sınıfını kullanıyorum. Yani birisi tarayıcıdan websiteme girmek istediğinde attığı isteğin (request'in) bütün detaylarına ulaşabiliyorum.
    return RedirectResponse(url='/todo/todo-page', status_code=status.HTTP_302_FOUND) # RedirectResponse -> İstek geldiği zaman nasıl cevap döndürülecek onu belirttim. Yani bana bir istek gelirse o isteği url='/tod0/tod0-page' sayfasına yollayacağım..! Burada bunu yapmamın sebebi kullanıcı bir kere giriş yaptıysa bir daha giriş yapmasına gerek kalmadan kendi todolarını görebileceği sayfaya yönlendiricem. Ancak giriş yapmadıysa zaten login sayfasına yönlendirilir.


app.include_router(auth_router) # app'e include_router(auth_router) diyerek import ettiğim auth_router ekledim
app.include_router(todo_router) # app'e include_router(todo_router) diyerek import ettiğim todo_router ekledim


Base.metadata.create_all(bind=engine) # database.py'de oluşturuduğum engine adlı değişkenin içine yazdığım sqlalchemy_database_url ile birlikte projemde (sqlalchemy_database_url içide yazdığım) todoai_app.db adlı dosyaya bakar eğer bu isimde dosya yoksa oluşturur varsa hiç bişey yapmaz.