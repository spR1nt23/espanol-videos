# Español en 7 días – Günlük görev (adım adım)

Bu dosya, her gün çalışan zamanlanmış görevin talimatıdır. Görev yeni bir oturumda başlar, önceki sohbeti bilmez.
Kullanıcıyla Türkçe konuş. Kullanıcı genelde ortada olmaz: soru sorma, makul kararı ver, sonunda kısa özet gönder.

## Yetkiler
- Serbest: video üretimi, yükleme, başlık, açıklama, hashtag, yayın saati.
- YAPMA (kullanıcıya bırak): video silme/gizleme, kanal adı/logo/ayar, para kazanma, yorumlara cevap.

## 0. Kurulum (çalışma alanı boşsa)
- Repo: `spR1nt23/espanol-videos` → add_repo (access: push) → `git clone --depth 1` → /home/claude/espanol-videos
- `pip install --break-system-packages piper-tts sherpa-onnx soundfile numpy pillow openpyxl`
- Modeller (huggingface kapalı olabilir, GitHub'dan al) → /home/claude/models altına `tar xjf`:
  - https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-es_MX-claude-high.tar.bz2
  - https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-tr_TR-fahrettin-medium.tar.bz2
  - https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-small.tar.bz2
- Yazı tipleri → /home/claude/assets: raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-{Bold,ExtraBold,SemiBold}.ttf
  ve ofl/inter/Inter%5Bopsz,wght%5D.ttf (Inter.ttf adıyla kaydet). Emoji: /usr/share/fonts/truetype/noto/NotoColorEmoji.ttf
- `cp uretim/render.py uretim/tts.py /home/claude/`

## 1. Cümleleri seç (5 adet)
- Duygusal / ilişki temalı, kısa Türkçe cümleler. `kullanilan_cumleler.txt` içindekileri TEKRAR KULLANMA.
- İspanyolca: doğal, Latin Amerika İspanyolcası. Okunuş Türkçe harflerle, vurgulu hece BÜYÜK: örn. `te ne-se-Sİ-to`.
- Ses motoru tek başına "Te amo", "Te extraño", "¿Qué haces?" okuyamıyor. Çok kısa ifadeleri uzat ("Yo te amo").
- Her cümleyi tts.py `say()` ile üret, `transcribe(...,'es')` ile kontrol et. Yanlış okunanı değiştir.
- `uretim/gun_<YYYY-MM-DD>.json` yaz (örnek: uretim/gun_2026-11-09.json). Alanlar: slug (01_.. 05_), tr, es, es_say, okunus, emoji, hue, konu (cümlenin boşluksuz küçük harfli yazılışı), saat.

## 2. Üret ve kontrol et
- `python3 render.py uretim/gun_<tarih>.json out_<tarih>` (1080x1920, 30fps, 16-20 sn, -14 LUFS)
- Her videodan 3 kare al (ffmpeg -ss 1.8 / 8.5 / son), bir kontrol sayfası yap ve BAK: yazı taşması, üst üste binme olmasın.

## 3. GitHub'a koy
- `videos/<YYYY-MM-DD>/TR_<GGAyy>_<slug>.mp4` (örn. TR_10Kas_01_...). `kullanilan_cumleler.txt` sonuna yeni cümleleri ekle.
- commit (sonuna session satırları) → `git push origin HEAD:main`

## 4. YouTube'a yükle (uygulamadaki tarayıcı: mcp__remote-devices__Claude_Browser__*)
- Önce built-in-browser skill'ini yükle. Sekme genişliğini `resize_window 1280x900` yap (bitince preset desktop).
- KANAL KONTROLÜ: https://studio.youtube.com/channel/UCBz_EV9wokexxWVS-9Zyudw/videos/short açılmalı.
  403 "Oops" çıkarsa başka hesaptasın: studio.youtube.com → `#avatar-btn` tıkla → "Hesap değiştir/Switch account" →
  `ytd-account-item-renderer` içinden "Español en 7 días" → tıkla. Tekrar kontrol et.
- HER VİDEO İÇİN TEK TEK (asla hepsini birden verme, günlük sınıra sayılıyor):
  1. https://studio.youtube.com/channel/UCBz_EV9wokexxWVS-9Zyudw/videos/upload?d=ud aç, 4 sn bekle.
  2. JS: raw.githubusercontent.com/spR1nt23/espanol-videos/main/videos/<tarih>/<dosya> → fetch → blob →
     `new File([b],dosya,{type:'video/mp4'})` → DataTransfer → `input[type=file]`.files → change olayı. 6 sn bekle, sayfadan AYRILMA.
  3. Başlık: `ytcp-uploads-dialog #title-textarea #textbox` focus + execCommand('selectAll') → computer type.
     `“<Türkçe cümle>” İspanyolca nasıl denir? #ispanyolca #shorts ` (sonda boşluk)
  4. Açıklama (`#description-textarea #textbox`, aynı yöntem):
     `“<cümle>” İspanyolca nasıl denir? <İspanyolca>. (<okunuş>) Bildiysen yorumlara yaz! Her gün yeni bir İspanyolca cümle için takip et. #ispanyolca #ispanyolcaöğren #ispanyolcaöğreniyorum #ispanyolcakelimeler #<konu> #yabancıdil #dilöğrenme #dilöğreniyorum #español #aprenderespañol #learnspanish #keşfet #shorts `
     (sondaki boşluk "#shortstory" otomatik tamamlamasını engeller). ESCAPE'E BASMA, pencereyi kapatır.
  5. `tp-yt-paper-radio-button[name=VIDEO_MADE_FOR_KIDS_NOT_MFK]` JS click → aria-checked "true" olmalı.
  6. `#next-button` x3 (1.5 sn arayla) → `#second-container-expand-button` → `#datepicker-trigger` →
     açılan input focus+select → type "10 Kas 2026" + Enter → `#time-of-day-container input` focus+select → "18:00" + Enter.
     Saat dilimi GMT+3. Saatler: 18:00, 19:30, 21:00, 22:00, 23:00. Geçmiş saate planlama: yerine en yakın ileri saatleri kullan.
  7. Tarih/saat doğrulanınca `#done-button` ("Planla"). `ytcp-video-share-dialog` "Video planlandı … <tarih saat>" yazmalı → "Kapat".
  8. "Günlük yükleme sınırına ulaşıldı" çıkarsa DUR: videoyu taslakta bırak, kullanıcıya bildir (kanalı telefonla doğrulaması gerekebilir).
- Sonunda Shorts listesini oku: 5 videonun "Planlandı" ve açıklamalarının dolu olduğunu kontrol et.

## 5. Kayıt
- Kullanıcının bilgisayarındaki `C:\Users\user\OneDrive\Desktop\ispanyolca\Espanol_en_7_dias_Yayin_Takvimi.xlsx`:
  device_stage_files → openpyxl ile yeni 5 satır (tarih, saat, cümleler, dosya, başlık, açıklama, "Planlandı", link) +
  son günlerin izlenme sayıları (Shorts listesinden) → device_commit_files (expectedMtimeMs ile).
- `DEVAM_NOTU.txt` içindeki "BEKLEYEN İŞ" kısmını güncelle.
- Repoya `gun_<tarih>.json` ve güncel `kullanilan_cumleler.txt` push'la.

## 6. Özet
- Kullanıcıya kısa Türkçe özet: 5 cümle + saatler + varsa sorun. En iyi giden videoyu ve izlenme eğilimini 1 cümleyle söyle.

## Notlar
- Başlık için focus+selectAll bazen tüm sayfayı seçer (diyalog tam yüklenmeden). Yazmadan önce `window.getSelection().toString()` kontrol et; yanlışsa başlık kutusuna triple_click yapıp tekrar dene. Açıklama boşsa activeElement'in açıklama kutusu olduğunu doğrula.
- Önceki bir çalışma yarım kalmışsa (videos/<tarih> var ama Studio'da eksik), sadece eksikleri json'daki saatlerle yükle; 'TR 10Kas ..' gibi dosya adlı başlık görürsen o yarım kalmış bir yüklemedir, kullanıcıya bildir.
- Aynı tarayıcıyı başka sohbetler de kullanıyor ve kanal değiştirebiliyor. Her yüklemeden önce kanal kimliğini kontrol et.
- 9 Kas itibarıyla izlenmeler: "Seni çok özledim" 103, "Adın ne?" 23, diğerleri 0-8. Duygusal tema henüz net kazanmadı; çeşitlilik dene (günlük ifadeler + duygusal karışık olabilir).
