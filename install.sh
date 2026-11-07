#!/usr/bin/env bash
# Nahimic Audio Suite (Huawei MateBook X Pro) - güvenli kurulum
# Kullanım: ./install.sh        (kurar)   |   ./install.sh --uninstall
set -euo pipefail

# Normal kullanıcı: sudo kullan | pkexec (root): doğrudan çalış, kullanıcı dosyalarını kullanıcı olarak yaz
if [ "$(id -u)" = 0 ]; then
    SUDO=""
    REAL_USER="${SUDO_USER:-$(id -nu "${PKEXEC_UID:-1000}")}"
    REAL_HOME="$(getent passwd "$REAL_USER" | cut -d: -f6)"
    RUN_AS="runuser -u $REAL_USER --"
else
    SUDO="sudo"
    REAL_USER="$USER"
    REAL_HOME="$HOME"
    RUN_AS=""
fi

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP=/opt/nahimic
HELPER_DIR=/usr/local/libexec/nahimic

if [ "${1:-}" = "--uninstall" ]; then
    $SUDO systemctl disable --now nahimic-pins.service 2>/dev/null || true
    $SUDO rm -rf "$APP" "$HELPER_DIR" /usr/share/polkit-1/actions/org.nahimic.reinit.policy /etc/polkit-1/rules.d/49-nahimic.rules
    $SUDO rm -f /etc/systemd/system/nahimic-pins.service /usr/lib/systemd/system-sleep/nahimic-pins
    $SUDO rm -f /usr/share/applications/matebook-nahimic.desktop /usr/share/applications/matesound.desktop /usr/local/bin/nahimic /usr/local/bin/matesound
    echo "Kaldırıldı / Uninstalled."; exit 0
fi

# Donanım kontrolü: yanlış makinede kurulmasın
PROD="$(cat /sys/class/dmi/id/product_name 2>/dev/null || true)"
case "$PROD" in
    *MACH*|*MateBook*|*MRC*|*MRG*|*HUAWEI*) ;;
    *) echo "Uyarı / Warning: Device '$PROD' is not a recognized Huawei MateBook. Press ENTER to continue or Ctrl+C to abort"; read -r _ ;;
esac

# Tüm Linux dağıtımları için otomatik bağımlılık kurulumu (Arch, Ubuntu/Debian, Fedora, openSUSE)
install_deps() {
    if command -v pacman >/dev/null 2>&1; then
        $SUDO pacman -S --needed --noconfirm alsa-tools alsa-utils python-pyqt6
    elif command -v apt-get >/dev/null 2>&1; then
        $SUDO apt-get update && $SUDO apt-get install -y alsa-tools alsa-utils python3-pyqt6 libqt6gui6
    elif command -v dnf >/dev/null 2>&1; then
        $SUDO dnf install -y alsa-tools alsa-utils python3-pyqt6
    elif command -v zypper >/dev/null 2>&1; then
        $SUDO zypper install -y alsa-tools alsa-utils python3-qt6
    else
        echo "Lütfen 'alsa-tools' (hda-verb) ve 'python3-pyqt6' paketlerini kurun / Please install alsa-tools and python3-pyqt6."
        exit 1
    fi
}

if ! command -v hda-verb >/dev/null 2>&1 || ! python3 -c "import PyQt6" 2>/dev/null; then
    echo "[bağımlılıklar / dependencies] Eksik paketler kuruluyor..."
    install_deps
fi

# 1) Uygulama: root sahipli, kullanıcı tarafından değiştirilemez
$SUDO install -d -m 755 "$APP" "$HELPER_DIR"
$SUDO install -m 644 "$SRC/main.py" "$APP/main.py"
$SUDO install -m 644 "$SRC/nahimic-logo.png" "$APP/nahimic-logo.png"
$SUDO sed -i "s|^APP_DIR = .*|APP_DIR = Path(\"$APP\")|" "$APP/main.py"
echo "[güncellendi] Uygulama dosyaları ($APP/main.py)"

# 2) Ayrıcalıklı yardımcı betik (pkexec ile çalışır): root:root 755
$SUDO install -o root -g root -m 755 "$SRC/enable_tweeters.sh" "$HELPER_DIR/enable_tweeters.sh"
echo "[güncellendi] Donanım betiği ($HELPER_DIR/enable_tweeters.sh)"

# 3) Başlatıcı ve masaüstü girişi (MateSound Studio + geriye dönük nahimic kısayolu)
printf '#!/bin/sh\nexec /usr/bin/python3 -B %s/main.py "$@"\n' "$APP" | $SUDO tee /usr/local/bin/matesound >/dev/null
$SUDO chmod 755 /usr/local/bin/matesound
$SUDO ln -sf /usr/local/bin/matesound /usr/local/bin/nahimic
$SUDO rm -f /usr/share/applications/matebook-nahimic.desktop
$SUDO tee /usr/share/applications/matesound.desktop >/dev/null <<EOF
[Desktop Entry]
Name=MateSound Studio
Comment=Huawei MateBook X Pro Quad-Speaker DSP & Ses Yöneticisi
Exec=/usr/local/bin/matesound
Icon=$APP/nahimic-logo.png
Terminal=false
Type=Application
Categories=AudioVideo;Audio;Settings;
EOF

# 4) Polkit kuralı: Şifresiz arka plan ve canlı donanım pin canlandırması
$SUDO install -d -m 755 /etc/polkit-1/rules.d
$SUDO tee /etc/polkit-1/rules.d/49-nahimic.rules >/dev/null <<EOF
polkit.addRule(function(action, subject) {
    if (action.id == "org.nahimic.reinit" ||
        (action.id == "org.freedesktop.policykit.exec" &&
         action.lookup("program") == "$HELPER_DIR/enable_tweeters.sh")) {
        return polkit.Result.YES;
    }
});
EOF

$SUDO tee /usr/share/polkit-1/actions/org.nahimic.reinit.policy >/dev/null <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE policyconfig PUBLIC "-//freedesktop//DTD PolicyKit Policy Configuration 1.0//EN"
 "http://www.freedesktop.org/standards/PolicyKit/1.0/policyconfig.dtd">
<policyconfig>
  <action id="org.nahimic.reinit">
    <description>Nahimic hoparlör pinlerini uyandır</description>
    <message>Hoparlör donanım pinlerini yeniden başlatmak için kimlik doğrulama gerekli</message>
    <defaults><allow_any>yes</allow_any><allow_inactive>yes</allow_inactive><allow_active>yes</allow_active></defaults>
    <annotate key="org.freedesktop.policykit.exec.path">$HELPER_DIR/enable_tweeters.sh</annotate>
  </action>
</policyconfig>
EOF

# 4b) Açılışta ve uykudan dönüşte pinleri otomatik uyandıran sistem servisi
$SUDO tee /etc/systemd/system/nahimic-pins.service >/dev/null <<EOF
[Unit]
Description=Nahimic - MateBook X Pro hoparlör pinlerini uyandır
After=sound.target

[Service]
Type=oneshot
ExecStart=$HELPER_DIR/enable_tweeters.sh
TimeoutStartSec=90

[Install]
WantedBy=multi-user.target
EOF
$SUDO systemctl daemon-reload || true
$SUDO systemctl enable nahimic-pins.service || true

# Uykudan dönüşte (resume) pinleri tekrar uyandır
$SUDO install -d -m 755 /usr/lib/systemd/system-sleep
$SUDO tee /usr/lib/systemd/system-sleep/nahimic-pins >/dev/null <<EOF
#!/bin/sh
[ "\$1" = post ] && $HELPER_DIR/enable_tweeters.sh >/dev/null 2>&1 &
exit 0
EOF
$SUDO chmod 755 /usr/lib/systemd/system-sleep/nahimic-pins

# 5) Kullanıcı otomatik başlatma (tepsiye küçük başlar)
$RUN_AS mkdir -p "$REAL_HOME/.config/autostart"
$RUN_AS rm -f "$REAL_HOME/.config/autostart/matebook-nahimic.desktop"
$RUN_AS tee "$REAL_HOME/.config/autostart/matesound.desktop" >/dev/null <<EOF
[Desktop Entry]
Name=MateSound Studio
Exec=/usr/local/bin/matesound --tray
Icon=$APP/nahimic-logo.png
Terminal=false
Type=Application
EOF

# 6) Pin yapılandırması (Arch mkinitcpio / Ubuntu initramfs-tools / Fedora dracut uyumlu)
FW=/lib/firmware/hda-jack-retask.fw
MODPROBE_CONF=/etc/modprobe.d/hda-jack-retask.conf
MKINIT_CONF=/etc/mkinitcpio.conf

INITRAMFS_READY=0
if grep -q "hda-jack-retask.fw" "$MKINIT_CONF" 2>/dev/null || \
   [ -x /etc/initramfs-tools/hooks/matesound-retask ] || \
   [ -f /etc/dracut.conf.d/99-matesound.conf ]; then
    INITRAMFS_READY=1
fi

if [ -f "$FW" ] && grep -q "^0x14 0x90170111" "$FW" && \
   [ -f "$MODPROBE_CONF" ] && grep -q "snd_soc_hdac_hda" "$MODPROBE_CONF" && \
   [ "$INITRAMFS_READY" = 1 ]; then
    echo "[atlandı] Pin ve initramfs yapılandırması zaten kurulu."
else
    echo "[kuruluyor] Pin, modprobe ve initramfs yapılandırması uygulanıyor..."
    $SUDO bash "$SRC/apply_pin_fix.sh"
fi

# 7) PipeWire DSP ve mikrofon yapılandırması (her zaman güncel tut)
PW="$REAL_HOME/.config/pipewire/pipewire.conf.d"
$RUN_AS mkdir -p "$PW"
for f in matebook-nahimic.conf matebook-mic-rnnoise.conf; do
    $RUN_AS install -m 644 "$SRC/config/$f" "$PW/$f"
    echo "[güncellendi] $PW/$f"
done

# 8) Donanım pinlerini ve DAC kazançlarını (0dB) anında canlı uygula (Reboot gerekmez!)
echo "[uygulanıyor] Hoparlör pinleri ve DAC kazançları (0dB) canlı etkinleştiriliyor..."
$SUDO "$HELPER_DIR/enable_tweeters.sh" || true

# 9) Çalışan eski arayüzü kapat, PipeWire DSP'yi yenile ve MateSound Studio'yu tepside başlat
pkill -f "python3.*/main.py" 2>/dev/null || true
REAL_UID="$(id -u "$REAL_USER" 2>/dev/null || echo 1000)"
if [ -d "/run/user/$REAL_UID" ]; then
    $RUN_AS env XDG_RUNTIME_DIR="/run/user/$REAL_UID" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$REAL_UID/bus" DISPLAY="${DISPLAY:-:0}" WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}" \
        bash -c '
            NODE_ID=$(pw-cli list-objects Node 2>/dev/null | awk "/id / {id=\$2} /matebook_nahimic_sink/ {gsub(\",\",\"\",id); print id; exit}")
            if [ -n "$NODE_ID" ]; then
                pw-cli s "$NODE_ID" Props "{ params = [ \"woofer_lp_L:Freq\" 1800.0 \"woofer_lp_R:Freq\" 1800.0 \"woofer_lp_L:Q\" 0.6 \"woofer_lp_R:Q\" 0.6 \"tweeter_hp_L:Freq\" 1800.0 \"tweeter_hp_R:Freq\" 1800.0 \"tweeter_hp_L:Q\" 0.6 \"tweeter_hp_R:Q\" 0.6 \"bass_boost_L:Freq\" 160.0 \"bass_boost_R:Freq\" 160.0 \"bass_boost_L:Gain\" 5.5 \"bass_boost_R:Gain\" 5.5 \"voice_clarity_L:Freq\" 2500.0 \"voice_clarity_R:Freq\" 2500.0 \"voice_clarity_L:Gain\" 1.5 \"voice_clarity_R:Gain\" 1.5 \"treble_sparkle_L:Freq\" 11000.0 \"treble_sparkle_R:Freq\" 11000.0 \"treble_sparkle_L:Gain\" 1.5 \"treble_sparkle_R:Gain\" 1.5 \"mix_L:Gain 1\" 1.25 \"mix_R:Gain 1\" 1.25 \"mix_L:Gain 2\" -0.55 \"mix_R:Gain 2\" -0.55 ] }" >/dev/null 2>&1 || true
                echo "[canlı] MateSound Studio DSP filtreleri güncellendi (kesintisiz)."
            fi
            nohup /usr/local/bin/matesound --tray >/dev/null 2>&1 &
        ' || true
fi

[ -f /usr/lib/ladspa/librnnoise_ladspa.so ] || \
    echo "Bilgi: RNNoise (yapay zeka mikrofon) için 'noise-suppression-for-voice' paketi (AUR) gerekli. Yoksa bu mod devre dışı kalır."

echo "Kurulum tamam! Arka planda tepsi uygulaması başlatıldı. Pencereyi açmak için: matesound"
