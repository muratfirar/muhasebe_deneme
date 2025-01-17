from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class FirmaTuru(db.Model):
    __tablename__ = 'firma_turu'
    
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(100), nullable=False)
    aciklama = db.Column(db.Text)
    
    @classmethod
    def choices(cls):
        return [(tur.id, tur.ad) for tur in cls.query.all()]
    
    def __repr__(self):
        return f'<FirmaTuru {self.ad}>'

class Firma(db.Model):
    __tablename__ = 'firma'
    
    id = db.Column(db.Integer, primary_key=True)
    unvan = db.Column(db.String(200), nullable=False)
    vergi_no = db.Column(db.String(10), unique=True)
    vergi_dairesi = db.Column(db.String(100))
    telefon = db.Column(db.String(20))
    email = db.Column(db.String(120))
    adres = db.Column(db.Text)
    durum = db.Column(db.Boolean, default=True)
    olusturma_tarihi = db.Column(db.DateTime, default=datetime.utcnow)
    firma_turu_id = db.Column(db.Integer, db.ForeignKey('firma_turu.id'))
    firma_turu = db.relationship('FirmaTuru', backref='firmalar') 