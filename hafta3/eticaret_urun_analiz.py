import json
import os
from google import genai
from google.genai import errors

API_KEY = "AQ.Ab8RN6JiAfESk8zcTQdQsX7P6j4cnfRdQ2ZGyH6g8vpMNiluaw"
client = genai.Client(api_key=API_KEY)
DOSYA_ADI = "urunler.json"


# 1. Dosyadan verileri yukleme
def verileri_yukle():
    if not os.path.exists(DOSYA_ADI):
        return []
    try:
        with open(DOSYA_ADI, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


# 2. Dosyaya verileri kaydetme
def verileri_kaydet(urunler):
    try:
        with open(DOSYA_ADI, "w", encoding="utf-8") as f:
            json.dump(urunler, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[HATA] Dosya kaydedilemedi: {e}")


# 3. Gemini API ile urun analizi yapma
def gemini_ile_urun_analiz_et(urun_talebi):
    prompt = f"""
Sen kurumsal bir e-ticaret veri asistanisin.
Asagidaki urun bilgisini analiz et ve SADECE gecerli bir JSON nesnesi dondur.
Markdown veya ```json etiketi KULLANMA.

Istenen format:
{{
  "urun_adi": "Kisa ve optimize edilmis urun adi",
  "kategori": "Uygun e-ticaret kategorisi",
  "seo_etiketleri": "3 adet virgulle ayrilmis SEO etiketi",
  "satis_aciklamasi": "Musteriyi ikna edecek 2 cumle"
}}

Urun Bilgisi: {urun_talebi}
"""
    try:
        yanit = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
        )
        temiz = yanit.text.replace("```json", "").replace("```", "").strip()
        return json.loads(temiz)
    except Exception as e:
        print(f"[API HATASI] Gemini yanit veremedi: {e}")
        return None


# 4. Stok durum uyarisi
def stok_uyarisi_ver(stok):
    if stok == 0:
        print("[UYARI] STOKTA YOK!")
    elif 1 <= stok <= 4:
        print(f"[UYARI] KRITIK STOK! Yalnizca {stok} adet kaldi.")


# 5. Yeni urun ekleme
def yeni_urun_ekle():
    aciklama = input("Urun aciklamasi: ").strip()
    if not aciklama:
        print("[HATA] Aciklama bos birakilamaz.")
        return

    try:
        fiyat = float(input("Urun fiyati: "))
        stok = int(input("Stok miktari: "))
        if fiyat < 0 or stok < 0:
            print("[HATA] Fiyat ve stok negatif olamaz.")
            return
    except ValueError:
        print("[HATA] Fiyat ve stok icin gecerli bir sayi giriniz.")
        return

    print("\n[API] Urun bilgileri olusturuluyor...")
    ai_sonuc = gemini_ile_urun_analiz_et(aciklama)

    if not ai_sonuc:
        print("[HATA] Urun bilgisi alinamadigi icin kayit yapilamadi.")
        return

    urunler = verileri_yukle()
    yeni_kod = f"URN-{len(urunler) + 1:04d}"

    yeni_kayit = {
        "urun_kodu": yeni_kod,
        "urun_adi": ai_sonuc.get("urun_adi", "Isimsiz Urun"),
        "kategori": ai_sonuc.get("kategori", "Genel"),
        "seo_etiketleri": ai_sonuc.get("seo_etiketleri", ""),
        "satis_aciklamasi": ai_sonuc.get("satis_aciklamasi", ""),
        "fiyat": fiyat,
        "stok": stok,
    }

    urunler.append(yeni_kayit)
    verileri_kaydet(urunler)

    print("\n[BASARILI] Urun kaydedildi.")
    print(f"Urun Kodu : {yeni_kayit['urun_kodu']}")
    print(f"Urun Adi  : {yeni_kayit['urun_adi']}")
    print(f"Kategori  : {yeni_kayit['kategori']}")
    print(f"Fiyat     : {yeni_kayit['fiyat']} TL")
    print(f"Stok      : {yeni_kayit['stok']}")
    print(f"SEO       : {yeni_kayit['seo_etiketleri']}")
    stok_uyarisi_ver(stok)


# 6. Urunleri listeleme
def urunleri_listele():
    urunler = verileri_yukle()
    if not urunler:
        print("\n[BILGI] Kayitli urun bulunmuyor.")
        return

    print("\n" + "=" * 60)
    for u in urunler:
        print(f"Kod: {u['urun_kodu']} | Ad: {u['urun_adi']}")
        print(
            f"Kategori: {u['kategori']} | Fiyat: {u['fiyat']} TL | Stok: {u['stok']}"
        )
        stok_uyarisi_ver(u["stok"])
        print("-" * 60)


# 7. Urun arama
def urun_ara():
    aranan = input("Aranacak urun: ").strip().lower()
    urunler = verileri_yukle()
    bulunanlar = [
        u
        for u in urunler
        if aranan in u["urun_adi"].lower() or aranan in u["urun_kodu"].lower()
    ]

    if not bulunanlar:
        print("\n[SONUC] Eslesen urun bulunamadi.")
        return

    print(f"\n[SONUC] {len(bulunanlar)} urun bulundu:")
    for u in bulunanlar:
        print(
            f"- [{u['urun_kodu']}] {u['urun_adi']} (Fiyat: {u['fiyat']} TL, Stok: {u['stok']})"
        )


# 8. Stok guncelleme
def stok_guncelle():
    kod = input("Urun kodu: ").strip().upper()
    urunler = verileri_yukle()

    for u in urunler:
        if u["urun_kodu"] == kod:
            try:
                yeni_stok = int(input("Yeni stok miktari: "))
                if yeni_stok < 0:
                    print("[HATA] Stok miktari negatif olamaz.")
                    return
            except ValueError:
                print("[HATA] Gecerli bir tamsayi giriniz.")
                return

            eski_stok = u["stok"]
            u["stok"] = yeni_stok
            verileri_kaydet(urunler)
            print(
                f"[BASARILI] Stok {eski_stok} -> {yeni_stok} olarak guncellendi."
            )
            stok_uyarisi_ver(yeni_stok)
            return

    print("[HATA] Urun bulunamadi.")


# 9. Ana menu dongusu
def main():
    while True:
        print("\n" + "=" * 25 + " E-TICARET YONETIM PANELI " + "=" * 25)
        print("1 - Yeni Urun Ekle")
        print("2 - Urunleri Listele")
        print("3 - Urun Ara")
        print("4 - Stok Guncelle")
        print("5 - Cikis")
        print("=" * 76)

        secim = input("Seciminiz: ").strip()

        if secim == "1":
            yeni_urun_ekle()
        elif secim == "2":
            urunleri_listele()
        elif secim == "3":
            urun_ara()
        elif secim == "4":
            stok_guncelle()
        elif secim == "5":
            print("Cikis yapildi.")
            break
        else:
            print("[HATA] Gecersiz secim! Lutfen 1-5 arasi bir rakam girin.")


if __name__ == "__main__":
    main()