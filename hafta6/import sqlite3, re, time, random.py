import sqlite3, re, time, random
import pandas as pd
from google import genai

# API Anahtari
API_KEY = "AQ.Ab8RN6KgmFEwKqs5jZAIwb4VXdGUxwdjWi30evzwGg6nVeu0rQ"
client = genai.Client(api_key=API_KEY)

# 1. VERITABANI OLUSTURMA VE TABLOLAR
conn = sqlite3.connect(':memory:')
cursor = conn.cursor()
cursor.execute("CREATE TABLE musteriler (musteri_id INT, ad_soyad TEXT, sehir TEXT)")
cursor.execute("CREATE TABLE siparisler (siparis_id INT, musteri_id INT, tutar REAL, tarih TEXT)")

# 1.000 musteri ve 1.000 siparis verisi uretip ekleme
sehirler = ['İstanbul', 'Ankara', 'İzmir', 'Bursa', 'Antalya']
isimler = ['Ahmet', 'Mehmet', 'Ayşe', 'Fatma', 'Ali', 'Zeynep', 'Mustafa', 'Elif', 'Emre', 'Gamze']
soyisimler = ['Yılmaz', 'Kaya', 'Demir', 'Çelik', 'Şahin', 'Yıldız', 'Öztürk', 'Aydın', 'Özdemir', 'Arslan']

musteriler_veri = []
for i in range(1, 1001):
    ad = f"{random.choice(isimler)} {random.choice(soyisimler)}"
    sehir = random.choice(sehirler)
    musteriler_veri.append((i, ad, sehir))

siparisler_veri = []
for i in range(1, 1001):
    m_id = random.randint(1, 1000)
    tutar = round(random.uniform(100.0, 10000.0), 2)
    tarih = "2026-01-01"
    siparisler_veri.append((i, m_id, tutar, tarih))

cursor.executemany("INSERT INTO musteriler VALUES (?, ?, ?)", musteriler_veri)
cursor.executemany("INSERT INTO siparisler VALUES (?, ?, ?, ?)", siparisler_veri)
conn.commit()
print("[BİLGİ] Veritabanı oluşturuldu. 1.000 müşteri ve 1.000 sipariş yüklendi.")

# 2. Guvenlik Kontrolu (Sadece SELECT izinli)
def guvenlik_kontrolu(sql_kodu: str) -> bool:
    yasakli_komutlar = r"\b(DROP|DELETE|UPDATE|INSERT|ALTER|TRUNCATE)\b"
    if re.search(yasakli_komutlar, sql_kodu, re.IGNORECASE):
        print("[GÜVENLİK ENGELİ] Zararlı SQL tespit edildi: Yasaklı komut içeriyor! Sadece SELECT izinli.")
        return False
    
    if not sql_kodu.strip().upper().startswith("SELECT"):
        print("[GÜVENLİK ENGELİ] Sadece SELECT sorgularına izin verilir!")
        return False
        
    return True

# 3. Markdown etiketlerini temizleme
def clean_sql(raw_sql: str) -> str:
    temiz = re.sub(r"```(sql)?", "", raw_sql, flags=re.IGNORECASE)
    temiz = temiz.replace("```", "").strip()
    return temiz

# 4. Gemini API entegrasyonu ve Self-Correction
def sql_asistani_calistir(kullanici_talebi: str):
    system_instruction = (
        "Aşağıdaki veritabanı şemasına göre kullanıcının doğal dille istediği veriyi çekecek SQLite uyumlu SQL sorgusunu yaz.\n"
        "Şema: musteriler(musteri_id, ad_soyad, sehir), siparisler(siparis_id, musteri_id, tutar, tarih).\n"
        "Kurallar: Sadece SELECT komutu kullan. Çıktıda markdown etiketi ve açıklama olmasın."
    )
    
    prompt = f"{system_instruction}\nKullanıcı Talebi: {kullanici_talebi}"
    deneme = 0
    max_deneme = 3

    while deneme < max_deneme:
        deneme += 1
        print(f"[GEMINI] SQL Üretiliyor... (Deneme {deneme}/{max_deneme})")
        
        try:
            yanit = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt
            )
            sql_sorgusu = clean_sql(yanit.text)
        except Exception as e:
            print(f"[API HATASI] Gemini yanıt veremedi: {e}")
            return None

        print(f"[SQL] {sql_sorgusu}")

        if not guvenlik_kontrolu(sql_sorgusu):
            return "GÜVENLİK ENGELİ"

        print("[GÜVENLİK] Denetim Başarılı (Sadece SELECT).")

        try:
            baslangic = time.perf_counter()
            df = pd.read_sql_query(sql_sorgusu, conn)
            bitis = time.perf_counter()
            sure = bitis - baslangic

            print(f"[SONUÇ] (İcra Süresi: {sure:.4f} sn)")
            if df.empty:
                print("Eşleşen kayıt bulunamadı.")
            else:
                print(df.head(10).to_string(index=False))
            return sure

        except sqlite3.Error as err:
            print(f"[SQL HATASI] Veritabanı Hatası: {err}")
            prompt = (
                f"{system_instruction}\n"
                f"Kullanıcı Talebi: {kullanici_talebi}\n"
                f"Ürettiğin hatalı sorgu: {sql_sorgusu}\n"
                f"SQLite Hatası: {err}\n"
                f"Lütfen hatayı düzelterek geçerli SQLite sorgusunu tekrar üret."
            )
            print("[SELF-CORRECTION] Hata Gemini'ye iletildi, sorgu yeniden üretilecek...")

    print("[HATA] 3 denemede de geçerli bir SQL çalıştırılamadı.")
    return None

# 5. Konsol Dongusu
def main():
    while True:
        try:
            talep = input("\nSoru Girin (Çıkış için 'q'): ").strip()
            if not talep:
                continue
            if talep.lower() == 'q':
                print("Program sonlandırılıyor...")
                break
            sql_asistani_calistir(talep)
        except KeyboardInterrupt:
            print("\nProgram kapatıldı.")
            break

if __name__ == "__main__":
    main()