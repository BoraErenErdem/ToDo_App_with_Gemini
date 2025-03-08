

from .database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey


class Todo(Base): # database.py'de oluşturduğum Base'i (Base = declarative_base()) kullanıyorum. Çünkü bu sınıf sql'deki tabloları oluşturmaktan sorumludur.
    __tablename__ = 'todos' # tablo ismini belirlemek için __tablename__ = '' yapılır. Ben tablomun adına todos dedim.

    id = Column(Integer, primary_key=True, index=True) # id'nin bir sütun olmasını belirttim ve integer olmasını, primary key olmasını ve index olmasını belirledim.
    title = Column(String)
    description = Column(String)
    priority = Column(Integer)
    complete = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey('users.id')) # ForeignKey('user.id') ifadesi aslında yabancı anahtar demektir yani bu anahtar Tod0 tablosunda değil başka bir tabloda anlamına gelir. Ve bu ForeignKey diğer tablounun (yani users tablosunun) id'si ile eşleşiyor..! Bu ilişki tipine de one to many denir. Çünkü bir kullanıcının birden çok Tod0'su olabilir.




class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True) # unique= parametresi ifadenin benzersiz olup olmamasını belirler.
    username = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String) # hashed_password -> parolanın şifrelenmiş halidir. Böyle yapmamın sebebi veritabanında asla parolaları açık metin olarak tutulmamalıdır..! (parola şifreledim)
    is_active = Column(Boolean, default=True) # kullancının aktif olup olmadığını görmek için böyle bir Column yaptım. (isteğe bağlı)
    role = Column(String) # kullanıcının rolü (admin, misafir, yetkili vb.) (isteğe bağlı)
    phone_number = Column(String)