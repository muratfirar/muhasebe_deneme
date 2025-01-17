import click
from flask import Flask
from models import db, Firma, FirmaTuru
from dotenv import load_dotenv
import os
from sqlalchemy import text

# .env dosyasını yükle
load_dotenv()

app = Flask(__name__)

# Veritabanı konfigürasyonu
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://murat:123357789@localhost:5432/muhasebe_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# SQLAlchemy'yi başlat
db.init_app(app)

@click.group()
def cli():
    """Veritabanı yönetim komutları"""
    pass

@cli.command('create-db')
def create_db():
    """Veritabanını oluştur"""
    with app.app_context():
        try:
            db.create_all()
            print("Veritabanı başarıyla oluşturuldu!")
        except Exception as e:
            print(f"Hata oluştu: {str(e)}")

@cli.command('drop-db')
def drop_db():
    """Veritabanını sil"""
    with app.app_context():
        try:
            # Önce tüm tabloları CASCADE ile sil
            db.session.execute(text('DROP SCHEMA public CASCADE'))
            db.session.execute(text('CREATE SCHEMA public'))
            db.session.commit()
            print("Veritabanı silindi!")
        except Exception as e:
            db.session.rollback()
            print(f"Hata oluştu: {str(e)}")

@cli.command('check-db')
def check_db():
    """Veritabanı durumunu kontrol et"""
    with app.app_context():
        try:
            firma_sayisi = Firma.query.count()
            firma_turu_sayisi = FirmaTuru.query.count()
            print(f"""
Veritabanı Durumu:
-----------------
Firma Sayısı: {firma_sayisi}
Firma Türü Sayısı: {firma_turu_sayisi}
Bağlantı: Başarılı
""")
        except Exception as e:
            print(f"Veritabanı hatası: {str(e)}")

@cli.command('init-firma-turleri')
def init_firma_turleri():
    """Temel firma türlerini ekle"""
    with app.app_context():
        try:
            firma_turleri = [
                FirmaTuru(ad='Şahıs Firması'),
                FirmaTuru(ad='Anonim Şirket'),
                FirmaTuru(ad='Limited Şirket'),
                FirmaTuru(ad='Komandit Şirket'),
                FirmaTuru(ad='Adi Ortaklık'),
                FirmaTuru(ad='Kooperatif'),
                FirmaTuru(ad='Diğer')
            ]
            
            for tur in firma_turleri:
                db.session.add(tur)
            db.session.commit()
            print("Firma türleri başarıyla eklendi!")
            
        except Exception as e:
            db.session.rollback()
            print(f"Hata oluştu: {str(e)}")

if __name__ == '__main__':
    cli() 