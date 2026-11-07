#!/usr/bin/env bash
# MateSound Studio - Universal Linux Quad-Speaker Firmware & Initramfs Setup
# Supports: Arch/Manjaro (mkinitcpio), Ubuntu/Debian/Mint/Pop!_OS (initramfs-tools), Fedora/RHEL/openSUSE (dracut)
set -euo pipefail

echo "=== Huawei MateBook Quad-Speaker Firmware & Initramfs Setup ==="

FW_FILE="/lib/firmware/hda-jack-retask.fw"
BACKUP_FILE="/lib/firmware/hda-jack-retask.fw.bak"
MODPROBE_CONF="/etc/modprobe.d/hda-jack-retask.conf"
MKINIT_CONF="/etc/mkinitcpio.conf"

# Detect subsystem_id dynamically for Realtek ALC256 (0x10ec0256), fallback to 0x1e83323f
SUBSYS_ID="0x1e83323f"
for hw in /sys/class/sound/hwC*D0; do
    if [ -f "$hw/vendor_id" ] && grep -qi "0x10ec0256" "$hw/vendor_id" 2>/dev/null; then
        if [ -f "$hw/subsystem_id" ]; then
            DETECTED_SUB="$(head -n 1 "$hw/subsystem_id" 2>/dev/null | tr -d '[:space:]')"
            [ -n "$DETECTED_SUB" ] && SUBSYS_ID="$DETECTED_SUB"
        fi
        break
    fi
done

# 1. Backup existing firmware patch if present
if [ -f "$FW_FILE" ] && [ ! -f "$BACKUP_FILE" ]; then
    cp "$FW_FILE" "$BACKUP_FILE"
fi

# 2. Write HDA pin retask firmware (Pin 0x14 -> 0x90170111 Top Tweeters, Pin 0x1b -> 0x90170110 Bottom Woofers)
cat << EOF > "$FW_FILE"
[codec]
0x10ec0256 $SUBSYS_ID 0

[pincfg]
0x12 0x411111f0
0x13 0x40000000
0x14 0x90170111
0x18 0x411111f0
0x19 0x411111f0
0x1a 0x411111f0
0x1b 0x90170110
0x1d 0x40759a05
0x1e 0x411111f0
0x21 0x04211020
EOF

# 3. Modprobe configuration (supports both snd-hda-intel and SOF snd_soc_hdac_hda across multiple cards)
cat << 'EOF' > "$MODPROBE_CONF"
# Realtek ALC256 Huawei MateBook Quad-Speaker Retask (MateSound Studio)
options snd-hda-intel patch=hda-jack-retask.fw,hda-jack-retask.fw,hda-jack-retask.fw,hda-jack-retask.fw
options snd_soc_hdac_hda patch=hda-jack-retask.fw,hda-jack-retask.fw,hda-jack-retask.fw,hda-jack-retask.fw
options snd_hda_intel power_save=0
EOF

# 4. Universal Initramfs integration (Arch mkinitcpio / Debian-Ubuntu initramfs-tools / Fedora-openSUSE dracut)
if [ -f "$MKINIT_CONF" ] && command -v mkinitcpio >/dev/null 2>&1; then
    if ! grep -q "hda-jack-retask.fw" "$MKINIT_CONF"; then
        echo "[mkinitcpio] Adding firmware to $MKINIT_CONF..."
        python3 -c '
import re
with open("/etc/mkinitcpio.conf", "r") as f:
    c = f.read()
new_c = re.sub(r"FILES=\((.*?)\)", lambda m: f"FILES=({m.group(1).strip()} /lib/firmware/hda-jack-retask.fw)".replace("(/lib", "(/lib").replace("( ", "("), c, count=1, flags=re.DOTALL)
with open("/etc/mkinitcpio.conf", "w") as f:
    f.write(new_c)
'
        mkinitcpio -P || true
    fi
elif command -v update-initramfs >/dev/null 2>&1 && [ -d /etc/initramfs-tools ]; then
    echo "[initramfs-tools] Adding hook for Ubuntu/Debian/Mint/Pop!_OS..."
    mkdir -p /etc/initramfs-tools/hooks
    cat << 'EOF' > /etc/initramfs-tools/hooks/matesound-retask
#!/bin/sh
PREREQ=""
prereqs() { echo "$PREREQ"; }
case "${1:-}" in prereqs) prereqs; exit 0 ;; esac
. /usr/share/initramfs-tools/hook-functions
mkdir -p "${DESTDIR}/lib/firmware" "${DESTDIR}/etc/modprobe.d"
cp -f /lib/firmware/hda-jack-retask.fw "${DESTDIR}/lib/firmware/hda-jack-retask.fw" 2>/dev/null || true
cp -f /etc/modprobe.d/hda-jack-retask.conf "${DESTDIR}/etc/modprobe.d/hda-jack-retask.conf" 2>/dev/null || true
EOF
    chmod 755 /etc/initramfs-tools/hooks/matesound-retask
    update-initramfs -u || true
elif command -v dracut >/dev/null 2>&1; then
    echo "[dracut] Adding configuration for Fedora/RHEL/openSUSE..."
    mkdir -p /etc/dracut.conf.d
    cat << 'EOF' > /etc/dracut.conf.d/99-matesound.conf
install_items+=" /lib/firmware/hda-jack-retask.fw /etc/modprobe.d/hda-jack-retask.conf "
EOF
    dracut --force || true
fi

# 5. Live sysfs hint (if supported by kernel)
for hw in /sys/class/sound/hwC*D0; do
    if [ -f "$hw/vendor_id" ] && grep -qi "0x10ec0256" "$hw/vendor_id" 2>/dev/null; then
        echo "0x14 0x90170111" > "$hw/user_pin_configs" 2>/dev/null || true
    fi
done

echo "=== Pin & Initramfs setup complete ==="
