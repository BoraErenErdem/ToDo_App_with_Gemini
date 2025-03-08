# Bu kodların hepsini FastAPI dökümantasyonundan aldım. 1 kere bu kodu yazınca bir daha yazmama gerek kalmaz..!

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

sqlalchemy_database_url = 'sqlite:///./todoai_app.db' # Bu ifadenin anlamı database projenin içinde oluşturulucak demek. todoai_app.db oluşuturulacak database'in ismidir. Değiştirilebilir
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"   -> sqlalchemy kullandığım için hem sqlite hem de Postgresql kullanabilirim..! Bu kullanım Postgresql örneğidir


engine = create_engine(sqlalchemy_database_url, connect_args={'check_same_thread': False}) # bu kısım yukarıda yazdığım url'yi alır ve bağlantıyı nasıl açacağına bakar

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) # bu kısım veritabanı ile bağlantı açar

Base = declarative_base()