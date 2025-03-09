

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from ..models import User
from passlib.context import CryptContext # bu şifreleme yapmak için oluşturulmuş kütüphanedir
from ..database import SessionLocal # Erişebilmek için 2 tane nokta koydum
from typing import Annotated
from sqlalchemy.orm import Session
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer # Bunlar fastapi'nin sağladığı kolaylıklardan biridir. Yeniden form oluşturmak yerine bu import ettiğim sınıflar aracılığıyla benim yerime form oluşturup yollayabilir. Bunları Dependency Injection ile kullanmam gerek..!
from jose import jwt, JWTError # Bu jose kütüphanesi JWT formatında çalışırken JSON şeklindeki nesneleri oluştururken kullandığım kütüphanedir..!
from datetime import timedelta, datetime, timezone # bu kısımı expires_delta: timedelta için import ettim. python'ın içinde bu kütüphane hazır bulunur.
from fastapi.templating import Jinja2Templates # Bunu yaparak aslında templates klasörünün içindeki HTML dosyalarını buraya import etmiş oldum.



router = APIRouter(prefix='/auth', tags=['Authentication'])


templates = Jinja2Templates(directory='app/templates') # Burada tempaltes adında değişken oluşturdum ve Jinja2Templates sınıfının içine templates klasörünü belirttim. Bunu yaptıktan sonra normal sayfalarımı yapıp bunu orada kullanacağım. # Sonradan Docker işlemlerinde canlıya alınca sıkıntı olmaması için (app'e koymak için) app/ ekledim..!


# Bu kısımda JWT oluşturuyorum (JWT.io sitesinde örnek olarak var)
SECRET_KEY = 'qjyv26f93s0za9v7iz6gdflp0uhh05un' # anahtar kelimemi random org kısmından oluşturdum. (kendim de oluşturabilirim) Bu anahtar kelimemle signature oluşturulacak.
ALGORITHM = 'HS256' # kullanacağım algoritmayı seçtim. (başka algoritmalarda seçebilirim)



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]



bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto') # schemes=['bcrypt'] -> şifreleme için kullanacağım algoritma.  deprecated='auto' -> algoritmaların güvenliğini ve geçerliliğini otomatik olarak yönetir.
# bcrypt şifreleme algoritması her seferinde farklı çıktı verir ancak bu onun algoritmasal özelliğidir. (örn. sha256 aynı çıktıyı veriyordu)

oauth2_bearer = OAuth2PasswordBearer(tokenUrl='/auth/token') # tokenUrl='/auth/token' yaptım çünkü prefix= kısmında '/auth' olarak vermiştim..!     # Böyle bişey yapmamın sebebi bu tokenUrl'den bir istek (request) atıldığında (yani @router.post('/token') kısmına) bana geri token verir.



class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str
    phone_number: str # migrations ile User tablosuna phone_number sütunu eklediğim için auth.py kısmında da bunu yapmak zorundayım yoksa phone_number null olur. '/create_user' kısmında eklediğim için request classına da eklemek zorundayım.



class Token(BaseModel): # Token sınıfı oluşturdum. Çünkü gelen token isteklerinde döndürülen token'ı yapısal olarak belirtmek daha iyidir..!
    access_token: str
    token_type: str



# jwt token'ını encode etmek için fonksiyon yazıyorum
def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta): # expires_delta: timedelta -> ne kadar sürede token'ın süresinin dolacağını yani geçersiz olacağını gösterir..!   # user_id -> aslında user'ın veritabanında bulunan id'sidir.
    payload = {'sub': username, 'id': user_id, 'role': role}
    expires = datetime.now(timezone.utc) + expires_delta
    payload.update({'exp': expires})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)



def authenticate_user(username: str, password: str, db):  # kullanıcının parolasını aldığımda doğrulamak için yaptım. username ve password belirledim. (bunlar değiştirilebilir..!)
    user = db.query(User).filter(User.username == username).first() # önce eşleşen kullanıcı var mı bakıyorum
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password): # password ile kullanıcının şifrelenmiş passwordu aynı mı değil mi (match) diye kontrol edilir
        return False
    return user # user bilgileri doğruysa return eder.



# jwt token'ını decode etmek için fonksiyon yazıyorum
async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]): # Bu fonksiyonu oluşturma sebebim JWT'yi decode etmektir. Çünkü kullanıcıdan JWT geldiğinde o token'ı decode edip gerçekten kullanıcı mı atmış diye kontrol etmem gerekir. (Kötü niyetli yazılımlar, insanları vb. önlemek için bunu yapıyorum)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get('sub')
        user_id = payload.get('id')
        role = payload.get('role')
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Username or ID is invalid!')
        return {'username': username, 'id': user_id, 'role': role}
    except JWTError: # yukarıda yazdıklarım başarısız olursa JWTError ile HTTPException fırlatırım.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token is invalid!')



# region HTML templates return kısmı
@router.get('/login-page') # Burada yapılan -> tarayıcıda login-page üstünden girilirse login.html'i göster dedim. request'i de cevabın içinde login-page'e yolluyorum.
def render_login_page(request: Request):
    return templates.TemplateResponse('login.html', {'request': request})


@router.get('/register-page') # Yukardaki işlemin aynısını register.html için yaptım.
def render_register_page(request: Request):
    return templates.TemplateResponse('register.html', {'request': request})
# endregion



@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_user(db:db_dependency, create_user_request: CreateUserRequest):
    # user = User(**create_user_request.model_dump()) # bu sefer bu yöntem çalışmaz. Çünkü request password istiyor fakat User sınıfında hashed_password var. Bunun temeli kanunlara dayanır. (kullanıcının parolasını kimse görmemeli)
    # Bu yüzden şifreleme algoritması kullanılır. Şifreleme algoritmasının çalışma mantığı (örn. olarak 123456 diye parola var ve ben onu ABefHROPTYQx gibi şifreliyorum) kullanıcı her parolasını yeniden girdiğinde benim şifreleme algoritmamın da veritabanında kullanıcının parolası için oluşturduğu şifreyi vermesi yani aynı çıktıyı vermesidir..! (örn. olarak sha256 şifreleme aracıdır.)

    user = User(
        username=create_user_request.username,
        email=create_user_request.email,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role=create_user_request.role,
        is_active=True,
        hashed_password=bcrypt_context.hash(create_user_request.password), # bu kısmı direkt create_user_request.password diyerek veremem. Önce şifreleyip vermem gerekir..!
        phone_number=create_user_request.phone_number # migrations ile User tablosuna phone_number sütunu eklediğim için auth.py kısmında da bunu yapmak zorundayım yoksa phone_number null olur.
    ) # bcrypt_context.hash(create_user_request.password) işlemi ile artık create_user_request.password ifadesinden geleni alıp kullanıcak ve şifrelicek.
    db.add(user)
    db.commit()



@router.post('/token', response_model= Token) # response_model= Token -> Token dönen isteklerde bunu belirtmek önemlidir. Burada yukarıda oluşturduğum Token sınıfını belirtiyorum (daha iyi)
# burada yazdığım token mantığı -> Kullanıcının doğru olduğunu anladıktan sonra kullanıcıya token değeri verilir. Bu değer string olabilir yani şifrelenmiş bir metindir. Bu yöntem çok yaygındır. Kullanıcı login yaptığında token verilir ve bundan sonraki bütün yapacağı isteklerde bu token takip edilir..! (örn. gelen isteklerde hacker gibi kötü niyetliler vb.) Herhangi bir sıkıntı olmaması açısından kullanıcı giriş yaptığında kullanıcıya bir token verilir ve bu token gerçek bir token mi, kullanıcı için mi oluşturulmuş vb. gibi bunun takibi yapılır. Bunu yapılması için de kullanıcıdan username ve password alınması ve doğrulanması gerekir. (yani authenticate_user() yapılması gerekir.)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db:db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Incorrent username or password..!')
    token = create_access_token(user.username, user.id, user.role, timedelta(minutes=60)) # Buradaki token'da aslında bir JSON nesnesi döndüreceğim ve bu JSON nesnesi de JWT Prensiplerine göre hazırlanır.   # yukarıda oluşturduğum create_access_token() fonksiyonunu burada token oluşturma kısmında kullandım..!
    return {'access_token': token, 'token_type': 'bearer'} # 'token_type': 'bearer' -> istek atarken tokenın kullanıcı tarafından geldiğini gösteren token tipidir..!