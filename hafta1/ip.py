import os
from google import genai
from google.genai import errors

def e_ticaret_api_simulasyonu(urun_talebi):
  os.system("clear")

  print("=" * 70)
  print("B2C E-TİCARET SİSTEMİ: API ENTEGRASYONU VE JSON".center(70, " "))
  print("=" * 70)

  anahtar = "BURAYA_ANAHTAR_GELECEK"

  client = genai.Client(api_key=anahtar)

  sistem_mesaji = """
  Sen kurumsal bir e-ticaret sisteminin arka planında çalışan
  bir veri yapılandırma asistanısın.

  Kullanıcının girdiği ham ürün bilgilerini analiz edip
  veritabanına kaydedilebilmesi için SADECE JSON formatında
  yanıt vermelisin.

  JSON nesnesi kesinlikle şu anahtarları içermelidir:

  {
    "urun_adi": "Kısa ve optimize edilmiş ürün adı",
    "kategori": "Uygun e-ticaret kategorisi",
    "seo_etiketleri": "3 adet virgülle ayrılmış SEO etiketi",
    "satis_aciklamasi": "Müşteriyi ikna edecek profesyonel 2 cümle"
  }

  JSON dışında hiçbir açıklama yazma.
  """

  print(f"\n[AŞAMA 1] KULLANICI TALEBİ ALINDI:\n'{urun_talebi}'")
  print("\n[AŞAMA 2] GEMINI SUNUCUSUNA API İSTEĞİ GÖNDERİLİYOR...")

  print("\n[TEST] API isteği başlatılıyor...", flush=True)

  try:
    interaction = client.interactions.create(
      model="gemini-3.8-flash",
      input=f"""
      {sistem_mesaji}

      Kullanıcının ürün talebi:

      {urun_talebi}
      """
    )

    print("\n[AŞAMA 3] SUNUCUDAN YANIT ALINDI. VERİ ÇÖZÜMLENİYOR...")

    yapilandirilmis_veri = interaction.output_text

    print("-" * 70)
    print("[SONUÇ] VERİTABANINA KAYDEDİLMEYE HAZIR JSON ÇIKTISI:")
    print(yapilandirilmis_veri)
    print("-" * 70)

    dosya_adi = "analiz_sonucu.txt"

    with open(dosya_adi, "w", encoding="utf-8") as dosya:
      dosya.write("=" * 70 + "\n")
      dosya.write("B2C E-TİCARET SİSTEMİ - GEMINI ANALİZ RAPORU\n")
      dosya.write("=" * 70 + "\n\n")

      dosya.write("[KULLANICI TALEBİ]\n")
      dosya.write(urun_talebi.strip() + "\n\n")

      dosya.write("[GEMINI JSON ÇIKTISI]\n")
      dosya.write(yapilandirilmis_veri)

    print(f"\n[BAŞARILI] Sonuç '{dosya_adi}' dosyasına kaydedildi.")

  except errors.APIError as e:
    print("\n[API HATASI]")
    print(f"Açıklama: {e}")

  except Exception as e:
    print(f"\n[SİSTEM HATASI] Beklenmeyen bir istisna oluştu: {e}")

ornek_talep = """
Mavi renkli, su geçirmez, 50 litre kapasiteli kamp çantamızı
sisteme ekleyelim, fiyatı girmene gerek yok.
"""

e_ticaret_api_simulasyonu(ornek_talep)
