from app import app, db

def test_db_connection():
    with app.app_context():
        try:
            # Veritabanı bağlantısını test et
            db.session.execute('SELECT 1')
            print("Veritabanı bağlantısı başarılı!")
            return True
        except Exception as e:
            print(f"Veritabanı bağlantı hatası: {str(e)}")
            return False

if __name__ == '__main__':
    test_db_connection() 