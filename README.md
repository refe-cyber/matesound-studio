# 🎛️ MateSound Studio — Huawei MateBook Quad-Speaker DSP & Output Manager for Linux

<p align="center">
  <img src="matesound-logo.png" width="120" alt="MateSound Studio Logo" />
</p>

**English** | [Türkçe](#-türkçe-dokümantasyon)

**MateSound Studio** is an open-source hardware codec unlocker, real-time PipeWire crossover/DSP equalizer, and smart audio output router built for **Huawei MateBook X Pro** (and Huawei MateBook models using the **Realtek ALC256 (`0x10ec0256`) + Intel SOF (`sof-hda-dsp`)** 4-speaker architecture) across **all Linux distributions**.

---

## 🔍 Why Do Huawei MateBook Speakers Sound Flat or Tinny on Linux?

On Windows, Huawei's audio driver drives two independent stereo amplifier channels inside the Realtek ALC256 codec:
1. **Bottom Woofers (`Pin 0x1b`)** — Downward-firing resonance bass speakers powered by **`DAC 0x03` (`Headphone Playback Volume`)**.
2. **Top Tweeters (`Pin 0x14`)** — Upward-firing keyboard treble speakers powered by **`DAC 0x02` (`Speaker Playback Volume`)**.

On Linux, two hardware bugs occur out of the box:
1. **Top Tweeters (`Pin 0x14`) are disabled** (`Pin Default 0x411111f0`), leaving only 2 of the 4 speakers working.
2. **Even worse:** When users retask `Pin 0x14` (`0x90170111`) using `hda-jack-retask`, the Linux kernel's `snd_hda_codec_realtek` auto-parser **disconnects `Pin 0x1b` (Bottom Woofers) from `DAC 0x03*` and routes both `0x14` and `0x1b` onto `DAC 0x02*`** (`Connection: 2 -> 0x02* 0x03`) at equal `0 dB` gain! Because the upward-firing tweeters point directly at your ears, they overpower the woofers and produce harsh, tinny, or distorted sound.

### ✅ How MateSound Studio Fixes It Permanently
- **Hardware DAC Separation (`enable_tweeters.sh`):**
  - Wakes both `Pin 0x14` and `Pin 0x1b` (`OUT` + `EAPD 0x02` + `Unmute`).
  - Explicitly routes **Bottom Woofers (`Pin 0x1b`) back to `DAC 0x03*`** (`hda-verb <dev> 0x1b 0x701 0x01`).
  - Synchronizes **`DAC 0x03` (Bottom Woofers)** `+17` steps (`+12.75 dB`) hotter than **`DAC 0x02` (Top Tweeters)** while tracking your desktop volume slider smoothly without ever resetting your volume.
  - Dynamically finds the internal `sofhdadsp` (`0x10ec0256`) card even when USB docks (Dell D6000, etc.) or USB headsets (Jabra, etc.) shift ALSA card numbers (`card0` -> `card2`).
- **Zero-Glitch Real-Time PipeWire DSP (`matebook-nahimic.conf`):**
  - Biquad low-pass / high-pass crossover (`1800 Hz`), dynamic bass shelf (`160 Hz`), vocal presence peaking (`2500 Hz`), and treble air shelf (`11000 Hz`) updated live via `pw-cli` with **0 ms audio interruption**.
- **Auto-Detecting Output Router & System Tray Menu:**
  - Automatically detects newly plugged USB headsets, Bluetooth headphones, 3.5mm jacks, docks, and HDMI monitors.
  - Lets you switch your active output target with a single click from the **System Tray right-click menu** or the **Dashboard**.
- **Bilingual UI (`🌐 EN / TR`):**
  - Instant live switching between **English** and **Turkish** from the header bar or tray menu.

---

## 🐧 Supported Linux Distributions

`install.sh` and `apply_pin_fix.sh` automatically detect your package manager and initramfs system:
- **Arch Linux / CachyOS / Manjaro / EndeavourOS** (`pacman` + `mkinitcpio`)
- **Ubuntu / Debian / Linux Mint / Pop!_OS / Zorin OS** (`apt` + `initramfs-tools`)
- **Fedora / Nobara / Bazzite / RHEL** (`dnf` + `dracut`)
- **openSUSE Tumbleweed / Leap** (`zypper` + `dracut`)

---

## 🚀 One-Command Installation

```bash
git clone https://github.com/refe-cyber/matesound-studio.git
cd matesound-studio
sudo ./install.sh
```

- Starts automatically in the system tray on login (`matesound --tray`).
- Open the control panel anytime by running:
  ```bash
  matesound
  ```

### Uninstall
```bash
sudo ./install.sh --uninstall
```

---

## 🇹🇷 Türkçe Dokümantasyon

**MateSound Studio**, **Huawei MateBook X Pro** (ve Realtek **ALC256 `0x10ec0256` + Intel SOF** dörtlü hoparlör mimarisini kullanan MateBook modelleri) için geliştirilmiş açık kaynaklı donanım pin uyandırıcı, sıfır kesintili gerçek zamanlı PipeWire DSP ekolayzer ve otomatik ses çıkış yöneticisidir.

### ✨ Başlıca Özellikler
1. **Gerçek 4'lü Hoparlör & DAC Ayrıştırması (`0x14` Tiz + `0x1b` Bas):**
   - Çekirdek retask sonrasında `Pin 0x1b` (Alt Bas) hoparlörlerin yanlışlıkla `0x02*` (Tiz DAC) hattına düşmesini `hda-verb <dev> 0x1b 0x701 0x01` komutuyla düzeltir ve alt basları kendi özel **`DAC 0x03*`** amfisine bağlar.
   - KDE / GNOME ses çubuğunuzla tam uyumlu çalışır; sesi kıstığınızda veya açtığınızda `%61`'e geri zıplamaz, alt bas ve üst tiz amfilerini birlikte dengeli şekilde kısar ve açar.
   - Bilgisayarınıza USB Dock veya Jabra gibi USB ses kartları takılı olduğunda kart numarası değişse bile (`card0` yerine `card2`) `sofhdadsp` üzerinden dahili ses çipini otomatik bulur.
2. **Otomatik Aygıt Algılama & Sağ Tık Tepsi Menüsü:**
   - Ne takarsanız (USB kulaklık, Jabra, Bluetooth, 3.5mm kulaklık, HDMI monitör) otomatik algılar.
   - Sistem tepsisindeki (saat yanındaki) **MateSound Studio** ikonuna sağ tıklayarak veya uygulama penceresinin en üstünden sesin hangi cihazdan çıkacağını tek tıkla seçebilirsiniz.
3. **Canlı Dil Seçeneği (`🌐 EN / TR`):**
   - Sağ üstteki **`🌐 TR / EN`** butonundan veya sağ tık tepsi menüsünden arayüzü anında İngilizce veya Türkçe yapabilirsiniz.
4. **Tüm Linux Dağıtımlarıyla Uyumlu:**
   - Arch/CachyOS/Manjaro (`mkinitcpio`), Ubuntu/Debian/Mint/Pop!_OS (`initramfs-tools`), Fedora/Nobara (`dracut`) ve openSUSE (`dracut`) dağıtımlarını otomatik tanır ve kurar.

### 🚀 Kurulum
```bash
git clone https://github.com/refe-cyber/matesound-studio.git
cd matesound-studio
sudo ./install.sh
```

Uygulama penceresini açmak için terminale **`matesound`** yazabilir veya uygulama menüsünden **MateSound Studio**'yu başlatabilirsiniz.

---

## 📄 License
Released under the [MIT License](LICENSE).
