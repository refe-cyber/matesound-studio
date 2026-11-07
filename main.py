#!/usr/bin/env python3
"""
MateSound Studio - Huawei MateBook Quad-Speaker DSP & Output Manager
Universal Linux Native PyQt6 Audio Dashboard (Live Real-Time PipeWire DSP Engine)
Supports: Arch/Manjaro/CachyOS, Ubuntu/Debian/Mint/Pop!_OS, Fedora/RHEL, openSUSE
Languages: English (EN) & Türkçe (TR)
"""

import sys
import os
import re
import json
import subprocess
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSlider, QPushButton, QTabWidget, QGridLayout,
    QDoubleSpinBox, QSpinBox, QGroupBox, QRadioButton,
    QSystemTrayIcon, QMenu, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QAction, QFont, QPixmap

CONFIG_DIR = Path.home() / ".config" / "pipewire" / "pipewire.conf.d"
CONFIG_FILE = CONFIG_DIR / "matebook-nahimic.conf"
SETTINGS_FILE = Path.home() / ".config" / "matesound" / "settings.json"
APP_DIR = Path("/home/refe/İndirilenler/Nahimic")
LOGO_PATH = APP_DIR / "nahimic-logo.png"
SECURE_SCRIPT = Path("/usr/local/libexec/nahimic/enable_tweeters.sh")


def load_saved_lang():
    try:
        if SETTINGS_FILE.exists():
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            if data.get("lang") in ("tr", "en"):
                return data["lang"]
    except Exception:
        pass
    env_lang = os.environ.get("LANG", "").lower()
    return "tr" if env_lang.startswith("tr") else "en"


def save_lang_pref(lang):
    try:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(json.dumps({"lang": lang}), encoding="utf-8")
    except Exception:
        pass


CURRENT_LANG = load_saved_lang()

I18N = {
    "tr": {
        "subtitle": "Huawei MateBook X Pro • Quad-Acoustic DSP & Otomatik Çıkış Yöneticisi",
        "status_connected": "● Canlı DSP Bağlı | Kesintisiz Mod",
        "status_active_out": "● Aktif Çıkış: {dev}",
        "status_updated": "● Canlı DSP Güncellendi (0 ms Kesinti)",
        "tab_dashboard": "🎛️  Ses Kontrol Paneli",
        "tab_advanced": "⚙️  Gelişmiş DSP & Donanım",
        "out_group": "🔊 Aktif Ses Çıkışı (Ne Takarsanız Otomatik Algılar • Tek Tıkla Seçin)",
        "scanning_devs": "Bağlı ses aygıtları taranıyor...",
        "profile_group": "Akıllı Ses Profilleri",
        "prof_music_t": "🎵  Müzik Modu",
        "prof_music_d": "Sıcak & Dolgun Bas, Akustik Sahne",
        "prof_movie_t": "🎬  Sinema Modu",
        "prof_movie_d": "Derin Bas & Genişletilmiş Diyalog",
        "prof_gaming_t": "🎮  Oyun Modu",
        "prof_gaming_d": "Ayak Sesleri & Vokal Netliği",
        "prof_voice_t": "🗣️  Konuşma / Toplantı",
        "prof_voice_d": "Maksimum Vokal, Sıfır Gürültü",
        "prof_balanced_t": "⚖️  Dengeli (Huawei)",
        "prof_balanced_d": "Doğal Stüdyo Fabrika Eğrisi",
        "sliders_group": "Akustik Ayarlar & Güçlendiriciler",
        "sl_bass": "Dinamik Bas Güçlendirme (Bass Boost):",
        "sl_vocal": "Vokal & Diyalog Netliği (Voice Clarity):",
        "sl_treble": "Tiz Parlaklığı (Treble Sparkle):",
        "sl_balance": "Hoparlör Balansı (Woofer vs Tweeter):",
        "dsp_group": "Crossover & Frekans Detayları (Hz Değerleri)",
        "lbl_crossover": "Crossover Kesim Frekansı (Hz):",
        "lbl_bass_freq": "Bas Boost Frekansı (Hz):",
        "lbl_vocal_freq": "Vokal Netliği Frekansı (Hz):",
        "lbl_treble_freq": "Tiz Parlaklığı Frekansı (Hz):",
        "lbl_preamp": "Genel Ön-Amfi (Pre-amp Çarpanı):",
        "btn_reset": "↺ Varsayılana Dön",
        "hw_pins_group": "Akustik Donanım Pinleri & Sürücü Durumu (ALC256 + SOF)",
        "card_tw_title": "🔊  Üst Tiz Hoparlörler",
        "card_tw_desc": "Klavye üstü 2x Tiz sürücüsü",
        "card_wf_title": "🔊  Alt Bas Hoparlörler",
        "card_wf_desc": "Gövde altı 2x Rezonans Bas sürücüsü",
        "card_hp_title": "🎧  3.5mm Kulaklık Jakı",
        "card_hp_desc": "Otomatik algılamalı kombo soket",
        "card_mc_title": "🎙️  Dörtlü Mikrofon Dizisi",
        "card_mc_desc": "360° Akustik hüzmeleme & Dikte desteği",
        "btn_wake_one": "⚡ Uyandır",
        "btn_reinit_hw": "🔄 Pinleri Uyandır",
        "btn_refresh_hw": "🔍 Şimdi Tara",
        "last_scan_init": "Son Tarama: --:--:--",
        "last_scan_fmt": "Son Tarama: {time} ({state})",
        "all_spk_ok": "Tüm Hoparlörler Aktif",
        "some_pins_sleep": "Bazı Pinler Uykuda",
        "waking_pins": "🔄 Pinler uyandırılıyor...",
        "missing_script": "⚠ Güvenli betik kurulu değil: ./install.sh çalıştırın",
        "mic_group": "Mikrofon Girişi & Yapay Zeka Gürültü Filtresi",
        "rb_dmic": "🎙️ 4'lü Donanımsal DMIC (Dikte / Tarayıcı için ideal)",
        "rb_rnnoise": "🤖 RNNoise Yapay Zeka (Fan ve klavye gürültüsünü bastırır)",
        "tray_open": "🎛️  MateSound Studio Paneli Aç",
        "tray_out_hdr": "🔊 SES ÇIKIŞ AYGITI SEÇİMİ",
        "tray_prof_hdr": "🎵 AKILLI SES PROFİLLERİ",
        "tray_lang": "🌐 Dil / Language: TR ➔ EN",
        "tray_quit": "❌ Çıkış",
        "dev_hp": "🎧 3.5mm Kulaklık Jakı (Dahili)",
        "dev_builtin": "💻 PC Hoparlörü (MateBook 4'lü Quad)",
        "dev_bt": "🟦 Bluetooth: {desc}",
        "dev_hdmi": "🖥️ Monitör ({port})",
        "hw_active_out": "🟢 AKTİF (0x40 OUT)",
        "hw_active_standby": "🟢 AKTİF (Beklemede)",
        "hw_passive": "🔴 PASİF ({ctls})",
        "hw_wrong_dac": "🔴 YANLIŞ DAC (0x02*)",
        "hw_wrong_dac_desc": "Bas hoparlör Tiz DAC'ına bağlı (Uyandırılmalı)",
        "hw_playing": "Güç: {pwr} (Çalıyor) | {eapd} | DAC: {dac}",
        "hw_idle_sleep": "Güç: {pwr} (Boşta Uyku) | {eapd} | DAC: {dac}",
        "hw_closed_desc": "Güç: {pwr} | Çıkış Kapalı (Uyandırılmalı)",
        "eapd_on": "EAPD Açık",
        "eapd_off": "EAPD Kapalı",
        "hp_plugged": "🔵 KULAKLIK TAKILI",
        "hp_plugged_desc": "3.5mm Analog Ses Çıkışı Devrede",
        "hp_unplugged": "⚪ BOŞTA (Takılı Değil)",
        "hp_unplugged_desc": "Dahili 4'lü Hoparlör Sistemi Devrede",
        "mic_active": "🟢 AKTİF (Quad DMIC)",
        "mic_rnnoise_active": "🤖 AKTİF (RNNoise AI)",
        "mic_rnnoise_desc": "Yapay Zeka gürültü bastırma devrede",
    },
    "en": {
        "subtitle": "Huawei MateBook X Pro • Quad-Acoustic DSP & Auto Output Manager",
        "status_connected": "● Live DSP Connected | Zero-Glitch Mode",
        "status_active_out": "● Active Output: {dev}",
        "status_updated": "● Live DSP Updated (0 ms Latency)",
        "tab_dashboard": "🎛️  Audio Control Dashboard",
        "tab_advanced": "⚙️  Advanced DSP & Hardware",
        "out_group": "🔊 Active Audio Output (Auto-Detects Hotplug • One-Click Select)",
        "scanning_devs": "Scanning connected audio devices...",
        "profile_group": "Smart Acoustic Profiles",
        "prof_music_t": "🎵  Music Mode",
        "prof_music_d": "Warm & Punchy Bass, Wide Soundstage",
        "prof_movie_t": "🎬  Cinema Mode",
        "prof_movie_d": "Deep Sub-Bass & Enhanced Dialogue",
        "prof_gaming_t": "🎮  Gaming Mode",
        "prof_gaming_d": "Footstep Precision & Vocal Clarity",
        "prof_voice_t": "🗣️  Voice / Meeting",
        "prof_voice_d": "Crystal Clear Vocals, Zero Rumble",
        "prof_balanced_t": "⚖️  Balanced (Huawei)",
        "prof_balanced_d": "Natural Studio Reference Curve",
        "sliders_group": "Acoustic Equalizer & Enhancers",
        "sl_bass": "Dynamic Bass Boost:",
        "sl_vocal": "Voice & Dialogue Clarity:",
        "sl_treble": "Treble Sparkle & Air:",
        "sl_balance": "Speaker Balance (Woofer vs Tweeter):",
        "dsp_group": "Crossover & Frequency Parameters (Hz)",
        "lbl_crossover": "Crossover Cutoff Frequency (Hz):",
        "lbl_bass_freq": "Bass Boost Center Frequency (Hz):",
        "lbl_vocal_freq": "Vocal Clarity Center Frequency (Hz):",
        "lbl_treble_freq": "Treble Sparkle Frequency (Hz):",
        "lbl_preamp": "Master Pre-Amp Gain Multiplier:",
        "btn_reset": "↺ Reset to Defaults",
        "hw_pins_group": "Hardware Codec Pins & Driver Status (ALC256 + SOF)",
        "card_tw_title": "🔊  Top Tweeter Speakers",
        "card_tw_desc": "2x Upward-firing keyboard tweeters",
        "card_wf_title": "🔊  Bottom Woofer Speakers",
        "card_wf_desc": "2x Downward-firing resonance woofers",
        "card_hp_title": "🎧  3.5mm Headphone Jack",
        "card_hp_desc": "Auto-impedance combo audio jack",
        "card_mc_title": "🎙️  Quad Microphone Array",
        "card_mc_desc": "360° Beamforming & Voice Dictation",
        "btn_wake_one": "⚡ Wake Pin",
        "btn_reinit_hw": "🔄 Wake Hardware Pins",
        "btn_refresh_hw": "🔍 Scan Now",
        "last_scan_init": "Last Scan: --:--:--",
        "last_scan_fmt": "Last Scan: {time} ({state})",
        "all_spk_ok": "All 4 Speakers Active",
        "some_pins_sleep": "Some Pins Sleeping",
        "waking_pins": "🔄 Waking hardware pins...",
        "missing_script": "⚠ Helper script not installed: run ./install.sh",
        "mic_group": "Microphone Input & AI Noise Suppression",
        "rb_dmic": "🎙️ Quad Hardware DMIC (Best for Dictation / Browser)",
        "rb_rnnoise": "🤖 RNNoise AI Filter (Suppresses fan & keyboard noise)",
        "tray_open": "🎛️  Open MateSound Studio",
        "tray_out_hdr": "🔊 AUDIO OUTPUT DEVICE",
        "tray_prof_hdr": "🎵 SMART SOUND PROFILES",
        "tray_lang": "🌐 Language / Dil: EN ➔ TR",
        "tray_quit": "❌ Quit",
        "dev_hp": "🎧 3.5mm Headphone Jack (Built-in)",
        "dev_builtin": "💻 PC Speakers (MateBook Quad-Speaker)",
        "dev_bt": "🟦 Bluetooth: {desc}",
        "dev_hdmi": "🖥️ Monitor ({port})",
        "hw_active_out": "🟢 ACTIVE (0x40 OUT)",
        "hw_active_standby": "🟢 ACTIVE (Standby)",
        "hw_passive": "🔴 INACTIVE ({ctls})",
        "hw_wrong_dac": "🔴 WRONG DAC (0x02*)",
        "hw_wrong_dac_desc": "Woofers routed to Tweeter DAC (Click Wake)",
        "hw_playing": "Power: {pwr} (Playing) | {eapd} | DAC: {dac}",
        "hw_idle_sleep": "Power: {pwr} (Idle Power-Save) | {eapd} | DAC: {dac}",
        "hw_closed_desc": "Power: {pwr} | Output Disabled (Click Wake)",
        "eapd_on": "EAPD On",
        "eapd_off": "EAPD Off",
        "hp_plugged": "🔵 HEADPHONES PLUGGED",
        "hp_plugged_desc": "3.5mm Analog Audio Output Active",
        "hp_unplugged": "⚪ IDLE (Unplugged)",
        "hp_unplugged_desc": "Internal Quad-Speaker System Active",
        "mic_active": "🟢 ACTIVE (Quad DMIC)",
        "mic_rnnoise_active": "🤖 ACTIVE (RNNoise AI)",
        "mic_rnnoise_desc": "AI neural noise suppression active",
    }
}


def _t(key, **kwargs):
    table = I18N.get(CURRENT_LANG, I18N["en"])
    text = table.get(key, I18N["en"].get(key, key))
    return text.format(**kwargs) if kwargs else text


class HardwareStatusWorker(QThread):
    """Realtek ALC256 Codec ve SOF Donanım Pinlerini Arka Planda Tutan İşçi"""
    status_updated = pyqtSignal(dict)

    def run(self):
        res = {
            "tweeter": {
                "name": "Üst Tiz Hoparlörler",
                "pin": "Node 0x14 | DAC 0x02",
                "status": "🔴 PASİF",
                "active": False,
                "desc": "Klavye üstü 2x Tiz sürücüsü",
                "badge_class": "badge-inactive"
            },
            "woofer": {
                "name": "Alt Bas Hoparlörler",
                "pin": "Node 0x1b | DAC 0x03",
                "status": "🔴 PASİF",
                "active": False,
                "desc": "Gövde altı 2x Rezonans Bas sürücüsü",
                "badge_class": "badge-inactive"
            },
            "headphone": {
                "name": "3.5mm Analog Kulaklık Jakı",
                "pin": "Node 0x21 | DAC 0x02",
                "status": "⚪ BOŞTA (Takılı Değil)",
                "active": False,
                "desc": "Otomatik empedans algılamalı kombo soket",
                "badge_class": "badge-idle"
            },
            "mic": {
                "name": "Dörtlü Mikrofon Dizisi",
                "pin": "Tiger Lake SOF Digital Mic",
                "status": "🟢 AKTİF (Quad DMIC)",
                "active": True,
                "desc": "360° Akustik hüzmeleme & Dikte desteği",
                "badge_class": "badge-active"
            }
        }

        codec_path = "/proc/asound/sofhdadsp/codec#0"
        if not os.path.exists(codec_path):
            for cand in sorted(Path("/proc/asound").glob("card*/codec#0")):
                codec_path = str(cand)
                break
        if os.path.exists(codec_path):
            try:
                with open(codec_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                def parse_node(node_hex):
                    m = re.search(r"Node " + re.escape(node_hex) + r"\s+\[.*?\](.*?)(?=Node 0x|\Z)", content, re.DOTALL)
                    if not m:
                        return None, None, None, ""
                    block = m.group(1)
                    ctls_m = re.search(r"Pin-ctls:\s*(0x[0-9a-fA-F]+)", block)
                    pwr_m = re.search(r"Power:\s*setting=\w+,\s*actual=(D\d)", block)
                    eapd_m = re.search(r"EAPD\s*(0x[0-9a-fA-F]+)", block)
                    ctls = ctls_m.group(1).lower() if ctls_m else "0x00"
                    pwr = pwr_m.group(1) if pwr_m else "D0"
                    eapd = _t("eapd_on") if eapd_m and eapd_m.group(1) == "0x2" else _t("eapd_off")
                    return ctls, pwr, eapd, block

                # Tweeter (Node 0x14)
                ctls14, pwr14, eapd14, _ = parse_node("0x14")
                if ctls14 is not None:
                    if ctls14 == "0x40":
                        res["tweeter"]["active"] = True
                        res["tweeter"]["badge_class"] = "badge-active"
                        if pwr14 == "D0":
                            res["tweeter"]["status"] = _t("hw_active_out")
                            res["tweeter"]["desc"] = _t("hw_playing", pwr=pwr14, eapd=eapd14, dac="0x02")
                        else:
                            res["tweeter"]["status"] = _t("hw_active_standby")
                            res["tweeter"]["desc"] = _t("hw_idle_sleep", pwr=pwr14, eapd=eapd14, dac="0x02")
                    else:
                        res["tweeter"]["active"] = False
                        res["tweeter"]["badge_class"] = "badge-inactive"
                        res["tweeter"]["status"] = _t("hw_passive", ctls=ctls14.upper())
                        res["tweeter"]["desc"] = _t("hw_closed_desc", pwr=pwr14)

                # Woofer (Node 0x1b)
                ctls1b, pwr1b, eapd1b, block1b = parse_node("0x1b")
                if ctls1b is not None:
                    on_dac03 = "0x03*" in block1b
                    if ctls1b == "0x40" and on_dac03:
                        res["woofer"]["active"] = True
                        res["woofer"]["badge_class"] = "badge-active"
                        if pwr1b == "D0":
                            res["woofer"]["status"] = _t("hw_active_out")
                            res["woofer"]["desc"] = _t("hw_playing", pwr=pwr1b, eapd=eapd1b, dac="0x03*")
                        else:
                            res["woofer"]["status"] = _t("hw_active_standby")
                            res["woofer"]["desc"] = _t("hw_idle_sleep", pwr=pwr1b, eapd=eapd1b, dac="0x03*")
                    elif ctls1b == "0x40" and not on_dac03:
                        res["woofer"]["active"] = False
                        res["woofer"]["badge_class"] = "badge-inactive"
                        res["woofer"]["status"] = _t("hw_wrong_dac")
                        res["woofer"]["desc"] = _t("hw_wrong_dac_desc")
                    else:
                        res["woofer"]["active"] = False
                        res["woofer"]["badge_class"] = "badge-inactive"
                        res["woofer"]["status"] = _t("hw_passive", ctls=ctls1b.upper())
                        res["woofer"]["desc"] = _t("hw_closed_desc", pwr=pwr1b)

                # Headphone (Node 0x21)
                hp_jack = False
                try:
                    out = subprocess.check_output(
                        ["amixer", "-c", "sofhdadsp", "cget", "iface=CARD,name='Headphone Jack'"],
                        text=True, stderr=subprocess.DEVNULL
                    )
                    hp_jack = "values=on" in out
                except Exception:
                    pass

                if hp_jack:
                    res["headphone"]["status"] = _t("hp_plugged")
                    res["headphone"]["active"] = True
                    res["headphone"]["desc"] = _t("hp_plugged_desc")
                    res["headphone"]["badge_class"] = "badge-plugged"
                else:
                    res["headphone"]["status"] = _t("hp_unplugged")
                    res["headphone"]["active"] = False
                    res["headphone"]["desc"] = _t("hp_unplugged_desc")
                    res["headphone"]["badge_class"] = "badge-idle"
            except Exception as e:
                print(f"Codec okuma hatası: {e}")

        self.status_updated.emit(res)


DMIC_SOURCE = "alsa_input.pci-0000_00_1f.3-platform-skl_hda_dsp_generic.HiFi__Mic1__source"
NAHIMIC_SINK = "matebook_nahimic_sink"


def _run(cmd):
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL, timeout=4)
    except Exception:
        return ""


class DeviceWatcher(QThread):
    """Takılan tüm ses aygıtlarını (PC Hoparlörü, Jabra/USB, Bluetooth, Kulaklık, HDMI) algılar ve DSP çıkışını yönetir"""
    state_changed = pyqtSignal(dict)

    def __init__(self, rnnoise_selected):
        super().__init__()
        self.rnnoise_selected = rnnoise_selected  # callable -> bool
        self.known_sinks = None
        self.known_hp = False
        self.active_sink = None

    def list_physical_sinks(self, hp):
        """Bağlı ve kullanılabilir tüm fiziksel çıkış aygıtlarını okunabilir isimlerle döndürür"""
        out = _run(["pactl", "list", "sinks"])
        devices = []
        for block in out.split("Sink #")[1:]:
            name_m = re.search(r"^\s*Name:\s*(.+)$", block, re.MULTILINE)
            desc_m = re.search(r"^\s*Description:\s*(.+)$", block, re.MULTILINE)
            if not name_m:
                continue
            name = name_m.group(1).strip()
            desc = desc_m.group(1).strip() if desc_m else name
            if name == NAHIMIC_SINK:
                continue
            # Takılı olmayan HDMI çıkışlarını gizle
            if "HDMI" in name.upper() and "not available" in block:
                continue

            if name.startswith("alsa_output.pci-") and "HDMI" not in name.upper():
                if hp:
                    label = _t("dev_hp")
                    kind = "hp"
                else:
                    label = _t("dev_builtin")
                    kind = "builtin"
            elif name.startswith("bluez_output"):
                label = _t("dev_bt", desc=desc)
                kind = "bt"
            elif "HDMI" in name.upper():
                port_name = desc.split("Output")[0].split("Audio)")[-1].strip() or "HDMI"
                label = _t("dev_hdmi", port=port_name)
                kind = "hdmi"
            elif "usb" in name.lower():
                icon = "🎧" if ("jabra" in name.lower() or "headset" in name.lower()) else "🔌"
                label = f"{icon} {desc}"
                kind = "usb"
            else:
                label = f"🔊 {desc}"
                kind = "other"

            devices.append({"name": name, "label": label, "kind": kind})

        # Sıralama: Dahili PC Hoparlörü / Kulaklık en üstte, sonra Bluetooth, USB, HDMI
        order = {"builtin": 0, "hp": 0, "bt": 1, "usb": 2, "hdmi": 3, "other": 4}
        devices.sort(key=lambda d: (order.get(d["kind"], 9), d["label"]))
        return devices

    def probe(self):
        hp = "values=on" in _run(["amixer", "-c", "sofhdadsp", "cget", "iface=CARD,name='Headphone Jack'"])
        devices = self.list_physical_sinks(hp)
        sources = [l.split("\t")[1] for l in _run(["pactl", "list", "short", "sources"]).splitlines() if "\t" in l]
        bt = next((d["name"] for d in devices if d["kind"] == "bt"), None)
        headset = next((s for s in sources if "Headset" in s and not s.endswith(".monitor")), None)
        builtin = next((d["name"] for d in devices if d["kind"] in ("builtin", "hp")), None)

        current_names = {d["name"] for d in devices}
        if self.known_sinks is None:
            # İlk açılış: Bluetooth bağlıysa onu, değilse PC Hoparlörünü seç
            self.known_sinks = set(current_names)
            self.known_hp = hp
            self.active_sink = bt or builtin or (devices[0]["name"] if devices else None)
        else:
            # Yeni bir USB / Bluetooth / HDMI aygıtı takıldıysa otomatik ona geç!
            added = [d["name"] for d in devices if d["name"] not in self.known_sinks]
            if added:
                self.active_sink = added[0]
            elif hp != self.known_hp and builtin:
                # 3.5mm kulaklık takıldı veya çıkarıldı
                self.active_sink = builtin
            elif self.active_sink not in current_names:
                # Seçili aygıt çıkarıldıysa PC hoparlörüne dön
                self.active_sink = bt or builtin or (devices[0]["name"] if devices else None)

            self.known_sinks = set(current_names)
            self.known_hp = hp

        return {
            "hp": hp,
            "bt": bt,
            "headset": headset,
            "builtin": builtin,
            "devices": devices,
            "active_sink": self.active_sink,
        }

    def select_sink(self, sink_name):
        """Kullanıcı sağ tık tepsi menüsünden veya panelden çıkış aygıtı seçtiğinde anında uygular"""
        self.active_sink = sink_name
        st = self.probe()
        st["active_sink"] = sink_name
        self.apply(st)
        self.state_changed.emit(st)

    def route_streams(self, dest_sink):
        """Uygulama seslerini MateSound DSP'ye, MateSound DSP çıkışını ise seçili fiziksel aygıta yönlendirir"""
        sinks_short = _run(["pactl", "list", "short", "sinks"])
        sink_id_to_name = {}
        for line in sinks_short.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2:
                sink_id_to_name[parts[0].strip()] = parts[1].strip()

        for block in _run(["pactl", "list", "sink-inputs"]).split("Sink Input #")[1:]:
            sid = block.split("\n", 1)[0].strip()
            sink_m = re.search(r"^\s*Sink:\s*(\d+)", block, re.MULTILINE)
            cur_sink_name = sink_id_to_name.get(sink_m.group(1), "") if sink_m else ""
            if 'node.name = "matebook_nahimic_output"' in block:
                if dest_sink and cur_sink_name != dest_sink:
                    subprocess.run(["pactl", "move-sink-input", sid, dest_sink],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                # Chrome, Spotify, OBS vb. tüm uygulamalar MateSound DSP üzerinden geçsin
                if cur_sink_name != NAHIMIC_SINK:
                    subprocess.run(["pactl", "move-sink-input", sid, NAHIMIC_SINK],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def apply(self, st):
        # Mikrofon: kulaklık mikrofonu varsa onu, yoksa dahili DMIC'i kullan (RNNoise seçiliyse dokunma)
        if not self.rnnoise_selected():
            target = st["headset"] if (st["hp"] and st["headset"]) else DMIC_SOURCE
            subprocess.run(["pactl", "set-default-source", target],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Sistem varsayılan çıkışı her zaman MateSound DSP olsun, hedef ise seçili aygıt
        subprocess.run(["pactl", "set-default-sink", NAHIMIC_SINK],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        dest = st.get("active_sink") or st.get("builtin")
        if dest:
            self.route_streams(dest)

    def run(self):
        last = None
        while not self.isInterruptionRequested():
            st = self.probe()
            self.apply(st)
            if st != last:
                self.state_changed.emit(st)
                last = st
            self.msleep(2000)


class AudioEngine:
    """PipeWire Filter-Chain ve ALSA Canlı Gerçek Zamanlı Denetleyici"""

    def __init__(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.tweeter_step = 70

    def get_sink_node_id(self):
        """Çalışan PipeWire içinde matebook_nahimic_sink ID'sini dinamik bulur"""
        try:
            out = subprocess.check_output(["pw-cli", "list-objects", "Node"], text=True)
            current_id = None
            for line in out.splitlines():
                line_str = line.strip()
                if line_str.startswith("id "):
                    parts = line_str.split()
                    if len(parts) >= 2:
                        current_id = parts[1].rstrip(",")
                if 'node.name = "matebook_nahimic_sink"' in line_str and current_id:
                    return current_id
        except Exception as e:
            print(f"Node ID bulma hatası: {e}")
        return None

    def update_live_dsp(self,
                        bass_gain=5.5, bass_freq=160.0,
                        vocal_gain=1.5, vocal_freq=2500.0,
                        treble_gain=1.5, treble_freq=11000.0,
                        crossover_freq=1800.0,
                        preamp_woofer=1.30, preamp_tweeter=1.10):
        """
        PipeWire'ı ASLA yeniden başlatmaz!
        Çalan müziği/videoyu kesmeden çalışan DSP düğümlerine canlı enjekte eder.
        """
        node_id = self.get_sink_node_id()
        g1 = preamp_woofer * 0.95
        g2 = -preamp_tweeter * 0.50
        if node_id:
            spa_string = f"""{{ params = [
                "woofer_lp_L:Freq" {crossover_freq:.1f}
                "woofer_lp_R:Freq" {crossover_freq:.1f}
                "woofer_lp_L:Q" 0.6
                "woofer_lp_R:Q" 0.6
                "tweeter_hp_L:Freq" {crossover_freq:.1f}
                "tweeter_hp_R:Freq" {crossover_freq:.1f}
                "tweeter_hp_L:Q" 0.6
                "tweeter_hp_R:Q" 0.6
                "bass_boost_L:Freq" {bass_freq:.1f}
                "bass_boost_R:Freq" {bass_freq:.1f}
                "bass_boost_L:Gain" {bass_gain:.1f}
                "bass_boost_R:Gain" {bass_gain:.1f}
                "voice_clarity_L:Freq" {vocal_freq:.1f}
                "voice_clarity_R:Freq" {vocal_freq:.1f}
                "voice_clarity_L:Gain" {vocal_gain:.1f}
                "voice_clarity_R:Gain" {vocal_gain:.1f}
                "treble_sparkle_L:Freq" {treble_freq:.1f}
                "treble_sparkle_R:Freq" {treble_freq:.1f}
                "treble_sparkle_L:Gain" {treble_gain:.1f}
                "treble_sparkle_R:Gain" {treble_gain:.1f}
                "mix_L:Gain 1" {g1:.2f}
                "mix_R:Gain 1" {g1:.2f}
                "mix_L:Gain 2" {g2:.2f}
                "mix_R:Gain 2" {g2:.2f}
            ] }}"""
            try:
                subprocess.run(["pw-cli", "s", str(node_id), "Props", spa_string],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                print(f"Canlı DSP güncelleme hatası: {e}")

        # Kalıcılık için arka planda konfigürasyonu da kaydet
        self.save_config_file(
            bass_gain, bass_freq, vocal_gain, vocal_freq,
            treble_gain, treble_freq, crossover_freq,
            preamp_woofer, preamp_tweeter
        )

    def save_config_file(self, bass_gain, bass_freq, vocal_gain, vocal_freq,
                         treble_gain, treble_freq, crossover_freq,
                         preamp_woofer, preamp_tweeter):
        g1 = preamp_woofer * 0.95
        g2 = -preamp_tweeter * 0.50
        conf_content = f"""# Huawei MateBook X Pro - MateSound Studio Crossover & Bass Engine
# Generated by MateSound Studio

context.modules = [
    {{ name = libpipewire-module-filter-chain
        flags = [ nofail ]
        args = {{
            node.description = "MateSound Studio (Huawei Quad-Audio)"
            media.name       = "MateSound Studio (Huawei Quad-Audio)"
            filter.graph = {{
                nodes = [
                    {{ type = builtin name = in_L label = copy }}
                    {{ type = builtin name = in_R label = copy }}

                    {{
                        type = builtin
                        name = woofer_lp_L
                        label = bq_lowpass
                        control = {{ "Freq" = {crossover_freq:.1f} "Q" = 0.6 }}
                    }}
                    {{
                        type = builtin
                        name = woofer_lp_R
                        label = bq_lowpass
                        control = {{ "Freq" = {crossover_freq:.1f} "Q" = 0.6 }}
                    }}
                    {{
                        type = builtin
                        name = bass_boost_L
                        label = bq_lowshelf
                        control = {{ "Freq" = {bass_freq:.1f} "Gain" = {bass_gain:.1f} }}
                    }}
                    {{
                        type = builtin
                        name = bass_boost_R
                        label = bq_lowshelf
                        control = {{ "Freq" = {bass_freq:.1f} "Gain" = {bass_gain:.1f} }}
                    }}

                    {{
                        type = builtin
                        name = tweeter_hp_L
                        label = bq_highpass
                        control = {{ "Freq" = {crossover_freq:.1f} "Q" = 0.6 }}
                    }}
                    {{
                        type = builtin
                        name = tweeter_hp_R
                        label = bq_highpass
                        control = {{ "Freq" = {crossover_freq:.1f} "Q" = 0.6 }}
                    }}
                    {{
                        type = builtin
                        name = voice_clarity_L
                        label = bq_peaking
                        control = {{ "Freq" = {vocal_freq:.1f} "Gain" = {vocal_gain:.1f} "Q" = 1.0 }}
                    }}
                    {{
                        type = builtin
                        name = voice_clarity_R
                        label = bq_peaking
                        control = {{ "Freq" = {vocal_freq:.1f} "Gain" = {vocal_gain:.1f} "Q" = 1.0 }}
                    }}
                    {{
                        type = builtin
                        name = treble_sparkle_L
                        label = bq_highshelf
                        control = {{ "Freq" = {treble_freq:.1f} "Gain" = {treble_gain:.1f} }}
                    }}
                    {{
                        type = builtin
                        name = treble_sparkle_R
                        label = bq_highshelf
                        control = {{ "Freq" = {treble_freq:.1f} "Gain" = {treble_gain:.1f} }}
                    }}

                    {{
                        type = builtin
                        name = mix_L
                        label = mixer
                        control = {{ "Gain 1" = {g1:.2f} "Gain 2" = {g2:.2f} }}
                    }}
                    {{
                        type = builtin
                        name = mix_R
                        label = mixer
                        control = {{ "Gain 1" = {g1:.2f} "Gain 2" = {g2:.2f} }}
                    }}
                ]
                links = [
                    {{ output = "in_L:Out" input = "woofer_lp_L:In" }}
                    {{ output = "woofer_lp_L:Out" input = "bass_boost_L:In" }}
                    {{ output = "bass_boost_L:Out" input = "mix_L:In 1" }}

                    {{ output = "in_L:Out" input = "tweeter_hp_L:In" }}
                    {{ output = "tweeter_hp_L:Out" input = "voice_clarity_L:In" }}
                    {{ output = "voice_clarity_L:Out" input = "treble_sparkle_L:In" }}
                    {{ output = "treble_sparkle_L:Out" input = "mix_L:In 2" }}

                    {{ output = "in_R:Out" input = "woofer_lp_R:In" }}
                    {{ output = "woofer_lp_R:Out" input = "bass_boost_R:In" }}
                    {{ output = "bass_boost_R:Out" input = "mix_R:In 1" }}

                    {{ output = "in_R:Out" input = "tweeter_hp_R:In" }}
                    {{ output = "tweeter_hp_R:Out" input = "voice_clarity_R:In" }}
                    {{ output = "voice_clarity_R:Out" input = "treble_sparkle_R:In" }}
                    {{ output = "treble_sparkle_R:Out" input = "mix_R:In 2" }}
                ]
                inputs  = [ "in_L:In" "in_R:In" ]
                outputs = [ "mix_L:Out" "mix_R:Out" ]
            }}
            capture.props = {{
                node.name         = "matebook_nahimic_sink"
                node.description  = "MateSound Studio (Huawei Quad-Audio)"
                media.class       = "Audio/Sink"
                audio.position    = [ FL FR ]
            }}
            playback.props = {{
                node.name         = "matebook_nahimic_output"
                node.passive      = true
                audio.position    = [ FL FR ]
                target.object     = "alsa_output.pci-0000_00_1f.3-platform-skl_hda_dsp_generic.HiFi__Speaker__sink"
            }}
        }}
    }}
]
"""
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(conf_content)

    def ensure_hardware_unmuted(self, force_dac_sync=False):
        """Kullanıcının KDE ses seviyesine (Speaker) dokunmadan, Alt Bas DAC (0x03 / Headphone) kazancını senkronize eder"""
        try:
            # 3.5mm kulaklık takılıysa kulaklık sesine müdahale etme
            hp_out = subprocess.check_output(
                ["amixer", "-c", "sofhdadsp", "cget", "iface=CARD,name='Headphone Jack'"],
                text=True, stderr=subprocess.DEVNULL
            )
            if "values=on" in hp_out:
                return

            spk_out = subprocess.check_output(
                ["amixer", "-c", "sofhdadsp", "sget", "Speaker"],
                text=True, stderr=subprocess.DEVNULL
            )
            m = re.search(r"Playback\s+(\d+)\s+\[\d+%\]\s+.*?\[(on|off)\]", spk_out)
            if not m:
                return
            spk_step = int(m.group(1))
            spk_on = (m.group(2) == "on")

            # Kullanıcının Speaker ses seviyesini ASLA değiştirme (%61'e zıplamasını önler).
            # Alt Bas (Headphone = DAC 0x03) seviyesini Üst Tiz (Speaker = DAC 0x02) seviyesinin +bass_offset üstünde tut:
            bass_offset = 87 - int(getattr(self, "tweeter_step", 70))
            if not spk_on or spk_step == 0:
                target_state = (0, "mute")
            else:
                woofer_step = min(87, max(1, spk_step + bass_offset))
                target_state = (woofer_step, "unmute")

            if force_dac_sync or getattr(self, "_last_woofer_state", None) != target_state:
                self._last_woofer_state = target_state
                subprocess.run(["amixer", "-c", "sofhdadsp", "set", "Bass Speaker", "unmute"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(["amixer", "-c", "sofhdadsp", "set", "Headphone", str(target_state[0]), target_state[1]],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass


class NahimicWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.engine = AudioEngine()
        self.setWindowTitle("MateSound Studio - Huawei MateBook X Pro")
        self.resize(900, 800)
        self.setMinimumSize(820, 620)
        self.current_devices = []
        self.current_active_sink = None

        # Özelleştirilmiş neon 'M' ikonu
        if LOGO_PATH.exists():
            self.app_icon = QIcon(str(LOGO_PATH))
        else:
            self.app_icon = QIcon.fromTheme("audio-speakers")
        self.setWindowIcon(self.app_icon)

        # Donanım durumu kontrol işçisi
        self.hw_worker = HardwareStatusWorker()
        self.hw_worker.status_updated.connect(self.on_hardware_status_updated)

        self.init_ui()
        self.init_tray()

        # Başlangıçta DAC kazançlarını (0dB) ve canlı DSP filtrelerini senkronize et
        self.last_auto_heal = 0
        self.engine.ensure_hardware_unmuted(force_dac_sync=True)
        self.apply_live_changes(silent=True)

        # İlk durumu hemen al
        self.request_hardware_status_refresh()

        # Kulaklık / Bluetooth otomatik yönetimi
        self.saved_before_bt = None
        self.watcher = DeviceWatcher(lambda: self.rb_rnnoise.isChecked())
        self.watcher.state_changed.connect(self.on_device_state)
        self.watcher.start()

        # 5 saniyede bir periyodik donanım pin taraması
        self.hw_poll_timer = QTimer(self)
        self.hw_poll_timer.timeout.connect(self.request_hardware_status_refresh)
        self.hw_poll_timer.start(5000)

        # 800 ms'de bir Alt Bas (DAC 0x03) kazancını KDE ses çubuğuyla senkronize tut (Speaker'a dokunmaz!)
        self.health_timer = QTimer(self)
        self.health_timer.timeout.connect(self.engine.ensure_hardware_unmuted)
        self.health_timer.start(800)

    def init_ui(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0f1118;
            }
            QWidget {
                color: #e0e6ed;
                font-family: 'Segoe UI', 'Ubuntu', 'Noto Sans', sans-serif;
            }
            QTabWidget::pane {
                border: 1px solid #1f2638;
                background: #141824;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #0f1118;
                color: #8b9bb4;
                padding: 10px 24px;
                margin-right: 4px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QTabBar::tab:selected {
                background: #141824;
                color: #00d2ff;
                border-bottom: 2px solid #00d2ff;
            }
            QGroupBox {
                border: 1px solid #1f2638;
                border-radius: 8px;
                margin-top: 18px;
                font-weight: bold;
                font-size: 13px;
                color: #00d2ff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 6px;
            }
            QPushButton.profile-btn {
                background: #191f2e;
                border: 1px solid #28334a;
                border-radius: 8px;
                padding: 12px;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                text-align: left;
            }
            QPushButton.profile-btn:hover {
                background: #222b40;
                border: 1px solid #00d2ff;
            }
            QPushButton.profile-btn[active="true"] {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #005b82, stop:1 #0096c7);
                border: 1px solid #00d2ff;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #1b2232;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8a2be2, stop:1 #00d2ff);
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #00d2ff;
                width: 16px;
                margin-top: -5px;
                margin-bottom: -5px;
                border-radius: 8px;
            }
            QDoubleSpinBox, QSpinBox {
                background: #181f2f;
                border: 1px solid #2a354d;
                border-radius: 5px;
                padding: 5px;
                color: #00d2ff;
                font-weight: bold;
            }
            QPushButton.action-btn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0077b6, stop:1 #00b4d8);
                border: none;
                border-radius: 6px;
                padding: 10px 18px;
                color: white;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton.action-btn:hover {
                background: #00d2ff;
                color: #000;
            }
        """)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 1. Başlık, Logo ve Donanım Rozeti
        header_layout = QHBoxLayout()

        if LOGO_PATH.exists():
            logo_lbl = QLabel()
            logo_pix = QPixmap(str(LOGO_PATH)).scaled(
                44, 44, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            logo_lbl.setPixmap(logo_pix)
            header_layout.addWidget(logo_lbl)
            header_layout.addSpacing(10)

        title_box = QVBoxLayout()
        app_title = QLabel("MATESOUND STUDIO")
        app_title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        app_title.setStyleSheet("color: #00f5d4; letter-spacing: 2px;")
        
        self.device_subtitle = QLabel(_t("subtitle"))
        self.device_subtitle.setStyleSheet("color: #8898aa; font-size: 12px;")
        title_box.addWidget(app_title)
        title_box.addWidget(self.device_subtitle)

        # Durum Göstergesi
        self.status_box = QLabel(_t("status_connected"))
        self.status_box.setStyleSheet("""
            background: #0d2818;
            color: #2ec4b6;
            border: 1px solid #165b33;
            border-radius: 12px;
            padding: 6px 14px;
            font-weight: bold;
            font-size: 11px;
        """)

        # Dil Değiştirme Butonu (EN / TR)
        self.btn_lang = QPushButton(f"🌐 {CURRENT_LANG.upper()}")
        self.btn_lang.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_lang.setStyleSheet("""
            QPushButton {
                background: #191f2e;
                border: 1px solid #00f5d4;
                border-radius: 12px;
                padding: 6px 12px;
                color: #00f5d4;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #00f5d4;
                color: #0f1118;
            }
        """)
        self.btn_lang.clicked.connect(self.toggle_language)

        header_layout.addLayout(title_box)
        header_layout.addStretch()
        header_layout.addWidget(self.status_box)
        header_layout.addSpacing(8)
        header_layout.addWidget(self.btn_lang)
        main_layout.addLayout(header_layout)

        main_layout.addSpacing(10)

        # 2. Sekmeler (Dashboard ve Gelişmiş Ayarlar)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.tab_dashboard = QWidget()
        self.tab_advanced = QWidget()
        self.tabs.addTab(self.tab_dashboard, _t("tab_dashboard"))
        self.tabs.addTab(self.tab_advanced, _t("tab_advanced"))

        self.build_dashboard_tab()
        self.build_advanced_tab()
        self.tabs.currentChanged.connect(self.on_tab_changed)

    def build_dashboard_tab(self):
        layout = QVBoxLayout(self.tab_dashboard)
        layout.setContentsMargins(15, 15, 15, 15)

        # 0. Aktif Ses Çıkış Aygıtı Seçici (Sağ tık menüsüyle senkronize)
        self.out_group = QGroupBox(_t("out_group"))
        self.out_devices_layout = QHBoxLayout(self.out_group)
        self.out_devices_layout.setSpacing(8)
        lbl_scanning = QLabel(_t("scanning_devs"))
        lbl_scanning.setStyleSheet("color: #8898aa; font-size: 12px;")
        self.out_devices_layout.addWidget(lbl_scanning)
        layout.addWidget(self.out_group)

        # Profiller Grubu
        self.profile_group = QGroupBox(_t("profile_group"))
        profile_layout = QGridLayout(self.profile_group)

        self.profile_btns = {}
        profiles = [
            ("music", _t("prof_music_t"), _t("prof_music_d")),
            ("movie", _t("prof_movie_t"), _t("prof_movie_d")),
            ("gaming", _t("prof_gaming_t"), _t("prof_gaming_d")),
            ("voice", _t("prof_voice_t"), _t("prof_voice_d")),
            ("balanced", _t("prof_balanced_t"), _t("prof_balanced_d"))
        ]

        row, col = 0, 0
        for pid, name, desc in profiles:
            btn = QPushButton(f"{name}\n{desc}")
            btn.setProperty("class", "profile-btn")
            btn.clicked.connect(lambda checked, p=pid: self.apply_preset(p))
            profile_layout.addWidget(btn, row, col)
            self.profile_btns[pid] = btn
            col += 1
            if col > 1:
                col = 0
                row += 1

        layout.addWidget(self.profile_group)

        # Akustik Kaydırıcılar Grubu
        self.sliders_group = QGroupBox(_t("sliders_group"))
        sliders_layout = QVBoxLayout(self.sliders_group)

        # 1. Dinamik Bas Güçlendirme
        self.slider_bass, self.lbl_bass, self.title_bass = self.create_slider_row(
            sliders_layout, _t("sl_bass"), 0, 80, 55, "dB", 0.1
        )

        # 2. Ses / Vokal Netliği
        self.slider_vocal, self.lbl_vocal, self.title_vocal = self.create_slider_row(
            sliders_layout, _t("sl_vocal"), 0, 60, 15, "dB", 0.1
        )

        # 3. Tiz Parlaklığı
        self.slider_treble, self.lbl_treble, self.title_treble = self.create_slider_row(
            sliders_layout, _t("sl_treble"), 0, 60, 15, "dB", 0.1
        )

        # 4. Alt/Üst Hoparlör Balansı (Woofer / Tweeter)
        self.slider_balance, self.lbl_balance, self.title_balance = self.create_slider_row(
            sliders_layout, _t("sl_balance"), 50, 150, 100, "%", 1.0
        )

        # Kaydırıcılar değiştiğinde doğrudan canlı güncelle (YouTube kesilmez!)
        self.slider_bass.valueChanged.connect(self.schedule_live_changes)
        self.slider_vocal.valueChanged.connect(self.schedule_live_changes)
        self.slider_treble.valueChanged.connect(self.schedule_live_changes)
        self.slider_balance.valueChanged.connect(self.schedule_live_changes)

        layout.addWidget(self.sliders_group)

    def build_advanced_tab(self):
        tab_layout = QVBoxLayout(self.tab_advanced)
        tab_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent;")

        scroll_widget = QWidget()
        layout = QVBoxLayout(scroll_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(14)

        # 1. Crossover ve DSP Frekans Detayları
        self.dsp_group = QGroupBox(_t("dsp_group"))
        dsp_layout = QGridLayout(self.dsp_group)

        # Crossover Frekansı
        self.lbl_crossover = QLabel(_t("lbl_crossover"))
        dsp_layout.addWidget(self.lbl_crossover, 0, 0)
        self.spin_crossover = QSpinBox()
        self.spin_crossover.setRange(1500, 3500)
        self.spin_crossover.setValue(1800)
        self.spin_crossover.setSingleStep(50)
        self.spin_crossover.valueChanged.connect(self.schedule_live_changes)
        dsp_layout.addWidget(self.spin_crossover, 0, 1)

        # Bas Merkez Frekansı
        self.lbl_bass_freq = QLabel(_t("lbl_bass_freq"))
        dsp_layout.addWidget(self.lbl_bass_freq, 1, 0)
        self.spin_bass_freq = QSpinBox()
        self.spin_bass_freq.setRange(60, 200)
        self.spin_bass_freq.setValue(160)
        self.spin_bass_freq.setSingleStep(5)
        self.spin_bass_freq.valueChanged.connect(self.schedule_live_changes)
        dsp_layout.addWidget(self.spin_bass_freq, 1, 1)

        # Vokal Frekansı
        self.lbl_vocal_freq = QLabel(_t("lbl_vocal_freq"))
        dsp_layout.addWidget(self.lbl_vocal_freq, 2, 0)
        self.spin_vocal_freq = QSpinBox()
        self.spin_vocal_freq.setRange(2000, 5000)
        self.spin_vocal_freq.setValue(2500)
        self.spin_vocal_freq.setSingleStep(100)
        self.spin_vocal_freq.valueChanged.connect(self.schedule_live_changes)
        dsp_layout.addWidget(self.spin_vocal_freq, 2, 1)

        # Tiz Frekansı
        self.lbl_treble_freq = QLabel(_t("lbl_treble_freq"))
        dsp_layout.addWidget(self.lbl_treble_freq, 3, 0)
        self.spin_treble_freq = QSpinBox()
        self.spin_treble_freq.setRange(8000, 16000)
        self.spin_treble_freq.setValue(11000)
        self.spin_treble_freq.setSingleStep(500)
        self.spin_treble_freq.valueChanged.connect(self.schedule_live_changes)
        dsp_layout.addWidget(self.spin_treble_freq, 3, 1)

        # Pre-amp Çıkış Güçlendirici
        self.lbl_preamp = QLabel(_t("lbl_preamp"))
        dsp_layout.addWidget(self.lbl_preamp, 4, 0)
        self.spin_preamp = QDoubleSpinBox()
        self.spin_preamp.setRange(0.8, 2.0)
        self.spin_preamp.setValue(1.30)
        self.spin_preamp.setSingleStep(0.05)
        self.spin_preamp.valueChanged.connect(self.schedule_live_changes)
        dsp_layout.addWidget(self.spin_preamp, 4, 1)

        # Her Hz/çarpan değeri için kaydırıcı (SpinBox ile çift yönlü bağlı)
        for row, spin, scale in [
            (0, self.spin_crossover, 1), (1, self.spin_bass_freq, 1),
            (2, self.spin_vocal_freq, 1), (3, self.spin_treble_freq, 1),
            (4, self.spin_preamp, 100),
        ]:
            sl = QSlider(Qt.Orientation.Horizontal)
            sl.setRange(int(round(spin.minimum() * scale)), int(round(spin.maximum() * scale)))
            sl.setValue(int(round(spin.value() * scale)))
            sl.valueChanged.connect(lambda v, s=spin, k=scale: s.setValue(v / k if k != 1 else v))
            spin.valueChanged.connect(lambda v, s=sl, k=scale: s.setValue(int(round(v * k))))
            dsp_layout.addWidget(sl, row, 2)
        dsp_layout.setColumnStretch(2, 1)

        self.btn_reset = QPushButton(_t("btn_reset"))
        self.btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reset.clicked.connect(self.reset_advanced_defaults)
        dsp_layout.addWidget(self.btn_reset, 5, 0, 1, 3)

        layout.addWidget(self.dsp_group)

        # 2. Akustik Donanım Pinleri & Sürücü Durumu
        self.hw_pins_group = QGroupBox(_t("hw_pins_group"))
        hw_pins_layout = QVBoxLayout(self.hw_pins_group)
        hw_pins_layout.setSpacing(10)

        # 2x2 Donanım Kartları
        cards_grid = QGridLayout()
        cards_grid.setHorizontalSpacing(10)
        cards_grid.setVerticalSpacing(10)

        # 1. Tweeter (0x14)
        self.card_tweeter, self.badge_tweeter, self.desc_tweeter = self.create_pin_card(
            _t("card_tw_title"), "Pin 0x14  •  DAC 0x02", _t("card_tw_desc")
        )
        cards_grid.addWidget(self.card_tweeter, 0, 0)

        # 2. Woofer (0x1b)
        self.card_woofer, self.badge_woofer, self.desc_woofer = self.create_pin_card(
            _t("card_wf_title"), "Pin 0x1b  •  DAC 0x03", _t("card_wf_desc")
        )
        cards_grid.addWidget(self.card_woofer, 0, 1)

        # 3. Headphone (0x21)
        self.card_headphone, self.badge_headphone, self.desc_headphone = self.create_pin_card(
            _t("card_hp_title"), "Pin 0x21  •  DAC 0x02", _t("card_hp_desc")
        )
        cards_grid.addWidget(self.card_headphone, 1, 0)

        # 4. Quad DMIC
        self.card_mic, self.badge_mic, self.desc_mic = self.create_pin_card(
            _t("card_mc_title"), "Tiger Lake SOF DSP  •  DMIC", _t("card_mc_desc")
        )
        cards_grid.addWidget(self.card_mic, 1, 1)

        hw_pins_layout.addLayout(cards_grid)

        # Canlandırma & Tarama Kontrol Satırı
        action_row = QHBoxLayout()
        self.btn_reinit_hw = QPushButton(_t("btn_reinit_hw"))
        self.btn_reinit_hw.setProperty("class", "action-btn")
        self.btn_reinit_hw.clicked.connect(self.reinit_hardware)
        action_row.addWidget(self.btn_reinit_hw)

        self.btn_refresh_hw = QPushButton(_t("btn_refresh_hw"))
        self.btn_refresh_hw.setStyleSheet("""
            QPushButton {
                background: #191f2e;
                border: 1px solid #28334a;
                border-radius: 6px;
                padding: 10px 14px;
                color: #e0e6ed;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #222b40;
                border: 1px solid #00d2ff;
                color: #00d2ff;
            }
        """)
        self.btn_refresh_hw.clicked.connect(self.request_hardware_status_refresh)
        action_row.addWidget(self.btn_refresh_hw)

        self.lbl_hw_check_time = QLabel(_t("last_scan_init"))
        self.lbl_hw_check_time.setStyleSheet("color: #8898aa; font-size: 11px;")
        self.lbl_hw_check_time.setWordWrap(True)
        hw_pins_layout.addWidget(self.lbl_hw_check_time)
        action_row.addStretch()

        hw_pins_layout.addLayout(action_row)
        layout.addWidget(self.hw_pins_group)

        # 3. Mikrofon Yönetimi
        self.mic_group = QGroupBox(_t("mic_group"))
        mic_layout = QVBoxLayout(self.mic_group)

        mic_box = QVBoxLayout()
        self.rb_dmic = QRadioButton(_t("rb_dmic"))
        self.rb_rnnoise = QRadioButton(_t("rb_rnnoise"))
        self.rb_dmic.setChecked(True)
        self.rb_dmic.toggled.connect(self.toggle_mic)

        mic_box.addWidget(self.rb_dmic)
        mic_box.addWidget(self.rb_rnnoise)
        mic_layout.addLayout(mic_box)

        layout.addWidget(self.mic_group)

        scroll.setWidget(scroll_widget)
        tab_layout.addWidget(scroll)

    def create_slider_row(self, parent_layout, label_text, min_val, max_val, default_val, unit, factor=1.0):
        h_layout = QHBoxLayout()
        lbl_title = QLabel(label_text)
        lbl_title.setMinimumWidth(240)
        lbl_title.setWordWrap(True)
        lbl_val = QLabel(f"{default_val * factor:.1f} {unit}")
        lbl_val.setStyleSheet("color: #00d2ff; font-weight: bold; font-size: 13px;")
        lbl_val.setFixedWidth(70)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default_val)
        slider.valueChanged.connect(lambda v: lbl_val.setText(f"{v * factor:.1f} {unit}"))

        h_layout.addWidget(lbl_title)
        h_layout.addWidget(slider)
        h_layout.addWidget(lbl_val)
        parent_layout.addLayout(h_layout)
        return slider, lbl_val, lbl_title

    def apply_preset(self, preset):
        """Hazır ses profillerini canlı uygular (sıfır kesinti)"""
        for pid, btn in self.profile_btns.items():
            btn.setProperty("active", "true" if pid == preset else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        if preset == "music":
            self.slider_bass.setValue(55)     # +5.5 dB tok bas
            self.slider_vocal.setValue(15)    # +1.5 dB
            self.slider_treble.setValue(15)   # +1.5 dB
            self.slider_balance.setValue(105)
            self.spin_preamp.setValue(1.30)
        elif preset == "movie":
            self.slider_bass.setValue(65)     # +6.5 dB derin bas
            self.slider_vocal.setValue(25)    # +2.5 dB
            self.slider_treble.setValue(20)   # +2.0 dB
            self.slider_balance.setValue(110)
            self.spin_preamp.setValue(1.35)
        elif preset == "gaming":
            self.slider_bass.setValue(45)     # +4.5 dB
            self.slider_vocal.setValue(30)    # +3.0 dB
            self.slider_treble.setValue(20)   # +2.0 dB
            self.slider_balance.setValue(100)
            self.spin_preamp.setValue(1.25)
        elif preset == "voice":
            self.slider_bass.setValue(25)     # +2.5 dB
            self.slider_vocal.setValue(40)    # +4.0 dB
            self.slider_treble.setValue(15)   # +1.5 dB
            self.slider_balance.setValue(95)
            self.spin_preamp.setValue(1.20)
        elif preset == "balanced":
            self.slider_bass.setValue(45)     # +4.5 dB
            self.slider_vocal.setValue(15)    # +1.5 dB
            self.slider_treble.setValue(15)   # +1.5 dB
            self.slider_balance.setValue(100)
            self.spin_preamp.setValue(1.30)

        self.apply_live_changes(silent=False)

    def apply_live_changes(self, silent=True):
        """Tüm ayarları sıfır kesintiyle canlı olarak PipeWire grafiğine enjekte eder"""
        bass_gain = self.slider_bass.value() * 0.1
        vocal_gain = self.slider_vocal.value() * 0.1
        treble_gain = self.slider_treble.value() * 0.1
        balance_ratio = self.slider_balance.value() / 100.0

        preamp = self.spin_preamp.value()
        preamp_woofer = preamp * balance_ratio
        preamp_tweeter = preamp * (2.0 - balance_ratio) * 0.85

        # Donanım DAC 0x02 (Üst Tiz 0x14) seviyesini balans sürgüsüne göre canlı ayarla
        # %100 balans -> 70 (-12.75 dB), %150 bas ağırlıklı -> 52 (-26.25 dB), %50 tiz ağırlıklı -> 85 (-1.50 dB)
        self.engine.tweeter_step = max(45, min(85, int(round(70 - (balance_ratio - 1.0) * 35))))
        self.engine.ensure_hardware_unmuted()

        self.engine.update_live_dsp(
            bass_gain=bass_gain,
            bass_freq=float(self.spin_bass_freq.value()),
            vocal_gain=vocal_gain,
            vocal_freq=float(self.spin_vocal_freq.value()),
            treble_gain=treble_gain,
            treble_freq=float(self.spin_treble_freq.value()),
            crossover_freq=float(self.spin_crossover.value()),
            preamp_woofer=preamp_woofer,
            preamp_tweeter=preamp_tweeter
        )

        if not silent:
            self.status_box.setText(_t("status_updated"))
            self.status_box.setStyleSheet("""
                background: #003554;
                color: #00d2ff;
                border: 1px solid #00d2ff;
                border-radius: 12px;
                padding: 6px 14px;
                font-weight: bold;
                font-size: 11px;
            """)
            QTimer.singleShot(2500, self.reset_status_box)

    def toggle_language(self):
        """Arayüz dilini canlı olarak TR <-> EN arasında değiştirir ve kaydeder"""
        global CURRENT_LANG
        CURRENT_LANG = "en" if CURRENT_LANG == "tr" else "tr"
        save_lang_pref(CURRENT_LANG)
        self.retranslate_ui()

    def retranslate_ui(self):
        """Pencereyi kapatmadan tüm metinleri yeni dile çevirir"""
        self.btn_lang.setText(f"🌐 {CURRENT_LANG.upper()}")
        self.device_subtitle.setText(_t("subtitle"))
        self.tabs.setTabText(0, _t("tab_dashboard"))
        self.tabs.setTabText(1, _t("tab_advanced"))
        self.out_group.setTitle(_t("out_group"))
        self.profile_group.setTitle(_t("profile_group"))

        for pid, tk, dk in [
            ("music", "prof_music_t", "prof_music_d"),
            ("movie", "prof_movie_t", "prof_movie_d"),
            ("gaming", "prof_gaming_t", "prof_gaming_d"),
            ("voice", "prof_voice_t", "prof_voice_d"),
            ("balanced", "prof_balanced_t", "prof_balanced_d"),
        ]:
            if pid in self.profile_btns:
                self.profile_btns[pid].setText(f"{_t(tk)}\n{_t(dk)}")

        self.sliders_group.setTitle(_t("sliders_group"))
        self.title_bass.setText(_t("sl_bass"))
        self.title_vocal.setText(_t("sl_vocal"))
        self.title_treble.setText(_t("sl_treble"))
        self.title_balance.setText(_t("sl_balance"))

        self.dsp_group.setTitle(_t("dsp_group"))
        self.lbl_crossover.setText(_t("lbl_crossover"))
        self.lbl_bass_freq.setText(_t("lbl_bass_freq"))
        self.lbl_vocal_freq.setText(_t("lbl_vocal_freq"))
        self.lbl_treble_freq.setText(_t("lbl_treble_freq"))
        self.lbl_preamp.setText(_t("lbl_preamp"))
        self.btn_reset.setText(_t("btn_reset"))

        self.hw_pins_group.setTitle(_t("hw_pins_group"))
        self.card_tweeter.lbl_title.setText(_t("card_tw_title"))
        self.card_tweeter.wake_btn.setText(_t("btn_wake_one"))
        self.card_woofer.lbl_title.setText(_t("card_wf_title"))
        self.card_woofer.wake_btn.setText(_t("btn_wake_one"))
        self.card_headphone.lbl_title.setText(_t("card_hp_title"))
        self.card_headphone.wake_btn.setText(_t("btn_wake_one"))
        self.card_mic.lbl_title.setText(_t("card_mc_title"))
        self.card_mic.wake_btn.setText(_t("btn_wake_one"))

        self.btn_reinit_hw.setText(_t("btn_reinit_hw"))
        self.btn_refresh_hw.setText(_t("btn_refresh_hw"))
        self.mic_group.setTitle(_t("mic_group"))
        self.rb_dmic.setText(_t("rb_dmic"))
        self.rb_rnnoise.setText(_t("rb_rnnoise"))

        if hasattr(self, "watcher"):
            st = self.watcher.probe()
            self.current_devices = st.get("devices", [])
            self.current_active_sink = st.get("active_sink")
        self.refresh_output_selectors()
        self.reset_status_box()
        self.request_hardware_status_refresh()

    def on_device_state(self, st):
        """Bağlı çıkış aygıtlarını (PC Hoparlörü, Jabra, Dock, Bluetooth, Kulaklık) arayüz ve sağ tık menüsünde günceller"""
        self.current_devices = st.get("devices", [])
        self.current_active_sink = st.get("active_sink")
        self.refresh_output_selectors()

        active_dev = next((d for d in self.current_devices if d["name"] == self.current_active_sink), None)
        is_external_bt_or_usb = active_dev and active_dev["kind"] in ("bt", "usb")

        if is_external_bt_or_usb and self.saved_before_bt is None:
            self.saved_before_bt = (
                self.slider_bass.value(), self.slider_vocal.value(),
                self.slider_treble.value(), self.slider_balance.value(),
                self.spin_preamp.value()
            )
            self.slider_bass.setValue(20)
            self.slider_vocal.setValue(10)
            self.slider_treble.setValue(10)
            self.slider_balance.setValue(100)
            self.spin_preamp.setValue(1.0)
        elif not is_external_bt_or_usb and self.saved_before_bt is not None:
            b, v, t, bal, pre = self.saved_before_bt
            self.saved_before_bt = None
            self.slider_bass.setValue(b)
            self.slider_vocal.setValue(v)
            self.slider_treble.setValue(t)
            self.slider_balance.setValue(bal)
            self.spin_preamp.setValue(pre)

        self.reset_status_box()
        self.request_hardware_status_refresh()

    def select_output_device(self, sink_name):
        """Kullanıcı sağ tık tepsi menüsünden veya panelden çıkış aygıtı seçtiğinde çağrılır"""
        if hasattr(self, "watcher"):
            self.watcher.select_sink(sink_name)

    def refresh_output_selectors(self):
        """Hem ana penceredeki çıkış butonlarını hem de sağ tık sistem tepsisi menüsünü günceller"""
        if hasattr(self, "out_devices_layout"):
            while self.out_devices_layout.count():
                item = self.out_devices_layout.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()

            for dev in self.current_devices:
                is_active = (dev["name"] == self.current_active_sink)
                prefix = "● " if is_active else "○ "
                btn = QPushButton(f"{prefix}{dev['label']}")
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                if is_active:
                    btn.setStyleSheet(
                        "QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0077b6, stop:1 #00b4d8);"
                        " color: #ffffff; border: 1px solid #00f5d4; border-radius: 7px; padding: 8px 12px; font-weight: bold; font-size: 12px; }"
                    )
                else:
                    btn.setStyleSheet(
                        "QPushButton { background: #1c2230; color: #b0bec5; border: 1px solid #2b3548;"
                        " border-radius: 7px; padding: 8px 12px; font-weight: bold; font-size: 12px; }"
                        "QPushButton:hover { background: #262f42; border: 1px solid #00d2ff; color: #ffffff; }"
                    )
                btn.clicked.connect(lambda checked, s=dev["name"]: self.select_output_device(s))
                self.out_devices_layout.addWidget(btn)

        if hasattr(self, "tray_menu"):
            self.rebuild_tray_menu()

    def shutdown(self):
        self.watcher.requestInterruption()
        self.watcher.wait(4000)

    def reset_status_box(self):
        active_dev = next((d for d in getattr(self, "current_devices", []) if d["name"] == getattr(self, "current_active_sink", None)), None)
        if active_dev:
            self.status_box.setText(_t("status_active_out", dev=active_dev["label"]))
        else:
            self.status_box.setText(_t("status_connected"))
        self.status_box.setStyleSheet("""
            background: #0d2818;
            color: #2ec4b6;
            border: 1px solid #165b33;
            border-radius: 12px;
            padding: 6px 14px;
            font-weight: bold;
            font-size: 11px;
        """)

    def schedule_live_changes(self):
        """Kaydırıcı sürüklenirken pw-cli çağrılarını 80 ms'de bir birleştirir"""
        if not hasattr(self, "_debounce"):
            self._debounce = QTimer(self)
            self._debounce.setSingleShot(True)
            self._debounce.timeout.connect(lambda: self.apply_live_changes(silent=True))
        self._debounce.start(80)

    def reset_advanced_defaults(self):
        self.spin_crossover.setValue(1800)
        self.spin_bass_freq.setValue(160)
        self.spin_vocal_freq.setValue(2500)
        self.spin_treble_freq.setValue(11000)
        self.spin_preamp.setValue(1.30)
        self.apply_live_changes(silent=False)

    def create_pin_card(self, title_text, pin_code, desc_text):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #121622;
                border: 1px solid #1f273a;
                border-radius: 8px;
            }
            QFrame:hover {
                border: 1px solid #00d2ff;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(4)

        top_layout = QHBoxLayout()
        lbl_title = QLabel(title_text)
        lbl_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #ffffff;")
        top_layout.addWidget(lbl_title)
        top_layout.addStretch()

        lbl_badge = QLabel("Taranıyor...")
        lbl_badge.setStyleSheet(self.get_badge_style("badge-idle"))
        top_layout.addWidget(lbl_badge)
        card_layout.addLayout(top_layout)

        lbl_pin = QLabel(pin_code)
        lbl_pin.setStyleSheet("color: #00d2ff; font-size: 11px; font-weight: bold; font-family: monospace;")
        card_layout.addWidget(lbl_pin)

        lbl_desc = QLabel(desc_text)
        lbl_desc.setStyleSheet("color: #8898aa; font-size: 11px;")
        lbl_desc.setWordWrap(True)
        card_layout.addWidget(lbl_desc)

        wake_btn = QPushButton(_t("btn_wake_one"))
        wake_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        wake_btn.setStyleSheet(
            "QPushButton { background:#2b1116; color:#ff5c77; border:1px solid #6b1d28;"
            " border-radius:5px; padding:4px 10px; font-weight:bold; font-size:11px; }"
            "QPushButton:hover { background:#ff5c77; color:#000; }"
        )
        wake_btn.clicked.connect(self.reinit_hardware)
        wake_btn.setVisible(False)
        card_layout.addWidget(wake_btn)
        card.wake_btn = wake_btn
        card.lbl_title = lbl_title

        return card, lbl_badge, lbl_desc

    def get_badge_style(self, badge_class):
        if badge_class == "badge-active":
            return """
                background: #0d2818;
                color: #2ec4b6;
                border: 1px solid #165b33;
                border-radius: 6px;
                padding: 3px 8px;
                font-weight: bold;
                font-size: 11px;
            """
        elif badge_class == "badge-inactive":
            return """
                background: #2b1116;
                color: #ff5c77;
                border: 1px solid #6b1d28;
                border-radius: 6px;
                padding: 3px 8px;
                font-weight: bold;
                font-size: 11px;
            """
        elif badge_class == "badge-plugged":
            return """
                background: #002b4d;
                color: #00b4d8;
                border: 1px solid #0077b6;
                border-radius: 6px;
                padding: 3px 8px;
                font-weight: bold;
                font-size: 11px;
            """
        else: # idle
            return """
                background: #141a29;
                color: #8898aa;
                border: 1px solid #232d42;
                border-radius: 6px;
                padding: 3px 8px;
                font-weight: bold;
                font-size: 11px;
            """

    def on_tab_changed(self, index):
        if index == 1:
            self.request_hardware_status_refresh()

    def request_hardware_status_refresh(self):
        if hasattr(self, "hw_worker") and not self.hw_worker.isRunning():
            self.hw_worker.start()

    def on_hardware_status_updated(self, status):
        now_str = datetime.now().strftime("%H:%M:%S")

        # Tweeter
        tw = status.get("tweeter", {})
        if hasattr(self, "badge_tweeter"):
            self.badge_tweeter.setText(tw.get("status", "Bilinmiyor"))
            self.badge_tweeter.setStyleSheet(self.get_badge_style(tw.get("badge_class", "badge-idle")))
            if "desc" in tw and tw["desc"]:
                self.desc_tweeter.setText(tw["desc"])
            self.card_tweeter.wake_btn.setVisible(not tw.get("active", False))

        # Woofer
        wf = status.get("woofer", {})
        if hasattr(self, "badge_woofer"):
            self.badge_woofer.setText(wf.get("status", "Bilinmiyor"))
            self.badge_woofer.setStyleSheet(self.get_badge_style(wf.get("badge_class", "badge-idle")))
            if "desc" in wf and wf["desc"]:
                self.desc_woofer.setText(wf["desc"])
            self.card_woofer.wake_btn.setVisible(not wf.get("active", False))

        # Headphone
        hp = status.get("headphone", {})
        if hasattr(self, "badge_headphone"):
            self.badge_headphone.setText(hp.get("status", "Bilinmiyor"))
            self.badge_headphone.setStyleSheet(self.get_badge_style(hp.get("badge_class", "badge-idle")))
            if "desc" in hp and hp["desc"]:
                self.desc_headphone.setText(hp["desc"])

        # Mic
        mc = status.get("mic", {})
        if hasattr(self, "badge_mic"):
            if hasattr(self, "rb_rnnoise") and self.rb_rnnoise.isChecked():
                self.badge_mic.setText(_t("mic_rnnoise_active"))
                self.badge_mic.setStyleSheet(self.get_badge_style("badge-plugged"))
                self.desc_mic.setText(_t("mic_rnnoise_desc"))
            else:
                self.badge_mic.setText(_t("mic_active"))
                self.badge_mic.setStyleSheet(self.get_badge_style(mc.get("badge_class", "badge-active")))
                self.desc_mic.setText(_t("card_mc_desc"))

        if hasattr(self, "lbl_hw_check_time"):
            all_ok = tw.get("active", False) and wf.get("active", False)
            status_txt = _t("all_spk_ok") if all_ok else _t("some_pins_sleep")
            self.lbl_hw_check_time.setText(_t("last_scan_fmt", time=now_str, state=status_txt))

        # Tiz hoparlör pasifleşmişse veya Bas hoparlör yanlış DAC'ta (0x02*) kalmışsa otomatik iyileştir (Auto-heal)
        hp = status.get("headphone", {})
        import time
        now = time.time()
        if (not tw.get("active", False) or not wf.get("active", False)) and not hp.get("active", False):
            if now - getattr(self, "last_auto_heal", 0) > 10:
                self.last_auto_heal = now
                self.reinit_hardware(silent=True)

    def toggle_mic(self):
        """Mikrofon kaynağını dikteyi kesmeden ayarlar"""
        try:
            if self.rb_dmic.isChecked():
                subprocess.run(["pactl", "set-default-source",
                                "alsa_input.pci-0000_00_1f.3-platform-skl_hda_dsp_generic.HiFi__Mic1__source"],
                               check=False)
            else:
                subprocess.run(["pactl", "set-default-source", "matebook_mic_rnnoise"], check=False)
        except Exception as e:
            print(f"Mic toggle error: {e}")
        self.request_hardware_status_refresh()

    def reinit_hardware(self, silent=False):
        """Donanım pinlerini canlı yeniden uyandırır (yalnızca root sahipli kurulu betik)"""
        script = SECURE_SCRIPT
        if script.exists() and script.stat().st_uid == 0 and not (script.stat().st_mode & 0o022):
            if hasattr(self, "lbl_hw_check_time") and not silent:
                self.lbl_hw_check_time.setText(_t("waking_pins"))
            try:
                subprocess.Popen(["pkexec", str(script)],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
        elif hasattr(self, "lbl_hw_check_time") and not silent:
            self.lbl_hw_check_time.setText(_t("missing_script"))
        self.engine.ensure_hardware_unmuted(force_dac_sync=True)
        QTimer.singleShot(1200, lambda: self.engine.ensure_hardware_unmuted(force_dac_sync=True))
        QTimer.singleShot(1500, self.request_hardware_status_refresh)

    def init_tray(self):
        """KDE Plasma 6 Wayland uyumlu StatusNotifierItem sistem tepsisi (MateSound Studio)"""
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.app_icon)
        self.tray.setToolTip("MateSound Studio - Huawei MateBook X Pro")

        self.tray_menu = QMenu()
        self.tray_menu.setStyleSheet("""
            QMenu {
                background: #141824;
                color: #ffffff;
                border: 1px solid #28334a;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item:selected {
                background: #0077b6;
                color: white;
            }
            QMenu::item:disabled {
                color: #00f5d4;
                font-weight: bold;
            }
        """)
        self.rebuild_tray_menu()
        self.tray.setContextMenu(self.tray_menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

    def rebuild_tray_menu(self):
        """Sağ tık sistem tepsisi menüsünü bağlı ses aygıtları ve profillerle canlı oluşturur"""
        self.tray_menu.clear()

        act_show = QAction(_t("tray_open"), self)
        act_show.triggered.connect(self.showNormal)
        self.tray_menu.addAction(act_show)

        self.tray_menu.addSeparator()
        hdr_out = QAction(_t("tray_out_hdr"), self)
        hdr_out.setEnabled(False)
        self.tray_menu.addAction(hdr_out)

        devices = getattr(self, "current_devices", [])
        if not devices:
            act_none = QAction(f"   ({_t('scanning_devs')})", self)
            act_none.setEnabled(False)
            self.tray_menu.addAction(act_none)
        else:
            for dev in devices:
                is_active = (dev["name"] == getattr(self, "current_active_sink", None))
                mark = "●" if is_active else "○"
                act_dev = QAction(f"{mark}  {dev['label']}", self)
                act_dev.triggered.connect(lambda checked, s=dev["name"]: self.select_output_device(s))
                self.tray_menu.addAction(act_dev)

        self.tray_menu.addSeparator()
        hdr_prof = QAction(_t("tray_prof_hdr"), self)
        hdr_prof.setEnabled(False)
        self.tray_menu.addAction(hdr_prof)

        for pid, tk in [
            ("music", "prof_music_t"),
            ("movie", "prof_movie_t"),
            ("gaming", "prof_gaming_t"),
            ("voice", "prof_voice_t"),
            ("balanced", "prof_balanced_t"),
        ]:
            act = QAction(f"   {_t(tk)}", self)
            act.triggered.connect(lambda checked, p=pid: self.apply_preset(p))
            self.tray_menu.addAction(act)

        self.tray_menu.addSeparator()
        act_lang = QAction(_t("tray_lang"), self)
        act_lang.triggered.connect(self.toggle_language)
        self.tray_menu.addAction(act_lang)

        act_quit = QAction(_t("tray_quit"), self)
        act_quit.triggered.connect(QApplication.instance().quit)
        self.tray_menu.addAction(act_quit)

    def on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            if self.isVisible():
                self.hide()
            else:
                self.showNormal()
                self.activateWindow()

    def closeEvent(self, event):
        """Pencere kapatıldığında sistem tepsisine gizlenir"""
        event.ignore()
        self.hide()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    if LOGO_PATH.exists():
        app_icon = QIcon(str(LOGO_PATH))
    else:
        app_icon = QIcon.fromTheme("audio-speakers")
    app.setWindowIcon(app_icon)

    window = NahimicWindow()
    app.aboutToQuit.connect(window.shutdown)
    if "--minimized" not in sys.argv and "--tray" not in sys.argv:
        window.show()
    sys.exit(app.exec())
