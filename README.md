# WeNeed Shopping List for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/default)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2023.11+-blue.svg)](https://www.home-assistant.io/)

A Home Assistant custom integration that connects [WeNeed](https://app.weneed.ch) (by Coop Switzerland) to Home Assistant's native **To-do List (`todo`)** platform.

Integrates seamlessly with **Home Assistant Assist**, **Alexa**, and **Google Assistant** for complete voice control.

---

## ✨ Features

- 🎙️ **Full Voice Assistant Support:** Add, check off, and remove items via voice commands.
- 🔍 **Automatic List Discovery:** Automatically detects all shopping lists associated with your account.
- 📱 **Two-Way Sync:** Works with Home Assistant's sidebar To-do Lists and dashboard cards.
- ⚙️ **Config Flow UI:** Easy setup directly in Home Assistant (Settings > Devices & Services).
- 🔄 **Auto-Refreshing Auth:** Automatically handles Firebase token renewals in the background.

---

## 📦 Installation via HACS
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?category=integration&repository=ha.weneed&owner=Luderas)

1. Open **HACS** in your Home Assistant.
2. Click the **3 dots** (top right corner) and select **Custom repositories**.
3. Add your repository URL:
   ```
   https://github.com/Luderas/ha-weneed
   ```
4. Set Type to **Integration** and click **Add**.
5. Find **WeNeed Shopping List** in HACS and click **Download**.
6. **Restart Home Assistant**.

---

## ⚙️ Setup

1. In Home Assistant, navigate to **Settings > Devices & Services**.
2. Click **Add Integration** and search for **WeNeed Shopping List**.
3. Enter your WeNeed credentials:
   - **Email:** Your WeNeed account email.
   - **Password:** Your WeNeed account password.
4. If you have multiple lists, select the one you want to link from the dropdown.
5. Click **Submit**.

---

## 🗣️ Voice Assistant Commands

Once set up, your Home Assistant Voice Assistant (Assist / ESP32 voice satellites / Alexa / Google Assistant) will respond to:

### Deutsch 🇩🇪 / 🇨🇭
- *"Füge Milch zur Einkaufsliste hinzu"*
- *"Setze Bananen auf die Einkaufsliste"*
- *"Hake Butter auf der Einkaufsliste ab"*
- *"Lösche Tomaten von der Einkaufsliste"*
- *"Was steht auf meiner Einkaufsliste?"*

### English 🇬🇧 / 🇺🇸
- *"Add milk to my shopping list"*
- *"Put bananas on the shopping list"*
- *"Complete butter on the shopping list"*
- *"Delete tomatoes from the shopping list"*
- *"What is on my shopping list?"*
