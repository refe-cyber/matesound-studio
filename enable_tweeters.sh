#!/usr/bin/env bash
set -euo pipefail
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Dahili ses kartını (sofhdadsp / ALC256) USB ses kartlarından (Jabra, Dock vb.) bağımsız olarak bul
# Açılışta ses kartı geç gelebilir: en fazla 40 sn bekle
DEV=""
CARD="sofhdadsp"
for _ in $(seq 1 80); do
    if [ -L /proc/asound/sofhdadsp ]; then
        CARD_DIR="$(readlink /proc/asound/sofhdadsp)"
        CARD_NUM="${CARD_DIR#card}"
        if [ -e "/dev/snd/hwC${CARD_NUM}D0" ]; then
            DEV="/dev/snd/hwC${CARD_NUM}D0"
            CARD="$CARD_NUM"
            break
        fi
    fi
    for hw in /sys/class/sound/hwC*D0; do
        if [ -f "$hw/vendor_id" ] && grep -qi "0x10ec0256" "$hw/vendor_id" 2>/dev/null; then
            HW_NAME="$(basename "$hw")"
            CARD_NUM="${HW_NAME#hwC}"
            CARD_NUM="${CARD_NUM%D0}"
            if [ -e "/dev/snd/$HW_NAME" ]; then
                DEV="/dev/snd/$HW_NAME"
                CARD="$CARD_NUM"
                break 2
            fi
        fi
    done
    sleep 0.5
done

if [ -z "$DEV" ] || [ ! -e "$DEV" ]; then
    echo "Hata: Realtek ALC256 (sofhdadsp) ses aygıtı bulunamadı!"
    exit 1
fi

echo "=== Huawei MateBook X Pro Quad-Speaker (0x14 + 0x1b) Aktifleştirici ($DEV / card$CARD) ==="

# 1. PCI Ses Donanımının uykuya (autosuspend) dalıp pinleri sıfırlamasını engelle (tüm Intel nesilleri için dinamik)
for pci_dev in /sys/bus/pci/devices/0000:00:1f.3 "$(readlink -f "/sys/class/sound/hwC${CARD}D0/device/.." 2>/dev/null || true)"; do
    if [ -n "$pci_dev" ] && [ -d "$pci_dev/power" ]; then
        echo on > "$pci_dev/power/control" 2>/dev/null || true
        echo 0 > "$pci_dev/power/autosuspend_delay_ms" 2>/dev/null || true
    fi
done
echo 0 > /sys/module/snd_hda_intel/parameters/power_save 2>/dev/null || true
echo 0 > /sys/module/snd_soc_sof_hda_dsp/parameters/power_save 2>/dev/null || true

# 2. Mevcut kullanıcı ses seviyesini (Speaker) oku; 0 ise varsayılan 70 (%61) kullan
# Böylece kullanıcının KDE ses çubuğundan ayarladığı ses seviyesi asla sıfırlanmaz!
SPK_STEP="$(amixer -c "$CARD" sget 'Speaker' 2>/dev/null | awk '/Front Left: Playback/ {print $4; exit}')"
if [ -z "${SPK_STEP:-}" ] || [ "$SPK_STEP" -le 0 ] 2>/dev/null; then
    SPK_STEP=70
fi
WOOFER_STEP=$(( SPK_STEP + 17 ))
if [ "$WOOFER_STEP" -gt 87 ]; then
    WOOFER_STEP=87
fi
SPK_HEX="$(printf "0x%02x" "$SPK_STEP")"
WOOFER_HEX="$(printf "0x%02x" "$WOOFER_STEP")"

echo "1. Mikser kanalları açılıyor (card $CARD, Tiz=$SPK_STEP, Bas=$WOOFER_STEP)..."
amixer -c "$CARD" set 'Master' 87 unmute 2>/dev/null || true
amixer -c "$CARD" set 'Speaker' "$SPK_STEP" unmute 2>/dev/null || true
amixer -c "$CARD" set 'Bass Speaker' unmute 2>/dev/null || true
amixer -c "$CARD" set 'Headphone' "$WOOFER_STEP" unmute 2>/dev/null || true

# 3. Pin 0x14 (Üst Tiz) -> DAC 0x02 ve Pin 0x1b (Alt Bas) -> DAC 0x03 bağlantısını kur
# ÇOK ÖNEMLİ: Kernel retask sonrası 0x1b'yi 0x02'ye (Tiz DAC'ına) bağlar ve baslar kaybolur!
# 0x1b (Alt Bas) mutlaka 0x03 (Index 1 = Bas DAC'ı) üzerinde çalışmalıdır:
echo "2. Pin 0x14 (Tiz -> DAC 0x02) ve Pin 0x1b (Bas -> DAC 0x03) ayrıştırılıyor..."
hda-verb "$DEV" 0x14 0x707 0x40    # Pin 0x14 -> OUT
hda-verb "$DEV" 0x14 0x70c 0x02    # Pin 0x14 -> EAPD ON
hda-verb "$DEV" 0x14 0x3b0 0x00    # Pin 0x14 -> Unmute

hda-verb "$DEV" 0x1b 0x701 0x01    # Pin 0x1b (Alt Bas) -> DAC 0x03 (Connection Index 1)
hda-verb "$DEV" 0x1b 0x707 0x40    # Pin 0x1b -> OUT
hda-verb "$DEV" 0x1b 0x70c 0x02    # Pin 0x1b -> EAPD ON
hda-verb "$DEV" 0x1b 0x3b0 0x00    # Pin 0x1b -> Unmute

# 4. DAC 0x03 (Alt Bas) ve DAC 0x02 (Üst Tiz) kazançlarını kullanıcının ses seviyesine göre ayarla
echo "3. Bas DAC (0x03 -> $WOOFER_HEX) ve Tiz DAC (0x02 -> $SPK_HEX) ayarlanıyor..."
hda-verb "$DEV" 0x03 0x705 0x00          # DAC 0x03 (Bas) Power -> D0
hda-verb "$DEV" 0x03 0x3b0 "$WOOFER_HEX" # DAC 0x03 (Bas) Gain

hda-verb "$DEV" 0x02 0x705 0x00          # DAC 0x02 (Tiz) Power -> D0
hda-verb "$DEV" 0x02 0x3b0 "$SPK_HEX"    # DAC 0x02 (Tiz) Gain

# ALSA önbelleğini donanımla senkronize et (Speaker seviyesine dokunmadan Bas DAC'ını güncelle)
amixer -c "$CARD" set 'Headphone' "$WOOFER_STEP" unmute 2>/dev/null || true
amixer -c "$CARD" set 'Bass Speaker' unmute 2>/dev/null || true

echo "=== Alt Bas (0x1b @ DAC 0x03 Tam Güç) ve Üst Tiz (0x14 @ DAC 0x02 Dengeli) aktif! ==="
