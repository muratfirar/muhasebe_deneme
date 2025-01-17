import xml.etree.ElementTree as ET
from collections import defaultdict
from decimal import Decimal
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from datetime import datetime

def dosya_sec():
    root = tk.Tk()
    root.withdraw()  # Ana pencereyi gizle
    
    dosya_yolu = filedialog.askopenfilename(
        title="Muhasebe XML Dosyasını Seçin",
        filetypes=[("XML Dosyaları", "*.xml"), ("Tüm Dosyalar", "*.*")],
        initialdir=Path.cwd()  # Mevcut çalışma dizininden başla
    )
    
    if dosya_yolu:
        print(f"\nSeçilen dosya: {dosya_yolu}")
        return dosya_yolu
    else:
        print("\nDosya seçilmedi!")
        return None

def cizgi_cek(uzunluk=100):
    print("=" * uzunluk)

def tablo_baslik_yazdir(baslik):
    cizgi_cek()
    print(f"{baslik:^100}")
    cizgi_cek()

def format_tutar(tutar):
    return f"{tutar:,.2f}".replace(",", ".")

def analiz_yap(xml_dosya):
    tree = ET.parse(xml_dosya)
    root = tree.getroot()
    
    # Dönem bilgisini al
    fiscal_period = root.find('.//FiscalPeriod')
    if fiscal_period is not None:
        donem_sonu = fiscal_period.text
    else:
        # Eğer FiscalPeriod bulunamazsa son işlem tarihini kullan
        son_tarih = None
        for entry in root.findall('.//Entry'):
            tarih = entry.find('.//EnteredDate')
            if tarih is not None and tarih.text:
                if son_tarih is None or tarih.text > son_tarih:
                    son_tarih = tarih.text
        donem_sonu = son_tarih or '2024-12-31'
    
    # Mizan verilerini topla
    mizan = defaultdict(lambda: {
        'hesap_kodu': '',
        'hesap_adi': '',
        'borc': Decimal('0'),
        'alacak': Decimal('0'),
        'borc_bakiye': Decimal('0'),
        'alacak_bakiye': Decimal('0')
    })
    
    # Fiş listesini topla
    fis_listesi = []
    
    # Her işlem için hesapları topla
    for entry in root.findall('.//Entry'):
        # Fiş bilgileri
        fis = {
            'no': entry.find('.//EntryNumber').text,
            'aciklama': entry.find('.//EntryComment').text,
            'tarih': entry.find('.//EnteredDate').text,
            'satirlar': []
        }
        
        for line in entry.findall('.//Line'):
            hesap_kodu = line.find('AccountMainID').text
            hesap_adi = line.find('AccountMainDescription').text
            tutar = Decimal(line.find('Amount').text)
            borc_alacak = line.find('DebitCreditCode').text
            
            # Mizan için hesapları topla
            if hesap_kodu not in mizan:
                mizan[hesap_kodu].update({
                    'hesap_kodu': hesap_kodu,
                    'hesap_adi': hesap_adi
                })
            
            if borc_alacak == 'D':
                mizan[hesap_kodu]['borc'] += tutar
            else:
                mizan[hesap_kodu]['alacak'] += tutar
            
            # Fiş satırını ekle
            fis['satirlar'].append({
                'hesap_kodu': hesap_kodu,
                'hesap_adi': hesap_adi,
                'borc': tutar if borc_alacak == 'D' else Decimal('0'),
                'alacak': tutar if borc_alacak == 'C' else Decimal('0')
            })
        
        fis_listesi.append(fis)
    
    # Bakiyeleri hesapla
    toplam_borc = Decimal('0')
    toplam_alacak = Decimal('0')
    toplam_borc_bakiye = Decimal('0')
    toplam_alacak_bakiye = Decimal('0')
    
    for hesap in mizan.values():
        borc = hesap['borc']
        alacak = hesap['alacak']
        borc_bakiye = max(borc - alacak, Decimal('0'))
        alacak_bakiye = max(alacak - borc, Decimal('0'))
        
        hesap['borc_bakiye'] = borc_bakiye
        hesap['alacak_bakiye'] = alacak_bakiye
        
        toplam_borc += borc
        toplam_alacak += alacak
        toplam_borc_bakiye += borc_bakiye
        toplam_alacak_bakiye += alacak_bakiye
    
    # Sonuçları döndür
    return {
        'mizan': list(mizan.values()),
        'fis_listesi': fis_listesi,
        'toplam': {
            'borc': toplam_borc,
            'alacak': toplam_alacak,
            'borc_bakiye': toplam_borc_bakiye,
            'alacak_bakiye': toplam_alacak_bakiye
        },
        'donem_sonu': donem_sonu
    }

if __name__ == "__main__":
    print("Muhasebe Analiz Programı")
    print("------------------------")
    
    dosya_yolu = dosya_sec()
    if dosya_yolu:
        analiz_yap(dosya_yolu) 