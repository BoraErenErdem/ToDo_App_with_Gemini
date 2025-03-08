

from fastapi import APIRouter, Body, Path, Query, Depends, HTTPException, Request
from ..models import Base, Todo # models.py'de tanımladığım Tod0 sınıfın import ile getirdim
from ..database import engine, SessionLocal
from sqlalchemy.orm import Session
from typing import Annotated
from starlette import status
from pydantic import BaseModel, Field
from ..routers.auth import get_current_user # routers package'ının auth.py dosyasının içindeki get_current_user() fonksiyonunu import ettim
from fastapi.templating import Jinja2Templates # Aynı şekilde Jinja2Templates sınıfını import ettim.
from starlette.responses import RedirectResponse # Aşağıda oluşturduğum fonksiyonda user olmayanları login kısmına göndereceğim için login-page kısmına gönderen bir fonksiyon daha oluşturdum. Orada kullanıyorum.
from dotenv import load_dotenv # Bu fonksiyon oluşturduğum .env dosyasının (GOOGLE_API_KEY= olan dosyayı) bu dosya içinde kullanılmasını sağlar. (Yani .env dosyasının tod0.py dosyasında kullanılmasını sağlar..!)
import google.generativeai as genai # Google'ın generative ai'ı olan Gemini'yi kullanmak için bunu yaptım
import os # pythonda yer alan kütüphanedir. (operating system)
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
import markdown # generative ai modelimin çıktıları markdown şeklinde vermemesi için kendi oluşturduğum fonksiyonda bunu kullanıyorum.
from bs4 import BeautifulSoup # BeautifulSoup kütüphanesi HTML'i işleyen kütüphanedir. Bunu da generative ai modelimin markdown çıktı vermemesi için kendi oluşturduğum fonksiyonda kullanıyorum.



router = APIRouter(prefix='/todo', tags=['Todo'])



templates = Jinja2Templates(directory='app/templates') # Aynı şekilde HTML dosyalarının içinde bulunduğu templates klasörünün adını verdim. # Sonradan Docker işlemlerinde canlıya alınca sıkıntı olmaması için (app'e koymak için) app/ ekledim..!



class TodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=1000)
    priority: int = Field(ge=1, le=5)
    complete: bool

    model_config = { # Bunu yapmak zorunda değilim. Pratik ve yol gösterici olsun diye yaptım.
        "jdon_schema_extra": {
            "example":{
                "title": "Todo title",
                "description": "Todo description",
                "priority": "Todo priority (between 1 and 5)",
                "complete": "Done(1) or Not Done(0)"
            }
        }
    }



def get_db(): # bu fonksiyon veritabanını verir.
    db = SessionLocal() # Genellikle SessionLocal ile çalışırken yield kullanılır.
    try:
        yield db  # yield -> return ile aynı şeyi yapar. Yani döndürür. Return'den farkı olarak tek bir değer döndürmek yerine yield birden fazla değerleri döndürebilir.
    finally:
        db.close() # bilerek vertabanı bağlantısını kapatıyorum. Açık bırakırsam bağlantı sayısını kullanımabağlı olarak aşabilir ve veritabanı patlayabilir.


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)] # import ettiğim get_current_user() fonksiyonunu DI Annotated yaptım. get_current_user() fonksiyonu return olarak dict döndüğü için (auth.py dosyasından bakabilirsin) dict dedim.


def redirect_to_login():
    redirect_response = RedirectResponse(url='/auth/login-page', status_code=status.HTTP_302_FOUND)
    redirect_response.delete_cookie('access_token') # Kullanıcının cookie'sindeki token ile kayıtlı token eşleşmiyorsa kullanıcının token'ı silinir.
    return redirect_response # Kullanıcı tekrardan login-page'e yönlendirilir.



# region HTML templates return kısmı
@router.get('/todo-page')
async def render_todo_page(request: Request, db: db_dependency): # Bu kısımda auth.py'deki gibi direkt return templates.TemplateResponse yapamam. Çünkü kullanıcı direkt giriş yapmadan /tod0-page kısmına giderse yine de girebilir! Ama giriş yapmayan kullanıcının girememesi lazım! Yani uygulamada güvenlik açığı oluşmuş olur..!
    try:
        user = await get_current_user(request.cookies.get('access_token')) # kullanıcının cookie'sinin içerisine nasıl kaydedildiyse öyle yazmam gerekiyor. (Yani access_token yazmamın sebebi kullanıcıları base.js dosyasında access_token olarak kaydetmemden.)
        if user is None:
            return redirect_to_login()
        todos = db.query(Todo).filter(Todo.owner_id == user.get('id')).all() # Kullanıcının todolarını aldım çünkü tod0.html'nin içine kullanıcının todolarını vermem lazım.
        return templates.TemplateResponse('todo.html', {'request': request, 'todos': todos, 'user': user})
    except:
        return redirect_to_login()



@router.get('/add-todo-page')
async def render_add_todo_page(request: Request):
    try:
        user = await get_current_user(request.cookies.get('access_token'))
        if user is None:
            return redirect_to_login()
        return templates.TemplateResponse('add-todo.html', {'request': request, 'user': user})
    except:
        return redirect_to_login()



@router.get('/edit-todo-page/{todo_id}') # Edit yapacağım todonun id'sini Path ile aldım.
async def render_add_todo_page(request: Request, todo_id: int, db: db_dependency):
    try:
        user = await get_current_user(request.cookies.get('access_token'))
        if user is None:
            return redirect_to_login()
        todo = db.query(Todo).filter(Todo.id == todo_id).first()
        return templates.TemplateResponse('edit-todo.html', {'request': request, 'todo':todo, 'user': user})
    except:
        return redirect_to_login()
# endregion



@router.get('/')
async def get_all(user: user_dependency, db: db_dependency): # artık çalışması için user_dependency'e ihtiyacı var. (yani get_current_user() fonksiyonuna ihtiyacı var)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    # return db.query(Tod0).all()  # burada db'ye yapmış olduğum .query(Tod0) sorugusu ile .all() diyerek bütün veritabanındaki verileri getirmesini istedim
    return db.query(Todo).filter(Todo.owner_id == user.get('id')).all()


@router.get('/todo/{todo_id}', status_code=status.HTTP_200_OK)
async def get_by_id(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    # todo0 = db.query(Tod0).filter(Tod0.id == todo_id).first() # bu ifade bana birden fazla Tod0 gelirse diye liste döndürür. Bu yüzden .first() yazarak ilk gelen elemanı alabilirim.
    todo = db.query(Todo).filter(Todo.id == todo_id).filter(Todo.owner_id == user.get('id')).first() # Bunu yapmamın sebebi hackerlara vb kötü niyetli yazılımlara karşı önlem almak (örn. bunu yapmazsam web sızma testlerinde araya proxy açarak rahatça erişilebilir) ve bu verilen Tod0'nun id'sini bul ve bulunan Tod0 gerçekten JWT'deki id'si olan kullanıcıya mı ait olduğuna bak..!
    if todo is not None:
        return todo
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Todo not found..!')


@router.post('/todo', status_code=status.HTTP_201_CREATED)
async def create_todo(user: user_dependency, db: db_dependency, todo_request: TodoRequest):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    new_todo = Todo(**todo_request.model_dump(), owner_id=user.get('id')) # owner_id=user.get('id') -> bunu yaparak token'dan aldıım veriyi artık kullanabiliyorum..!
    new_todo.description = create_todo_with_gemini(new_todo.description) # tod0 kaydedilmeden önce tod0'unun açıklamasını Gemini'a yaptırmak için oluşturduğum fonksiyonla değiştiriyorum.
    db.add(new_todo) # db'ye yeni veri ekler
    db.commit() # işlemin yapılacağı anlamına gelir. db.add(new_todo) yapıp db.commit() yapmazsam işlem yapılmaz..!


@router.put('/todo/{todo_id}', status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(user: user_dependency, db: db_dependency, todo_request: TodoRequest, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    todo = db.query(Todo).filter(Todo.id == todo_id).filter(Todo.owner_id == user.get('id')).first()
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Todo not found..!')

    todo.title = todo_request.title
    todo.description = todo_request.description
    todo.priority = todo_request.priority
    todo.complete = todo_request.complete

    db.add(todo) # bu kısmı yazmak zorunda değilim. Sadece pratik alıştırma olsun diye yazıyorum. Zaten db.commit() değişkenlikleri kaydeder..!
    db.commit()


@router.delete('/todo/{todo_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    todo = db.query(Todo).filter(Todo.id == todo_id).filter(Todo.owner_id == user.get('id')).first()
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Todo not found..!')

    #db.query(Tod0).filter(Tod0.id == todo_id).delete() # db.delete() işleminin uzun versiyonu
    db.delete(todo)
    db.commit()



# Bu kısmı generative ai modelimin çıktı olarak markdown şeklinde çıktı vermemesi için yapıyorum.
def markdown_to_text(markdown_string): # Bu fonksiyonu çıktıları markdown şeklinde veren generative ai'larda kullanabilirim.
    html = markdown.markdown(markdown_string) # html olduğunu belirttim
    soup = BeautifulSoup(html, 'html.parser') # BeautifulSoup kullanarak oluşturduğum html'i kullanacağımı ve 'html.parser' olarak görev yapacağını belirttim.
    text = soup.get_text()
    return text



# Bu kısımda Gemini ile tod0 açıklaması oluşturması için kendim fonksiyon yazıyorum.
def create_todo_with_gemini(todo_string: str):
    load_dotenv()
    genai.configure(api_key=os.environ.get('GOOGLE_API_KEY')) # Bu kısımda kullanacağım generative ai'ı .configure() ile gösteriyorum.  # .config() içerisinde api_key= belirtiyorum. Burada .env dosyası ile çalıştığım için os.environ.get('GOOGLE_API_KEY') diyerek .env dosyasının içinde belirttiğim google api anahatırını buraya yazıyorum. (.env dosyasıyla çalıştığım için os.environ.get() diyerek GOOGLE_API_KEY'i anca alabildim. Sektör standartlarında böyle yapılır o yüzden böyle yaptım..!)
    llm = ChatGoogleGenerativeAI(model='gemini-2.0-flash') # Burada model='gemini-2.0-flash' diyerek Gemini'nin 2.0 flash versiyonunu kullanacağımı belirttim.
    response = llm.invoke( # Burada .invoke() ile istediğim mesajları bir dizi olarak [] verebilirim. Bu LangChain'in özelliğidir.
        [
            HumanMessage(content='Todo listeme ekleyebileceğin bir todo maddesi sağlayacağım. Senden istediğim şey, bu todo maddesinin daha uzun ve daha kapsamlı bir açıklamasını oluşturman:'), # import ettiğim HumanMessage generative ai'a insan tarafından yani benim tarafımdan söylenecek mesajdır (prompt)..!
            HumanMessage(todo_string)
        ]
    )
    return markdown_to_text(response.content) # .content ile generative ai'ın cevabını verir.