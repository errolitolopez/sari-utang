# Pag-setup sa Windows (Setting up on Windows)

Para sa computer sa tindahan. Ang computer ang "server": dito nakatira ang listahan,
at bubuksan ito sa phone gamit ang parehong Wi-Fi.

*For the store's computer. The computer keeps the data; phones on the same Wi-Fi open the app.*

---

## 1. I-install ang Python at Git (isang beses lang)

**Python**
1. Buksan ang <https://www.python.org/downloads/> at i-download ang **Python 3** (yung malaking dilaw na button).
2. Patakbuhin ang installer. Sa unang screen, **i-check ang "Add python.exe to PATH"** ✅, tapos **Install Now**.

**Git**
1. Buksan ang <https://git-scm.com/download/win> at i-download ang **Git for Windows**.
2. Patakbuhin ang installer. Puwedeng **Next** lang nang Next (okay ang mga default).

> Kailangan ng internet dito at sa unang takbo ng app. Pagkatapos noon, gumagana na kahit walang internet
> (internet lang ang kailangan para sa auto-update, at sa unang beses na bubuksan sa bawat phone).

## 2. Kunin ang app mula sa GitHub

Buksan ang **Command Prompt** (Start → i-type `cmd`) at patakbuhin:

```bat
cd C:\
git clone https://github.com/errolitolopez/sari-utang.git SariUtang
```

Ang app ay nasa **`C:\SariUtang`** na. Hindi kailangan ng GitHub account sa laptop (public ang repository).

## 3. Patakbuhin (unang beses)

1. Buksan ang folder na **`C:\SariUtang`** at i-double-click ang **`run.bat`**.
   - Kung lumabas ang *"Windows protected your PC"*: **More info → Run anyway**.
2. Maghintay habang nag-iinstall (unang beses lang, 1–2 minuto).
3. Itatanong ang **PIN** (4 hanggang 6 na numero). Ilagay ang PIN ng ate mo.
   Kapag Enter lang, magiging **0000** — palitan agad gamit ang `change-pin.bat`.
4. Kapag lumabas ang *Windows Security / Firewall* na tanong: i-check ang **Private networks** at **Allow access**.
5. Lalabas ang ganito — **huwag isara ang window** habang ginagamit:

   ```
   Sari Utang is running. Keep this window open.

     On this computer:  http://127.0.0.1:5000
     On your phone:     http://192.168.1.17:5000
   ```

6. Ilagay ang pangalan ng tindahan: buksan ang **`C:\SariUtang\config\settings.json`** sa Notepad
   (nagagawa ito sa unang takbo), palitan ang `"Sari-Sari Store"`, at i-save.

## 4. Buksan sa phone

1. Siguraduhing nasa **parehong Wi-Fi** ang phone at computer (hindi mobile data).
2. Sa Chrome ng phone, buksan ang address na nakalagay sa *On your phone* (hal. `http://192.168.1.17:5000`).
3. Mag-login gamit ang PIN.
4. Chrome menu (⋮) → **Add to Home screen** para may icon na parang app.

**Hindi bumubukas sa phone?**
- Sa computer: *Settings → Network & Internet → Wi-Fi → (pangalan ng Wi-Fi)* → **Network profile: Private**.
- Patakbuhin ulit ang `run.bat` at piliin ang **Allow access** sa Firewall.
- Kung nag-restart ang router, puwedeng magbago ang address — tingnan ulit ang window ng Sari Utang.
  (Para hindi na magbago: sa settings ng router, mag-set ng *DHCP reservation / static IP* para sa computer.)

## 5. Desktop icon at auto-start (walang itim na window)

Pagkatapos ma-set ang PIN sa `run.bat`, **isara na ang window na iyon** at gamitin ang mga ito:

1. I-double-click ang **`create-shortcuts.bat`**. Magkakaroon ng 2 icon sa Desktop:
   - **Sari Utang** — magsisimula ang app **sa background** (walang itim na window) at bubuksan sa browser.
     Kung tumatakbo na, bubuksan lang ang browser.
   - **Stop Sari Utang** — ihihinto ang app.
2. I-double-click ang **`install-autostart.bat`** para kusang magsimula (sa background din) pag in-on ang computer.
   Para tanggalin: **`remove-autostart.bat`**.
3. Para hindi mag-sleep ang computer habang bukas ang tindahan:
   *Settings → System → Power → Screen and sleep → "When plugged in, put my device to sleep after": **Never***.

> Dahil walang window sa background, ang address para sa phone at mga mensahe ay nasa
> **`logs\sari-utang.log`** (buksan sa Notepad). Kung may problema, patakbuhin ang `run.bat` para makita ang window.

## 6. Mga dapat tandaan

| Gusto mong… | Gawin |
|---|---|
| Palitan ang PIN | I-double-click ang `change-pin.bat` |
| Palitan ang pangalan ng tindahan (sa invoice) | Buksan ang `config\settings.json` sa Notepad, palitan ang `"store_name"`, i-save, i-refresh ang page |
| Magdagdag ng unit (hal. "tali") | `config\units.json` sa Notepad |
| Buksan ang app | Desktop icon **Sari Utang** |
| Ihinto ang app | Desktop icon **Stop Sari Utang** (o isara ang window kung `run.bat` ang ginamit) |
| Makita ang address para sa phone | Buksan ang `logs\sari-utang.log`, o patakbuhin ang `run.bat` |

### Backup

- Tuwing magsisimula ang app, may kopya ang listahan sa folder na **`backups`** (huling 30 ang tinatago).
- Mga isang beses kada linggo, **kopyahin ang `backups` folder** sa USB o Google Drive, para ligtas kahit masira ang computer.
- **Para ibalik ang backup:** ihinto ang Sari Utang (**Stop Sari Utang**) → kopyahin ang napiling file mula sa `backups` papunta sa
  `instance\sari_utang.db` (palitan ang luma) → patakbuhin ulit ang `run.bat`.

### Pag-update ng app (automatic)

**Kusa itong nag-a-update** — walang kailangang gawin sa laptop:
- tuwing magsisimula ang app, at
- bawat 6 na oras habang tumatakbo,

kinukuha nito ang bagong version mula sa GitHub (`git pull`) at nagre-restart nang mag-isa.
Kung may bagong packages, kusa ring ini-install. Hindi nagagalaw ang listahan ng utang (`instance\`) at `backups\`.

Hindi mag-a-update (at tuloy lang ang lumang version) kung:
- **walang internet** — susubukan ulit sa susunod;
- **may binagong file ng app mismo** (hal. `app.py`) na binago rin sa bagong version.
  Para ayusin: sa Command Prompt, `cd C:\SariUtang` tapos `git checkout .`

Makikita ang dahilan sa `logs\sari-utang.log`.

> Ligtas baguhin ang `config\settings.json` at `config\units.json`: kopya ito ng tindahan
> (ginagawa sa unang takbo mula sa `*.example.json`), kaya hindi nito napipigilan ang update.

**Manual na pag-update** (kung ayaw maghintay):

```bat
cd C:\SariUtang
git pull
```

Tapos **Stop Sari Utang** → **Sari Utang**.

Para patayin ang auto-update: sa `config\settings.json`, gawing `"auto_update": false`.
