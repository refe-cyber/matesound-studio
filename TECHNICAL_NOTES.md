# 📓 MateSound Studio — Teknik Bellek ve Mimari Özeti (Her Şeyin Kaydı)

Bu belge, **Huawei MateBook X Pro (`MACHD-WXX9`, Realtek ALC256 `0x10ec0256`, Subsystem `0x1e83323f`, Intel Tiger Lake SOF `sof-hda-dsp`)** üzerinde yaptığımız tüm donanım keşiflerini, çözdüğümüz tüm Linux ses/çekirdek sorunlarını, `hda-verb` komutlarını, PipeWire DSP mimarisini ve sistemdeki dosya konumlarını hiçbir detayı unutmamak için kayıt altına alır.

---

## 1. 🔍 Donanım Mimarisi ve Keşfettiğimiz Kök Nedenler

Huawei MateBook X Pro'da fiziksel olarak **4 adet hoparlör** ve Realtek ALC256 çipi içinde **2 ayrı Stereo DAC (Amfi)** bulunur:

| Fiziksel Donanım | HDA Codec Pin (Node) | Bağlı Olduğu DAC | ALSA Mikser Kontrolü | Görevi |
| :--- | :--- | :--- | :--- | :--- |
| **Üst Tiz Hoparlörler (2x Tweeter)** | `Node 0x14` | `DAC 0x02` (`index 0`) | `Speaker Playback Volume` | Klavye üstünden doğrudan yüze bakan tiz/vokal sürücüleri |
| **Alt Bas Hoparlörler (2x Woofer)** | `Node 0x1b` | `DAC 0x03*` (`index 1`) | `Headphone Playback Volume` | Gövde altından masaya vuran güçlü rezonans bas sürücüleri |
| **3.5mm Kulaklık Jakı** | `Node 0x21` | `DAC 0x02` / `0x03` | `Headphone Jack` (`iface=CARD`) | Otomatik algılamalı analog kulaklık çıkışı |
| **4'lü Mikrofon Dizisi (Quad DMIC)** | Intel SOF DSP | `HiFi__Mic1__source` | `PGA2.0 2 Master Capture` | Ekran/kasa üstü 360° dijital mikrofon dizisi |

### Çözdüğümüz 5 Kritik Sorun

#### Sorun 1: Üst Tiz Hoparlörlerin (`Pin 0x14`) Linux'ta Fabrika Çıkışı Kapalı Olması
- **Neden:** BIOS/UEFI varsayılan olarak `Node 0x14` pinini `0x411111f0` (`[N/A] Speaker at Ext Rear`) olarak bıraktığı için Linux çekirdeği bu pini hiç bağlamıyordu.
- **Çözüm:**
  - `/lib/firmware/hda-jack-retask.fw` içinde `0x14 0x90170111` (`[Fixed] Internal Speaker`) olarak tanımlandı.
  - SOF sürücüsü `snd-hda-intel` değil **`snd_soc_hdac_hda`** modülünü kullandığı için `/etc/modprobe.d/hda-jack-retask.conf` içine:
    ```ini
    options snd-hda-intel patch=hda-jack-retask.fw,hda-jack-retask.fw,hda-jack-retask.fw,hda-jack-retask.fw
    options snd_soc_hdac_hda patch=hda-jack-retask.fw,hda-jack-retask.fw,hda-jack-retask.fw,hda-jack-retask.fw
    options snd_hda_intel power_save=0
    ```
    eklendi ve `hda-jack-retask.fw` dosyası **initramfs** (`mkinitcpio` / `initramfs-tools` / `dracut`) içine gömüldü.

#### Sorun 2: Retask Sonrası Basların Kaybolması ve Sesin "Çok Tiz / Patlak" Çıkması (En Kritik Keşif!)
- **Neden:** `hda-jack-retask.fw` açılışta yüklendiğinde Linux çekirdeğinin `snd_hda_codec_alc269` otomatik ayrıştırıcısı, alt bas hoparlörü (`Node 0x1b`) kendi bas amfisi olan **`DAC 0x03*` (`index 1`)** hattından koparıp tiz amfisi olan **`DAC 0x02*` (`index 0`)** hattına bağlıyordu (`Connection: 2 -> 0x02* 0x03`). Üstelik yüzünüze doğrudan bakan üst tiz hoparlörleri (`0x14`) `0 dB` (`0x57` = `87`) tam güçte sürünce tizler basları tamamen eziyor ve patlak ses veriyordu.
- **Çözüm (`enable_tweeters.sh`):**
  1. `hda-verb "$DEV" 0x1b 0x701 0x01` komutuyla **`Node 0x1b` (Alt Bas) zorla `DAC 0x03*` (`Connection Index 1`) hattına geri alındı!**
  2. Alt Bas DAC (`0x03`, ALSA `'Headphone'`) her zaman Üst Tiz DAC (`0x02`, ALSA `'Speaker'`) seviyesinin **`+17` adım (`+12.75 dB`) üzerinde** (tavan `87` = `0x57` = `0.00 dB` tam güç) sürüldü.

#### Sorun 3: USB Dock (Dell D6000) veya USB Hoparlör (Jabra) Takılıyken Pinlerin "PASİF" Görünmesi
- **Neden:** Bilgisayara USB ses cihazları takılıyken açıldığında Linux çekirdeği `card0`'ı Jabra USB'ye, `card1`'i Dell Dock'a, `card2`'yi ise dahili ses kartına (`sofhdadsp`) atıyordu. Sabit `/dev/snd/hwC0D0`, `/proc/asound/card0/codec#0` ve `amixer -c 0` kullanan kodlar `card0`'da Jabra'yı görünce hata veriyordu.
- **Çözüm:**
  - Tüm betikler ve uygulama artık sabit `card0` yerine **`/proc/asound/sofhdadsp`** sembolik bağını ve **`/sys/class/sound/hwC*D0/vendor_id` (`0x10ec0256`)** kimliğini tarayarak dahili ses kartının o anki numarasını (`hwC0D0`, `hwC1D0`, `hwC2D0` vb.) dinamik buluyor.
  - `amixer` çağrılarının tamamı `amixer -c sofhdadsp` olarak çalışıyor.

#### Sorun 4: KDE Ses Çubuğundan Sesi Kısınca `%61`'e Geri Zıplaması
- **Neden:** KDE ses çubuğundaki `500 Series Chipset Family ... Speaker` sürgüsü doğrudan ALSA `'Speaker'` (`DAC 0x02`) kanalını kontrol ediyor. Uygulama her 10 saniyede bir `'Speaker'` kanalına `70` (`-12.75 dB` = KDE'de `%61`) yazdığı için kullanıcı sesi kıstığında çubuk `%61`'e geri zıplıyordu.
- **Çözüm:**
  - `main.py` içindeki `ensure_hardware_unmuted()` artık `'Speaker'` kanalına **asla yazmıyor**, yalnızca kullanıcının ayarladığı `'Speaker'` adımını (`spk_step`) **okuyor** ve Alt Bas amfisini (`'Headphone'` / `DAC 0x03`) `min(87, spk_step + bass_offset)` olarak senkronize ediyor.
  - Böylece ses çubuğu asla `%61`'e zıplamıyor; sesi kıstığınızda veya `%0`'a çektiğinizde hem alt baslar hem üst tizler birlikte kısılıyor ve kapanıyor.

#### Sorun 5: Ekran Kapanıp Açıldığında (DPMS Uyku) Sesin Otomatik HDMI Monitöre Kaçması
- **Neden:** Harici monitör bağlıyken ekran uykuya dalıp uyandığında HDMI ses portu kopup tekrar `available` durumuna geçiyor ve "yeni takılan cihaz" gibi algılanıp sesi PC hoparlöründen çalıyordu.
- **Çözüm:**
  - `DeviceWatcher.probe()` içindeki otomatik geçiş (hotplug) listesinden **HDMI monitörler (`kind == "hdmi"`)** ve **Dock (`dock`)** uyanmaları hariç tutuldu.
  - Kulaklık (3.5mm), Bluetooth veya Jabra/USB kulaklık taktığınızda otomatik geçer; ancak ekran/monitör açılıp kapandığında ses **PC Hoparlörü (MateBook 4'lü Quad)** üzerinde sabit kalır (HDMI sadece sağ tık menüsünden elle seçilirse devreye girer).

---

## 2. ⚡ Donanım `hda-verb` Komutları Sözlüğü

Dahili ses kartını (`$DEV`, örn. `/dev/snd/hwC0D0` veya `/dev/snd/hwC2D0`) doğrudan uyandıran düşük seviye HDA komutları:

```bash
# Üst Tiz Hoparlörler (Node 0x14 -> DAC 0x02)
hda-verb "$DEV" 0x14 0x707 0x40    # Pin Widget Control -> 0x40 (OUT etkin)
hda-verb "$DEV" 0x14 0x70c 0x02    # EAPD/BTL Enable    -> 0x02 (Harici Amfi Açık)
hda-verb "$DEV" 0x14 0x3b0 0x00    # Amp-Out Mute       -> 0x00 (Sessizden çıkar)

# Alt Bas Hoparlörler (Node 0x1b -> DAC 0x03*)
hda-verb "$DEV" 0x1b 0x701 0x01    # Connection Select  -> 0x01 (DAC 0x03* seç! Çok önemli!)
hda-verb "$DEV" 0x1b 0x707 0x40    # Pin Widget Control -> 0x40 (OUT etkin)
hda-verb "$DEV" 0x1b 0x70c 0x02    # EAPD/BTL Enable    -> 0x02 (Harici Amfi Açık)
hda-verb "$DEV" 0x1b 0x3b0 0x00    # Amp-Out Mute       -> 0x00 (Sessizden çıkar)

# DAC Güç ve Kazançları
hda-verb "$DEV" 0x03 0x705 0x00    # DAC 0x03 (Alt Bas) Güç Durumu -> D0 (Tam Aktif)
hda-verb "$DEV" 0x03 0x3b0 0x57    # DAC 0x03 (Alt Bas) Kazanç     -> 0x57 (87 = 0.00 dB)
hda-verb "$DEV" 0x02 0x705 0x00    # DAC 0x02 (Üst Tiz) Güç Durumu -> D0 (Tam Aktif)
hda-verb "$DEV" 0x02 0x3b0 0x46    # DAC 0x02 (Üst Tiz) Kazanç     -> 0x46 (70 = -12.75 dB)
```

### Donanım Durumunu Doğrulama Komutu
Terminalde her zaman şu komutla `Node 0x14` ve `Node 0x1b` durumunu kontrol edebilirsiniz:
```bash
grep -A 22 -E "Node 0x(02|03|14|1b) " /proc/asound/sofhdadsp/codec#0
```
- `Node 0x14` altında: `Pin-ctls: 0x40: OUT`, `EAPD 0x2: EAPD`, `Connection: 1 -> 0x02` olmalı.
- `Node 0x1b` altında: `Pin-ctls: 0x40: OUT`, `EAPD 0x2: EAPD`, `Connection: 2 -> 0x02 0x03*` (**`0x03*` yıldızlı**) olmalı.

---

## 3. 🎛️ PipeWire Gerçek Zamanlı DSP Grafiği (`matebook-nahimic.conf`)

PipeWire `libpipewire-module-filter-chain` modülü üzerinde çalışan `matebook_nahimic_sink` (`MateSound Studio (Huawei Quad-Audio)`) düğümleri:

- **Bas Yolu (`in_L/R` ➔ `woofer_lp_L/R` ➔ `bass_boost_L/R` ➔ `mix_L/R:In 1`):**
  - `woofer_lp_L/R` (`bq_lowpass`): `Freq = 1800.0 Hz`, `Q = 0.6`
  - `bass_boost_L/R` (`bq_lowshelf`): `Freq = 160.0 Hz`, `Gain = +5.5 dB`
- **Tiz ve Vokal Yolu (`in_L/R` ➔ `tweeter_hp_L/R` ➔ `voice_clarity_L/R` ➔ `treble_sparkle_L/R` ➔ `mix_L/R:In 2`):**
  - `tweeter_hp_L/R` (`bq_highpass`): `Freq = 1800.0 Hz`, `Q = 0.6`
  - `voice_clarity_L/R` (`bq_peaking`): `Freq = 2500.0 Hz`, `Gain = +1.5 dB`, `Q = 1.0`
  - `treble_sparkle_L/R` (`bq_highshelf`): `Freq = 11000.0 Hz`, `Gain = +1.5 dB`
- **Faz ve Karıştırıcı (`mix_L/R`):**
  - `Gain 1 = 1.25` (Bas yolu kazancı)
  - `Gain 2 = -0.55` (Tiz yolu ters fazlı kazancı — üst ve alt hoparlörlerin akustik faz iptalini önler ve sesi toklaştırır)
- **Canlı Güncelleme:** PipeWire asla yeniden başlatılmaz (`systemctl --user restart pipewire` yapılmaz); tüm kaydırıcılar `pw-cli s <node_id> Props "{ params = [ ... ] }"` ile **0 ms kesintiyle** canlı enjekte edilir.

---

## 4. 📂 Sistemdeki Kurulu Dosya Konumları

`sudo ./install.sh` çalıştırıldığında sistemde kurulan tüm dosyalar:

| Dosya Yolu | Açıklama |
| :--- | :--- |
| `/opt/nahimic/main.py` | MateSound Studio PyQt6 ana uygulaması (Root sahipli, güvenli) |
| `/opt/nahimic/nahimic-logo.png` | Neon "M" uygulama ve sistem tepsisi ikonu |
| `/usr/local/bin/matesound` | Uygulama başlatıcı komut (`nahimic` sembolik bağı da buna bağlıdır) |
| `/usr/local/libexec/nahimic/enable_tweeters.sh` | Donanım pinlerini ve DAC yönlendirmesini uyandıran root betiği |
| `/etc/systemd/system/nahimic-pins.service` | Bilgisayar açılışında (boot) pinleri şifresiz otomatik uyandıran servis |
| `/usr/lib/systemd/system-sleep/nahimic-pins` | Uyku modundan (suspend/resume) uyanınca pinleri otomatik uyandıran kanca |
| `/etc/polkit-1/rules.d/49-nahimic.rules` | Arayüzden "Pinleri Uyandır" veya Auto-Heal çağrıldığında şifre sormayan Polkit kuralı |
| `/lib/firmware/hda-jack-retask.fw` | ALC256 `Pin 0x14` (`0x90170111`) ve `Pin 0x1b` (`0x90170110`) çekirdek firmware yaması |
| `/etc/modprobe.d/hda-jack-retask.conf` | `snd_soc_hdac_hda` ve `snd-hda-intel` modül parametreleri |
| `~/.config/pipewire/pipewire.conf.d/matebook-nahimic.conf` | PipeWire gerçek zamanlı Crossover & EQ DSP modülü |
| `~/.config/pipewire/pipewire.conf.d/matebook-mic-rnnoise.conf` | PipeWire RNNoise yapay zeka mikrofon gürültü bastırma modülü |
| `~/.config/autostart/matesound.desktop` | Oturum açıldığında sistem tepsisinde (`matesound --tray`) otomatik başlatıcı |
| `~/.config/matesound/settings.json` | Kullanıcının dil tercihi (`"tr"` veya `"en"`) |

---

## 5. 🛠️ Günlük Kullanım ve Bakım Komutları

- **Arayüzü açmak için:**
  ```bash
  matesound
  ```
- **Kaynak kodda yapılan bir değişikliği sisteme canlı uygulamak için (Reboot gerekmez):**
  ```bash
  sudo /home/refe/İndirilenler/Nahimic/install.sh
  ```
- **Donanım pinlerini terminalden elle uyandırmak için:**
  ```bash
  sudo /usr/local/libexec/nahimic/enable_tweeters.sh
  ```
- **Tamamen kaldırmak için:**
  ```bash
  sudo /home/refe/İndirilenler/Nahimic/install.sh --uninstall
  ```
- **GitHub Deposu:** https://github.com/refe-cyber/matesound-studio
