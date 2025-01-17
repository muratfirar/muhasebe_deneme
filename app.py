from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from decimal import Decimal
import xml.etree.ElementTree as ET
from collections import defaultdict
import os
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from config import TDHPConfig
from models import db, Firma, FirmaTuru
from muhasebe_analiz import analiz_yap
import json

app = Flask(__name__)

# Proje kök dizinini al
basedir = os.path.abspath(os.path.dirname(__file__))

# Veritabanı konfigürasyonu
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://murat:123357789@localhost:5432/muhasebe_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Diğer konfigürasyonlar
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = 'gizli-anahtar-buraya'
app.config['MAX_PERIODS'] = 3

# Session konfigürasyonu
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True

# SQLAlchemy'yi başlat
db.init_app(app)

# Upload klasörünü oluştur
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Veritabanını oluştur
with app.app_context():
    db.create_all()

# Jinja2 filtresi - para formatı için
@app.template_filter('para_format')
def para_format(value):
    try:
        if value is None:
            return "0,00 ₺"
        return f"{float(value):,.2f} ₺".replace(",", ".")
    except (ValueError, TypeError):
        return "0,00 ₺"

# Upload klasörü için MIME type kontrolü ekle
ALLOWED_EXTENSIONS = {'xml'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/veri-girisi', methods=['GET'])
def veri_girisi():
    # Sayfa yüklenirken session'ı temizle
    for key in list(session.keys()):
        if key.startswith('sonuclar_donem_'):
            session.pop(key)
    return render_template('veri_girisi.html', max_periods=app.config['MAX_PERIODS'])

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'Dosya seçilmedi'}), 400
        
    files = []
    for i in range(1, app.config['MAX_PERIODS'] + 1):
        file_key = f'file_{i}'
        if file_key in request.files:
            file = request.files[file_key]
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                try:
                    sonuclar = analiz_yap(filepath)
                    session[f'sonuclar_donem_{i}'] = sonuclar
                    files.append(filename)
                except Exception as e:
                    return jsonify({'error': f'Dosya analiz hatası: {str(e)}'}), 400

    return jsonify({'success': True, 'files': files})

@app.route('/mizan', methods=['GET'])
def mizan():
    # Tüm dönemlerin verilerini topla
    periods_data = {}
    for i in range(1, app.config['MAX_PERIODS'] + 1):
        if f'sonuclar_donem_{i}' in session:
            periods_data[i] = session[f'sonuclar_donem_{i}']
    
    return render_template('mizan.html', periods=periods_data)

@app.route('/bilanco', methods=['GET'])
def bilanco():
    periods_data = {}
    for i in range(1, app.config['MAX_PERIODS'] + 1):
        if f'sonuclar_donem_{i}' in session:
            data = session[f'sonuclar_donem_{i}']
            
            # Bilanço hesaplarını ve grup toplamlarını hesapla
            bilanco_hesaplari = {}
            grup_toplamlari = defaultdict(lambda: {
                'net_bakiye': Decimal('0'), 
                'tip': '',
                'hesap_adi': ''  # Alt grup adı için
            })
            ana_grup_toplamlari = defaultdict(lambda: {
                'net_bakiye': Decimal('0'), 
                'tip': '',
                'hesap_adi': ''  # Ana grup adı için
            })
            
            for hesap in data['mizan']:
                hesap_kodu = hesap['hesap_kodu']
                if hesap_kodu[0] in ['1', '2', '3', '4', '5']:
                    # Decimal olarak net bakiye hesapla
                    borc_bakiye = Decimal(str(hesap['borc_bakiye']))
                    alacak_bakiye = Decimal(str(hesap['alacak_bakiye']))
                    net_bakiye = abs(borc_bakiye - alacak_bakiye)
                    tip = 'Borç' if borc_bakiye > alacak_bakiye else 'Alacak'
                    
                    # Hesap detayı
                    bilanco_hesaplari[hesap_kodu] = {
                        'hesap_kodu': hesap_kodu,
                        'hesap_adi': hesap['hesap_adi'],
                        'net_bakiye': net_bakiye,
                        'tip': tip
                    }
                    
                    # Ana grup toplamı için
                    ana_grup = hesap_kodu[0]
                    ana_grup_toplamlari[ana_grup]['net_bakiye'] += net_bakiye
                    ana_grup_toplamlari[ana_grup]['tip'] = tip
                    ana_grup_toplamlari[ana_grup]['hesap_adi'] = TDHPConfig.get_ana_grup_adi(ana_grup)
                    
                    # Alt grup toplamı için
                    if len(hesap_kodu) >= 2:
                        alt_grup = hesap_kodu[:2]
                        grup_toplamlari[alt_grup]['net_bakiye'] += net_bakiye
                        grup_toplamlari[alt_grup]['tip'] = tip
                        grup_toplamlari[alt_grup]['hesap_adi'] = TDHPConfig.get_alt_grup_adi(alt_grup)
            
            periods_data[i] = {
                'bilanco': bilanco_hesaplari,
                'grup_toplamlari': dict(grup_toplamlari),
                'ana_grup_toplamlari': dict(ana_grup_toplamlari),
                'donem_sonu': data.get('donem_sonu', 'Tarih bilgisi yok')
            }
    
    return render_template('bilanco.html', periods=periods_data)

@app.route('/karsilastirmali-analiz', methods=['GET'])
def karsilastirmali_analiz():
    # Tüm dönemlerin verilerini topla
    periods_data = {}
    for i in range(1, app.config['MAX_PERIODS'] + 1):
        if f'sonuclar_donem_{i}' in session:
            periods_data[i] = session[f'sonuclar_donem_{i}']
    
    return render_template('karsilastirmali_analiz.html', periods=periods_data)

@app.route('/fisler', methods=['GET'])
def fisler():
    # Tüm dönemlerin verilerini topla
    periods_data = {}
    for i in range(1, app.config['MAX_PERIODS'] + 1):
        if f'sonuclar_donem_{i}' in session:
            periods_data[i] = session[f'sonuclar_donem_{i}']
    
    # Filtreleme
    fis_no = request.args.get('fis_no')
    tarih_baslangic = request.args.get('tarih_baslangic')
    tarih_bitis = request.args.get('tarih_bitis')
    hesap_kodu = request.args.get('hesap_kodu')
    donem = request.args.get('donem')
    
    # Seçili dönemin fişlerini al
    if donem and donem in periods_data:
        fis_listesi = periods_data[donem]['fis_listesi']
    else:
        # Tüm dönemlerin fişlerini birleştir
        fis_listesi = []
        for period_data in periods_data.values():
            fis_listesi.extend(period_data['fis_listesi'])
    
    # Filtreleri uygula
    if fis_no:
        fis_listesi = [f for f in fis_listesi if fis_no in f['no']]
    if tarih_baslangic:
        fis_listesi = [f for f in fis_listesi if f['tarih'] >= tarih_baslangic]
    if tarih_bitis:
        fis_listesi = [f for f in fis_listesi if f['tarih'] <= tarih_bitis]
    if hesap_kodu:
        fis_listesi = [f for f in fis_listesi if any(s['hesap_kodu'].startswith(hesap_kodu) for s in f['satirlar'])]
    
    return render_template('fisler.html', fis_listesi=fis_listesi, periods=periods_data)

@app.route('/firma-tanim', methods=['GET', 'POST'])
def firma_tanim():
    if request.method == 'POST':
        firma = Firma(
            unvan=request.form['unvan'],
            vergi_no=request.form['vergi_no'],
            vergi_dairesi=request.form['vergi_dairesi'],
            telefon=request.form['telefon'],
            email=request.form['email'],
            adres=request.form['adres'],
            firma_turu_id=request.form['firma_turu']
        )
        db.session.add(firma)
        try:
            db.session.commit()
            return redirect(url_for('firma_listesi'))
        except Exception as e:
            db.session.rollback()
            return str(e), 400
            
    firma_turleri = FirmaTuru.query.all()
    return render_template('firma_tanim.html', firma_turleri=firma_turleri)

@app.route('/firma-listesi')
def firma_listesi():
    firmalar = Firma.query.all()
    return render_template('firma_listesi.html', firmalar=firmalar)

@app.route('/firma-duzenle/<int:id>', methods=['GET', 'POST'])
def firma_duzenle(id):
    firma = Firma.query.get_or_404(id)
    if request.method == 'POST':
        firma.firma_turu = request.form['firma_turu']
        firma.unvan = request.form['unvan']
        firma.vergi_no = request.form['vergi_no']
        firma.vergi_dairesi = request.form['vergi_dairesi']
        firma.adres = request.form['adres']
        firma.telefon = request.form['telefon']
        firma.email = request.form['email']
        firma.yetkili_adi = request.form['yetkili_adi']
        firma.yetkili_telefon = request.form['yetkili_telefon']
        firma.aciklama = request.form['aciklama']
        db.session.commit()
        return redirect(url_for('firma_listesi'))
    
    firma_turleri = FirmaTuru.choices()
    return render_template('firma_tanim.html', firma=firma, firma_turleri=firma_turleri)

@app.route('/firma-sil/<int:id>', methods=['DELETE'])
def firma_sil(id):
    firma = Firma.query.get_or_404(id)
    db.session.delete(firma)
    db.session.commit()
    return '', 204

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)  # use_reloader=False ekledik 