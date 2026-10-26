FOOTRATE — telepítés Windows 11-en
=================================

MIT TUD?
- Regisztráció és bejelentkezés felhasználónévvel/jelszóval.
- Közös képgaléria.
- Saját kép feltöltése (JPG/PNG/WEBP, maximum 5 MB).
- 1–10-es értékelés, átlagpontszám.
- A saját képedet nem tudod értékelni; ezt a szerver is ellenőrzi.
- Egy felhasználó egy képet egyszer értékelhet, de később módosíthatja.
- A felhasználók csak a saját képüket törölhetik. A beállított adminfiók bármelyik képet törölheti moderálás céljából.


ADMIN JOG — CSAK A TE FIÓKODNAK
================================
Az adminisztrátort a FOOTRATE_ADMIN_USERNAME környezeti változóval lehet beállítani.
Fontos: először regisztráld a saját fiókodat, és csak utána tedd elérhetővé az oldalt
másoknak. A tárhelyen a környezeti változó értéke pontosan a te felhasználóneved legyen.
Például, ha a felhasználóneved AxelBat, az érték: AxelBat.

Windows helyi teszthez ugyanabban a parancssorban, a szerver indítása előtt:
    set FOOTRATE_ADMIN_USERNAME=AxelBat
    python app.py
(AxelBat helyére a saját felhasználónevedet írd.)

Internetes tárhelyen a tárhely beállításainál add hozzá a FOOTRATE_ADMIN_USERNAME
környezeti változót a saját felhasználóneveddel. A jelszavadat ne írd a kódba,
és ne add oda másnak. Az admin címke és a mások képein megjelenő admin-törlés gomb
csak a beállított felhasználónévvel bejelentkezett fióknál jelenik meg. A szerver is
ellenőrzi a jogosultságot, tehát a gomb elrejtése önmagában nem védelem.

1. TELEPÍTSD A PYTHONT
Python 3.11 vagy 3.12 ajánlott: https://www.python.org/downloads/
Telepítéskor jelöld be az "Add Python to PATH" lehetőséget.

2. NYISD MEG A PROJEKT MAPPÁJÁT
Csomagold ki a ZIP-et például az Asztalra, majd nyisd meg a FootRate mappát.

3. NYISS TERMINÁLT A MAPPA HELYÉN
A Fájlkezelő címsorába írd: cmd
Nyomj Entert.

4. HOZD LÉTRE A VIRTUÁLIS KÖRNYEZETET ÉS TELEPÍTSD A CSOMAGOKAT
Windows parancssorban futtasd egymás után:

    py -m venv .venv
    .venv\Scripts\activate
    python -m pip install --upgrade pip
    pip install -r requirements.txt

Ha a "py" parancs nem működik, próbáld a "python" parancsot.

5. INDÍTSD EL
    python app.py

6. NYISD MEG
A böngészőben nyisd meg:
    http://127.0.0.1:5000

Regisztrálj egy fiókot. A barátaid is regisztrálhatnak ugyanazon a szerveren.

FONTOS: EZ MÉG CSAK HELYI TESZT
A 127.0.0.1 címet csak a saját számítógéped éri el. A barátaid nem tudnak
csak úgy ezen a címen csatlakozni. A valódi internetes használathoz HTTPS-es
tárhely, tartós fájltárolás és megfelelő adatbázis kell. Ne töltsd fel
nyilvánosan érzékeny képekkel, és ne osszátok meg a jelszavaitokat.

ÉLESÍTÉS ELŐTT:
- Állíts be tartós, titkos FOOTRATE_SECRET_KEY környezeti változót.
- Használj HTTPS-t és tartós, biztonságos adatbázist/tárhelyet.
- Legyen képtörlési és jelentési lehetőség, valamint moderálás.
- Csak olyan képet tölts fel, amelyet szabad megosztanod; más személy képéhez
  kérj engedélyt. Ne jelenjen meg név, arc, iskola vagy más személyes adat.


MOBILOS HASZNÁLAT
=================
A felület reszponzív, Androidon és iPhone-on is használható böngészőből.
Ha HTTPS-es tárhelyre telepítetted:
- Android/Chrome: menü (⋮) -> "Alkalmazás telepítése" vagy "Hozzáadás a kezdőképernyőhöz".
- iPhone/Safari: Megosztás -> "Főképernyőhöz adás".

A kezdőképernyős ikon PWA-manifestet használ. Ez nem teszi a szervert
önállóvá: az oldal interneten való eléréséhez továbbra is éles tárhely szükséges.
