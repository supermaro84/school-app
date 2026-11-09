# Instrukcja obsługi platformy szkolnej

Platforma służy do komunikacji i organizacji życia szkoły: ogłoszeń, kalendarza zajęć i wydarzeń, wiadomości, grup klasowych, zdjęć, dokumentów oraz szkolnej biblioteki.

Ta instrukcja nie opisuje krok po kroku, gdzie kliknąć, bo interfejs jest prosty. Wyjaśnia za to:

- do czego służy każda funkcja i do czego jej **nie** używać,
- co można wprowadzić i jakie są ograniczenia,
- kto co widzi i kto może co zmieniać,
- jak z platformy korzystają poszczególne grupy użytkowników,
- przykładowe scenariusze i sytuacje brzegowe.

---

## Spis treści

1. [Pierwsze kroki](#1-pierwsze-kroki)
2. [Najważniejsze pojęcia](#2-najważniejsze-pojęcia)
3. [Opis funkcji](#3-opis-funkcji)
   - [3.1 Strona główna](#31-strona-główna)
   - [3.2 Kalendarz i wydarzenia](#32-kalendarz-i-wydarzenia)
   - [3.3 Ogłoszenia](#33-ogłoszenia)
   - [3.4 Wiadomości](#34-wiadomości)
   - [3.5 Grupy](#35-grupy)
   - [3.6 Użytkownicy i profil](#36-użytkownicy-i-profil)
   - [3.7 Media: galerie i zdjęcia](#37-media-galerie-i-zdjęcia)
   - [3.8 Dokumenty](#38-dokumenty)
   - [3.9 Inwentarz (biblioteka)](#39-inwentarz-biblioteka)
   - [3.10 Powiadomienia, sortowanie, język i wygląd](#310-powiadomienia-sortowanie-język-i-wygląd)
4. [Instrukcje dla grup użytkowników](#4-instrukcje-dla-grup-użytkowników)
5. [Przykładowe scenariusze (use case'y)](#5-przykładowe-scenariusze-use-casey)
6. [Warunki brzegowe i ograniczenia](#6-warunki-brzegowe-i-ograniczenia)
7. [Dobre praktyki](#7-dobre-praktyki)

---

## 1. Pierwsze kroki

### Konto i logowanie

- **Nie ma samodzielnej rejestracji.** Konta zakłada szkoła: importem listy uczniów, rodziców i nauczycieli albo ręcznie w panelu administracyjnym. Jeśli nie masz konta, zgłoś się do sekretariatu lub administratora.
- **Login** to zwykle `imie.nazwisko` (nauczyciele) albo `imie_nazwisko` (uczniowie i rodzice), bez polskich znaków.
- **Hasło tymczasowe przy pierwszym logowaniu jest takie samo jak login.** Platforma od razu wymaga jego zmiany. Dopóki hasło nie zostanie zmienione, każda strona przekierowuje do formularza zmiany hasła.
- **Nowe hasło** musi mieć co najmniej 4 znaki i nie może być podobne do loginu, imienia, nazwiska ani adresu e-mail. Zalecamy dłuższe hasło (co najmniej 10 znaków).
- **Zapomniane hasło** można zresetować linkiem wysyłanym na adres e-mail przypisany do konta. Jeśli konto nie ma adresu e-mail, hasło resetuje administrator.

### Język i wygląd

- **Język** interfejsu: polski, angielski lub norweski. Zmiana działa od razu.
- **Treści wpisane przez ludzi nie są tłumaczone.** Ogłoszenia, nazwy grup, role, typy wydarzeń itp. wyświetlają się tak, jak zostały wpisane.
- **Motyw**: jasny, ciemny lub systemowy (zgodny z ustawieniami urządzenia). Wybór zapamiętuje przeglądarka.
- **Urządzenia:** platforma działa na telefonie, tablecie i komputerze. Na małym ekranie listy i szczegóły wyświetlają się osobno.

---

## 2. Najważniejsze pojęcia

| Pojęcie | Co oznacza |
|---|---|
| **Rola** | Administrator, Nauczyciel, Uczeń albo Opiekun. Rola jest **etykietą informacyjną**: widać ją przy nazwisku i można według niej filtrować listę użytkowników. **Sama rola nie nadaje ani nie odbiera uprawnień.** |
| **Administrator grupy** | Osoba, która zarządza daną grupą: zmienia jej opis, członków i administratorów. Grupa klasowa ma zwykle jako administratorów wychowawcę i jednego rodzica. |
| **Członek grupy** | Osoba w grupie. Dostaje ogłoszenia i wydarzenia skierowane do tej grupy. |
| **Właściciel / autor** | Osoba, która utworzyła ogłoszenie, wydarzenie, galerię lub przedmiot w inwentarzu. Tylko ona może je edytować i usuwać. |
| **Osoby powiązane** | Powiązanie rodzic → dziecko. Rodzic widzi to, co widzi jego dziecko: ogłoszenia, wydarzenia, galerie i dokumenty. **Nie widzi wiadomości prywatnych dziecka.** Powiązania ustawia administrator. |
| **Panel administracyjny** | Osobny panel (`/admin/`) dla osób z uprawnieniami technicznymi, np. do zakładania kont czy nadawania ról. Zwykli użytkownicy z niego nie korzystają. |

> **Ważne:** ponieważ role nie ograniczają uprawnień, technicznie każdy zalogowany użytkownik może utworzyć grupę, ogłoszenie, wydarzenie czy galerię. O tym, kto z czego korzysta, decydują **zasady szkoły** opisane w rozdziale 4.

---

## 3. Opis funkcji

### 3.1 Strona główna

**Do czego służy:** szybki podgląd najbliższych wydarzeń (na 2 dni do przodu).

- **Rodzic** widzi osobną zakładkę dla siebie i dla każdego dziecka, z liczbą wydarzeń przy każdej osobie.
- Strona niczego nie edytuje. To tylko podgląd, a pełne informacje są w Kalendarzu.

**Nie służy do:** sprawdzania planu na cały tydzień czy miesiąc. Do tego jest Kalendarz.

---

### 3.2 Kalendarz i wydarzenia

**Do czego służy:** lekcje, zebrania, wycieczki, dni wolne, uroczystości i każde inne zdarzenie z datą i godziną.

**Co widzisz:** wydarzenia, w których bierzesz udział: przypisane do Ciebie lub do Twojej grupy. Rodzic widzi też wydarzenia swoich dzieci, z loginem dziecka w nawiasie przy tytule, np. „Język polski – Klasa 2A (nadia_adamska)”.

**Co można wprowadzić:**

| Pole | Opis |
|---|---|
| Nazwa | Krótka i jednoznaczna, np. „Wycieczka do Muzeum Fram – 4A”. Maks. 200 znaków. |
| Opis | Szczegóły: miejsce, co zabrać, kontakt. |
| Początek | Data i godzina. |
| Czas trwania | Godziny (0–23) i minuty (0–59). |
| Typ | Np. Lekcja, Spotkanie, Edukacyjne, Integracyjne, Dzień wolny, Administracyjne, Inne. |
| Status | Aktywne, Wstępne (termin do potwierdzenia), Odwołane, Zakończone. |
| Grupy i/lub osoby | **Co najmniej jedno** z dwóch. Autor zawsze jest uczestnikiem. |
| Dokumenty | Np. zgoda na wycieczkę, regulamin (patrz 3.8). |

**Kto może zmieniać:** tylko autor wydarzenia. Może je edytować (także dodawać i usuwać dokumenty) albo usunąć.

**Dobre użycie:**
- **Odwołanie:** gdy wydarzenie jest odwołane, **zmień status na „Odwołane”** zamiast je usuwać. Uczestnicy zobaczą, że się nie odbędzie.
- **Niepewny termin:** użyj statusu „Wstępne”.

**Nie używaj do:**
- długich komunikatów bez daty (do tego jest Ogłoszenie),
- rozmów z rodzicami (do tego są Wiadomości),
- wydarzeń wielodniowych w jednym wpisie. Czas trwania to maks. 23 h 59 min, więc np. kolonie wpisz jako osobne dni albo jako wydarzenie na pierwszy dzień z opisem całości.

**Lekcje cykliczne** (plan lekcji) wprowadza administrator importem. W aplikacji nie ma opcji „powtarzaj co tydzień”.

---

### 3.3 Ogłoszenia

**Do czego służy:** informacje do przeczytania przez grupę lub wybrane osoby, np. zmiany organizacyjne, przypomnienia, prośby do rodziców, gratulacje.

**Co można wprowadzić:**

| Pole | Opis |
|---|---|
| Tytuł | Maks. 200 znaków. |
| Treść | Tekst z formatowaniem (pogrubienia, listy, linki). |
| Grupy i/lub osoby | **Co najmniej jedno.** Ogłoszenie dla całej szkoły wymaga wskazania wszystkich grup. |
| Data wygaśnięcia | Opcjonalna. Po tej dacie ogłoszenie dostaje oznaczenie „wygasłe”, ale **nie znika**. |
| Zdjęcia | Do 10 na ogłoszenie. |
| Dokumenty | Do 10, każdy do 20 MB. |

**Kto co widzi:**
- **Odbiorcy:** członkowie i administratorzy wskazanych grup, wskazane osoby oraz rodzice tych osób.
- **Autor** widzi, **kto już przeczytał** ogłoszenie (i kiedy), a kto jeszcze nie. Pozostali widzą tylko listę odbiorców.

**Komentarze:**
- Każdy odbiorca może dodać komentarz (maks. 500 znaków).
- **Komentarzy nie da się edytować ani usunąć.** Pisz je rozważnie.

**Kto może zmieniać:** autor. Może edytować treść, odbiorców, zdjęcia i dokumenty albo usunąć ogłoszenie razem z komentarzami.

**Nie używaj do:**
- spraw jednego ucznia czy rodziny: do tego są Wiadomości, a komentarze widzą wszyscy odbiorcy,
- terminów, które powinny być w kalendarzu. Wydarzenie z datą dodaj do Kalendarza, a w ogłoszeniu najwyżej o nim przypomnij.

---

### 3.4 Wiadomości

**Do czego służy:** prywatna korespondencja między konkretnymi osobami, np. rodzic ↔ wychowawca czy nauczyciel ↔ kilkoro rodziców.

**Co można wprowadzić:**

| Pole | Opis |
|---|---|
| Tytuł wątku | Maks. 150 znaków. |
| Odbiorcy | **Tylko konkretne osoby** (nie grupy). Można wybrać wiele osób. |
| Treść | Maks. 1500 znaków na wiadomość. |
| Zdjęcia / dokumenty | Jak w ogłoszeniach. |

**Zasady:**
- **Kto widzi i odpowiada:** wątek widzą i odpowiadają w nim wyłącznie autor i wybrani odbiorcy.
- **Rodzic nie widzi wiadomości dziecka.** Powiązanie rodzic → dziecko nie obejmuje wiadomości.
- **Odbiorców nie można zmienić** po utworzeniu wątku. Jeśli trzeba kogoś dołączyć, załóż nowy wątek.
- **Wiadomości nie da się edytować ani usunąć.**

**Nie używaj do:** komunikatów dla całej klasy. Wiadomość do 25 osób to 25 osób w jednym wątku, a każda odpowiedź trafia do wszystkich. Do tego służy Ogłoszenie.

---

### 3.5 Grupy

**Do czego służy:** zbiory osób, do których kieruje się ogłoszenia, wydarzenia i galerie. Typowe grupy to klasa (np. „Klasa 4A”), rodzice klasy („Rodzice klasy 4A”), grono pedagogiczne, zajęcia dodatkowe czy rada rodziców.

**Co widzisz:** domyślnie grupy, do których należysz Ty i Twoje dzieci. Możesz też przełączyć widok na wszystkie grupy.

- **Profil z listy:** kliknięcie osoby na liście członków otwiera jej profil, a przy każdym nazwisku widać rolę.

**Tworzenie grupy:**
- **Nazwa** jest unikalna bez względu na wielkość liter („klasa 4a” = „Klasa 4A”). Maks. 150 znaków.
- **Autor** grupy zawsze zostaje jej administratorem.
- **Kopiowanie członków z innych grup:** opcja „Dodaj członków z grup” kopiuje wszystkich członków i administratorów wskazanych grup, np. tworząc „Wycieczka 4A+4B” z klas 4A i 4B. To **jednorazowa kopia**: późniejsze zmiany w grupie źródłowej nie przenoszą się automatycznie.

**Edycja (tylko administratorzy grupy):**
- **Zakres zmian:** opis, administratorzy i członkowie.
- **Co najmniej jeden administrator** musi zostać w grupie.
- **Administrator nie jest jednocześnie zwykłym członkiem.** Jeśli ktoś jest na obu listach, zostaje tylko administratorem.
- **Usuwanie grupy:** w aplikacji nie da się usunąć grupy. Robi to administrator platformy.

**Nie używaj do:** grup „na jedną wiadomość”. Do rozmowy z kilkoma osobami wystarczy wątek w Wiadomościach.

---

### 3.6 Użytkownicy i profil

**Lista użytkowników:**
- Każdy zalogowany widzi wszystkich użytkowników: imię, nazwisko, login, rolę, e-mail, telefon, opis i osoby powiązane.
- Można szukać po imieniu, nazwisku, loginie i e-mailu, a także filtrować po roli.

**Własny profil** (edytujesz sam):

| Pole | Zasady |
|---|---|
| Imię, nazwisko | Wymagane. |
| E-mail | Wymagany. Służy do resetu hasła. |
| Data urodzenia | Nie może być z przyszłości. Nie jest pokazywana innym. |
| Telefon | Tylko cyfry, spacje i znaki `+ - ( )`. **Widoczny dla wszystkich zalogowanych.** |
| Opis | Wolny tekst, np. „Wychowawczyni 3A, konsultacje we wtorki 15:00”. **Widoczny dla wszystkich zalogowanych.** |

**Czego nie zmienisz sam:** loginu, roli i powiązań rodzic–dziecko. Zgłoś to administratorowi.

**Nie wpisuj w profilu** informacji prywatnych ani wrażliwych (zdrowie, adres domowy itp.). Profil widzą wszyscy zalogowani.

---

### 3.7 Media: galerie i zdjęcia

**Galerie** to albumy zdjęć, np. z wycieczki, jasełek czy dnia sportu.

- **Udostępnianie:** galerię można udostępnić grupom i/lub osobom. **Bez udostępnienia jest prywatna** (widzi ją tylko autor).
- **Kto widzi:** autor, osoby i grupy, którym ją udostępniono, oraz rodzice tych osób.
- **Kto dodaje zdjęcia:** autor oraz osoby i członkowie grup, którym galerię udostępniono. **Rodzic, który widzi galerię tylko przez dziecko, nie może dodawać zdjęć.**
- **Kto usuwa zdjęcia:** autor zdjęcia, a także autor galerii (dowolne zdjęcie).
- **Edycja i usuwanie galerii:** tylko autor. Usunięcie galerii usuwa wszystkie jej zdjęcia.

**Moje zdjęcia:** lista wszystkich zdjęć, które dodałeś do ogłoszeń, wiadomości i galerii, z możliwością usunięcia.

**Zdjęcia** (wszędzie w platformie):
- **Zmniejszanie:** są automatycznie zmniejszane (dłuższy bok do 1920 px) i zapisywane jako JPEG.
- **Prywatność:** **usuwane są dane ukryte w pliku, w tym lokalizacja GPS.**
- **Obrót:** zdjęcie zrobione telefonem „bokiem” zostaje automatycznie obrócone.
- **Przezroczystość i animacje:** przezroczyste tło staje się białe, a z animacji (GIF) zostaje pierwsza klatka.

**Nie używaj do:**
- **zdjęć uczniów bez zgody rodziców** (RODO). Udostępniaj galerie tylko właściwym grupom.
- skanów dokumentów: lepiej dodać je jako PDF w Dokumentach.

---

### 3.8 Dokumenty

**Do czego służy:** pliki dołączane do ogłoszeń, wydarzeń i wiadomości, np. zgody, regulaminy, listy lektur czy karty zgłoszeń.

- **Dozwolone formaty:** PDF, Word (DOC/DOCX), Excel (XLS/XLSX), PowerPoint (PPT/PPTX), OpenDocument (ODT/ODS/ODP), RTF, TXT, CSV.
- **Limity:** maks. **20 MB na plik** i **10 plików** na jeden wpis.
- **Strona „Dokumenty”** zbiera w jednym miejscu wszystkie dokumenty z ogłoszeń i wydarzeń, które do Ciebie (lub Twoich dzieci) trafiły, oraz z Twoich wątków wiadomości. Można filtrować: wszystkie / moje.
- **Usuwanie:** usunąć można tylko dokumenty dodane przez siebie.

**Nie używaj do:**
- plików wykonywalnych, archiwów ZIP ani zdjęć: zdjęcia dodaje się jako zdjęcia,
- przechowywania dokumentów bez związku z żadnym ogłoszeniem czy wydarzeniem.

---

### 3.9 Inwentarz (biblioteka)

**Do czego służy:** spis rzeczy, które ktoś posiada i może wypożyczyć innym. Pierwszym zastosowaniem jest **szkolna biblioteka**: książki należą do konta „biblioteka”. Na razie dostępna jest kategoria **Książka**.

**Trzy widoki:**

| Zakładka | Co pokazuje |
|---|---|
| Moje przedmioty | Rzeczy, których jesteś właścicielem, ze statusem „Dostępna” albo „Wypożyczono: [osoba]” i terminem zwrotu. |
| Wypożyczone przeze mnie | Rzeczy, które masz u siebie, z właścicielem i terminem zwrotu. |
| Wszystkie przedmioty | Katalog wszystkich użytkowników, przy każdej pozycji informacja, czy jest dostępna. |

**Wyszukiwanie:** po tytule, autorze, opisie lub numerze ISBN.

**Dodawanie książki:**

| Pole | Zasady |
|---|---|
| Tytuł, autor | Wymagane. |
| ISBN | Opcjonalny. 10 lub 13 cyfr (myślniki i spacje dozwolone), sprawdzana jest cyfra kontrolna. Kilka egzemplarzy może mieć ten sam ISBN. |
| Opis | Np. „Lektura dla klas 4–6”, stan egzemplarza. |
| Zdjęcia | Np. okładka. Do 10 na raz. |

**Wypożyczanie:**
- **Kto wypożycza:** wypożyczać może **tylko właściciel**. Wybiera osobę i opcjonalnie termin zwrotu (nie z przeszłości).
- **Kiedy przedmiot jest u wypożyczającego:** od razu pojawia się w jego zakładce „Wypożyczone przeze mnie”.
- **Zwrot zaznacza właściciel** po odebraniu rzeczy („Oznacz jako zwrócone”). Wypożyczający nie może sam zakończyć wypożyczenia.
- **Przekroczony termin** jest wyróżniony na czerwono.
- **Historia:** właściciel widzi historię wcześniejszych wypożyczeń.
- **Kto widzi nazwisko wypożyczającego:** tylko właściciel i sam wypożyczający. Pozostali w katalogu widzą tylko „Wypożyczona”.

**Nie używaj do:** spisu rzeczy szkolnych bez właściciela-osoby. Każdy przedmiot musi należeć do konkretnego konta, np. „biblioteka”.

---

### 3.10 Powiadomienia, sortowanie, język i wygląd

- **Liczniki w menu** pokazują nieprzeczytane ogłoszenia, nowe komentarze, nowe odpowiedzi w wiadomościach i nowe zdjęcia w galeriach. Licznik maleje po otwarciu danego elementu. Wartości powyżej 99 wyświetlają się jako „99+”.
- **Ogłoszenia i wiadomości** można sortować: najnowsze, ostatnia aktywność (np. nowy komentarz), alfabetycznie. Wybór jest zapamiętywany.
- **Platforma nie wysyła e-maili ani powiadomień push** o nowych treściach. Trzeba do niej zaglądać.

---

## 4. Instrukcje dla grup użytkowników

### 4.1 Dyrekcja i administratorzy

**Typowe zadania:**
- **Zakładanie kont** (importem lub w panelu administracyjnym), nadawanie ról i powiązań rodzic → dziecko.
- **Ogłoszenia ogólnoszkolne**, np. dni wolne, zmiany organizacyjne. Wybierz wszystkie grupy albo przygotuj grupę „Cała szkoła”.
- **Wydarzenia ogólnoszkolne** w Kalendarzu: rady pedagogiczne, uroczystości, dni wolne (typ „Dzień wolny”).
- **Porządkowanie grup:** przypisywanie wychowawców jako administratorów, usuwanie nieaktualnych grup w panelu.
- **Pomoc użytkownikom:** reset haseł, poprawa ról, odblokowanie dostępu.

**Na co uważać:**
- Konta z importu mają hasło równe loginowi, dopóki ktoś się nie zaloguje. Przekaż dane logowania i poproś o szybkie pierwsze logowanie.
- Usunięcie konta w panelu usuwa też wszystko, co ta osoba utworzyła: ogłoszenia, komentarze, wiadomości, wydarzenia, zdjęcia. Zamiast usuwać, **dezaktywuj konto**.
- Panel administracyjny daje szerokie uprawnienia. Pełne uprawnienia (superuser) powinno mieć jak najmniej osób.

### 4.2 Nauczyciele i wychowawcy

**Typowe zadania:**
- **Zarządzanie grupami swojej klasy** („Klasa X” i „Rodzice klasy X”): pilnowanie listy członków, dodanie nowego ucznia czy rodzica.
- **Ogłoszenia:**
  - do klasy: sprawy uczniów,
  - do rodziców: zebrania, zgody, opłaty.
  - Po kilku dniach warto sprawdzić, kto jeszcze nie przeczytał.
- **Wydarzenia:** wycieczki, sprawdziany, zebrania. Do wycieczki dołącz zgodę jako dokument.
- **Wiadomości** do konkretnego rodzica lub kilku rodziców w sprawach indywidualnych.
- **Galerie** z wydarzeń klasowych, udostępnione grupie klasy i grupie rodziców.

**Na co uważać:**
- **Lekcje** w kalendarzu należą do wychowawcy klasy, także te prowadzone przez innych nauczycieli. Prowadzący i współprowadzący są wpisani w opisie lekcji.
- **Sprawy wrażliwe** (oceny, zachowanie, zdrowie) poruszaj **tylko w Wiadomościach**, nigdy w ogłoszeniach ani komentarzach.
- **Odwołane zajęcia:** zmień status wydarzenia na „Odwołane” zamiast je usuwać.

### 4.3 Rodzice i opiekunowie

**Typowe zadania:**
- **Ogłoszenia i kalendarz:** sprawdzanie ich dla siebie i dzieci. Przy kilkorgu dzieciach każde wydarzenie ma w nawiasie login dziecka, którego dotyczy.
- **Komentarze** pod ogłoszeniem, gdy pytanie dotyczy wszystkich, np. „Czy zbiórka jest przed szkołą?”.
- **Wiadomości** do wychowawcy w sprawach własnego dziecka.
- **Galerie i dokumenty:** pobieranie zgód, przeglądanie zdjęć z wydarzeń.
- **Rodzic-administrator grupy klasowej** pomaga wychowawcy: może dodać do grupy nowego rodzica czy poprawić opis grupy.

**Na co uważać:**
- Komentarz pod ogłoszeniem widzą **wszyscy odbiorcy** i nie można go usunąć.
- Nie widzisz wiadomości prywatnych swojego dziecka. To zamierzone.
- Jeśli nie widzisz treści dziecka, prawdopodobnie brakuje powiązania rodzic → dziecko. Zgłoś to administratorowi.

### 4.4 Uczniowie

**Typowe zadania:**
- **Ogłoszenia klasy i plan zajęć** w Kalendarzu.
- **Materiały** od nauczyciela w Dokumentach.
- **Wiadomości** do nauczyciela.
- **Biblioteka:** książki wypożyczone na Twoje konto widać w „Inwentarz → Wypożyczone przeze mnie”, razem z terminem zwrotu.

**Na co uważać:**
- Nie twórz grup, ogłoszeń ani wydarzeń, jeśli nauczyciel o to nie prosi. Platforma technicznie na to pozwala, ale to narzędzie szkoły, nie czat.
- Zdjęcia innych osób dodawaj tylko za ich zgodą.

### 4.5 Biblioteka (konto „biblioteka”)

**Typowe zadania:**
- **Prowadzenie księgozbioru** w Inwentarzu: każdy egzemplarz to osobna pozycja. Dwa egzemplarze „Pana Tadeusza” to dwie pozycje.
- **Wypożyczanie** z terminem zwrotu, np. 2 tygodnie.
- **Zwroty:** zaznaczanie zwrotu po fizycznym odebraniu książki.
- **Kontrola terminów:** w „Moich przedmiotach” zaległe wypożyczenia są wyróżnione na czerwono.
- **Uzupełnianie danych:** brakujące ISBN-y i zdjęcia okładek przy okazji.

**Na co uważać:**
- Wypożyczonej książki nie da się usunąć. Najpierw zaznacz zwrot.
- Duże listy książek administrator może wczytać importem z pliku CSV.

---

## 5. Przykładowe scenariusze (use case'y)

### UC1. Wycieczka klasowa ze zgodą rodziców

1. **Wydarzenie:** wychowawczyni 4A tworzy w Kalendarzu „Wycieczka do Muzeum Fram”, typ *Edukacyjne*, status *Wstępne*, dla grup „Klasa 4A” i „Rodzice klasy 4A”, z dołączonym PDF ze zgodą.
2. **Ogłoszenie:** publikuje ogłoszenie do „Rodzice klasy 4A” z prośbą o oddanie zgód do piątku i datą wygaśnięcia w ten piątek.
3. **Kontrola odczytów:** po dwóch dniach sprawdza, kto nie przeczytał ogłoszenia, i do tych osób pisze Wiadomość.
4. **Potwierdzenie:** gdy termin jest pewny, zmienia status wydarzenia na *Aktywne*.

**Wynik:** rodzice widzą termin w kalendarzu, zgoda jest w Dokumentach, a wychowawczyni wie, kto jeszcze nie przeczytał.

### UC2. Rodzic dwójki dzieci w różnych klasach

**Sytuacja:** pani Chmielewska ma powiązania z Dawidem (2B), Oskarem (5) i Weroniką (6A).

**Co widzi:**
- **Na stronie głównej:** cztery zakładki (ona i troje dzieci), każda z liczbą wydarzeń na najbliższe 2 dni.
- **W Kalendarzu:** lekcje wszystkich dzieci, z loginem dziecka w nawiasie przy tytule.
- **W ogłoszeniach:** ogłoszenia dla klas 2B, 5 i 6A, a przy każdym informacja, którego dziecka dotyczy.

**Wynik:** jedno konto wystarcza do śledzenia całej rodziny.

### UC3. Wypożyczenie i zwrot książki w bibliotece

1. **Wypożyczenie:** biblioteka znajduje w katalogu „Dzieci z Bullerbyn” i wypożycza ją uczennicy klasy 2A z terminem zwrotu za 14 dni.
2. **U uczennicy:** książka pojawia się w jej zakładce „Wypożyczone przeze mnie”, a w katalogu inni widzą status „Wypożyczona”.
3. **Zwrot:** po oddaniu książki biblioteka zaznacza „Oznacz jako zwrócone”. Książka znów jest dostępna, a wypożyczenie trafia do historii.

### UC4. Zaległy zwrot książki

**Sytuacja:** termin zwrotu minął. W „Moich przedmiotach” biblioteki pozycja jest wyróżniona na czerwono, a uczeń widzi czerwony termin w „Wypożyczone przeze mnie”.

**Co robi biblioteka:** wysyła uczniowi (lub rodzicowi) Wiadomość z przypomnieniem. Platforma sama nie wysyła przypomnień.

### UC5. Nowy uczeń dołącza do klasy

1. **Konta:** administrator zakłada konto ucznia i rodziców z powiązaniem rodzic → dziecko.
2. **Grupy:** wychowawca (albo rodzic-administrator grupy) dodaje ucznia do „Klasa 3B”, a rodziców do „Rodzice klasy 3B”.
3. **Co od razu działa:** od tej chwili uczeń i rodzice widzą lekcje i nowe ogłoszenia klasy. Wcześniejsze ogłoszenia do grupy także są widoczne, bo widoczność zależy od przynależności do grupy.

### UC6. Odwołanie zajęć

**Sytuacja:** zajęcia z katechezy w 4B się nie odbędą.

**Co robi autor wydarzenia** (wychowawca klasy):
1. Zmienia status tej jednej lekcji na *Odwołane* i dopisuje w opisie powód.
2. Opcjonalnie dodaje krótkie ogłoszenie do „Rodzice klasy 4B”.

**Czego unikać:** usuwania lekcji. Wtedy rodzice nie dowiedzą się, że zajęcia były odwołane.

### UC7. Galeria z jasełek

1. **Galeria:** nauczycielka tworzy galerię „Jasełka 2026” i udostępnia ją grupom „Klasa 1A” i „Rodzice klasy 1A”.
2. **Zdjęcia:** dodaje 40 zdjęć, w kilku partiach po maks. 10.
3. **Dodawanie przez rodziców:** rodzice z grupy „Rodzice klasy 1A” mogą dodać własne zdjęcia. Rodzic, który widzi galerię tylko przez dziecko (nie jest w grupie rodziców), może je oglądać, ale nie dodawać.
4. **Usuwanie:** nauczycielka jako autorka galerii może usunąć każde nieodpowiednie zdjęcie.

### UC8. Rozmowa rodzica z wychowawcą i pedagogiem

1. **Nowy wątek:** rodzic zakłada wątek „Sprawa Jakuba – zachowanie na przerwach” z wychowawczynią jako odbiorczynią.
2. **Brak pedagoga w wątku:** wychowawczyni chce włączyć pedagoga, ale odbiorców nie da się dodać, więc zakłada **nowy wątek** z rodzicem i pedagogiem i streszcza w nim sprawę.

### UC9. Grupa na zajęcia międzyklasowe

**Sytuacja:** nauczyciel tworzy grupę „Chór szkolny”, korzystając z „Dodaj członków z grup” (klasy 4A, 4B, 4C), a potem usuwa osoby, które się nie zapisały.

**Na co uważać:** to jednorazowa kopia. Gdy do 4A dojdzie nowy uczeń, nie trafi do chóru automatycznie.

---

## 6. Warunki brzegowe i ograniczenia

### Konto i logowanie

| Sytuacja | Zachowanie platformy |
|---|---|
| Ktoś chce założyć konto sam | Niemożliwe. Nie ma strony rejestracji, konto zakłada szkoła. |
| Pierwsze logowanie | Każda strona przekierowuje do zmiany hasła, dopóki hasło nie zostanie zmienione. |
| Nowe hasło takie jak login lub podobne do imienia / nazwiska | Odrzucone. |
| Nowe hasło krótsze niż 4 znaki | Odrzucone. |
| Konto bez adresu e-mail (np. uczniowie) | Reset hasła przez e-mail niemożliwy. Hasło zmienia administrator. |
| Konto dezaktywowane | Nie można się zalogować. Treści tej osoby zostają. |
| Konto usunięte | Znikają też wszystkie treści, które ta osoba utworzyła. |

### Profil i użytkownicy

| Sytuacja | Zachowanie platformy |
|---|---|
| Data urodzenia w przyszłości | Odrzucona. |
| Telefon z literami | Odrzucony (dozwolone: cyfry, spacje, `+ - ( )`). |
| Pusty e-mail w profilu | Odrzucony. E-mail jest wymagany. |
| Chęć zmiany loginu, roli lub powiązań | Niemożliwa w profilu. Robi to administrator. |
| Telefon i opis w profilu | Widoczne dla **wszystkich** zalogowanych. |

### Ogłoszenia i komentarze

| Sytuacja | Zachowanie platformy |
|---|---|
| Ogłoszenie bez grup i bez osób | Odrzucone („Wybierz co najmniej jedną grupę lub osobę”). |
| Minęła data wygaśnięcia | Ogłoszenie dalej widoczne, z oznaczeniem „wygasłe”. |
| Ogłoszenie do osoby, która ma rodzica | Rodzic też je widzi. |
| Komentarz dłuższy niż 500 znaków | Odrzucony. |
| Pomyłka w komentarzu | Komentarza nie da się edytować ani usunąć. |
| Usunięcie ogłoszenia | Znikają też komentarze, zdjęcia i dokumenty. |
| Nowa osoba dołącza do grupy | Widzi także wcześniejsze ogłoszenia tej grupy. |

### Wydarzenia

| Sytuacja | Zachowanie platformy |
|---|---|
| Wydarzenie bez grup i bez osób | Odrzucone. |
| Wydarzenie dłuższe niż 23 h 59 min | Niemożliwe w jednym wpisie. Podziel je na dni. |
| Czas trwania 0 h 0 min | Wydarzenie bez długości. Unikaj tego, ustaw realny czas. |
| Lekcje co tydzień | W aplikacji brak powtarzania. Plan lekcji wczytuje administrator importem. |
| Edycja cudzego wydarzenia | Niemożliwa. Edytuje tylko autor. |
| Odwołanie | Zmiana statusu na „Odwołane”. Usunięcie kasuje wydarzenie bez śladu. |

### Wiadomości

| Sytuacja | Zachowanie platformy |
|---|---|
| Wiadomość do grupy | Niemożliwa. Odbiorcami są tylko osoby. |
| Dodanie odbiorcy do istniejącego wątku | Niemożliwe. Załóż nowy wątek. |
| Treść dłuższa niż 1500 znaków | Odrzucona. Podziel ją lub dołącz dokument. |
| Rodzic a wiadomości dziecka | Rodzic ich nie widzi. |
| Odpowiedź w cudzym wątku | Niemożliwa. Odpowiadają tylko autor i odbiorcy. |

### Grupy

| Sytuacja | Zachowanie platformy |
|---|---|
| Nazwa grupy już istnieje (także inną wielkością liter) | Odrzucona. |
| Usunięcie ostatniego administratora | Odrzucone. Grupa musi mieć co najmniej jednego. |
| Osoba jednocześnie administratorem i członkiem | Zostaje tylko administratorem. |
| Edycja grupy przez zwykłego członka | Niemożliwa. Przycisk „Edytuj” widzą tylko administratorzy. |
| Zmiany w grupie źródłowej po „Dodaj członków z grup” | Nie przenoszą się. Kopia jest jednorazowa. |
| Usunięcie grupy | Niedostępne w aplikacji. Robi to administrator platformy. |

### Zdjęcia, galerie i dokumenty

| Sytuacja | Zachowanie platformy |
|---|---|
| Więcej niż 10 zdjęć lub dokumentów na raz | Odrzucone. Dodaj w kilku partiach (galeria, edycja). |
| Plik, który nie jest obrazem, wysłany jako zdjęcie | Odrzucony („nie jest prawidłowym obrazem”). |
| Bardzo duże zdjęcie z aparatu | Zmniejszone do 1920 px, zapisane jako JPEG, bez danych GPS. |
| Dokument większy niż 20 MB | Odrzucony. |
| Nieobsługiwany format (np. ZIP, EXE) | Odrzucony. |
| Galeria bez udostępnienia | Widzi ją tylko autor. |
| Rodzic widzący galerię przez dziecko | Może oglądać, nie może dodawać zdjęć. |
| Usunięcie galerii | Usuwa wszystkie jej zdjęcia. |

### Inwentarz

| Sytuacja | Zachowanie platformy |
|---|---|
| Nieprawidłowy ISBN (zła cyfra kontrolna, zła długość) | Odrzucony. |
| Brak ISBN | Dozwolone. |
| Ten sam ISBN w kilku egzemplarzach | Dozwolone. |
| Wypożyczenie samemu sobie | Niemożliwe. |
| Termin zwrotu w przeszłości | Odrzucony. |
| Wypożyczenie przedmiotu, który już jest wypożyczony | Odrzucone („jest już wypożyczony”). |
| Usunięcie wypożyczonego przedmiotu | Odrzucone. Najpierw zaznacz zwrot. |
| Zwrot zaznaczany przez wypożyczającego | Niemożliwy. Zwrot zaznacza właściciel. |
| Cudzy przedmiot: edycja, wypożyczenie, usunięcie | Niemożliwe (strona „nie znaleziono”). |
| Kto widzi, kto wypożyczył | Tylko właściciel i wypożyczający. |

---

## 7. Dobre praktyki

1. **Właściwe narzędzie:**
   - termin → **Kalendarz**,
   - informacja dla wielu osób → **Ogłoszenie**,
   - sprawa indywidualna → **Wiadomość**,
   - zdjęcia z wydarzenia → **Galeria**.
2. **Jasne tytuły** z klasą i datą, np. „4A – zebranie 12.11”, ułatwiają wyszukiwanie i sortowanie.
3. **Daty wygaśnięcia** ogłoszeń ułatwiają odróżnienie aktualnych informacji od archiwalnych.
4. **Odwoływanie zamiast usuwania** wydarzeń. Usunięcie nie zostawia śladu.
5. **Sprawy wrażliwe** (oceny, zdrowie, zachowanie) tylko w Wiadomościach, do właściwych osób.
6. **RODO:** zdjęcia uczniów udostępniaj tylko grupom, których dotyczą, i tylko za zgodą rodziców. W profilu nie wpisuj danych, których nie chcesz pokazywać całej szkole.
7. **Regularne logowanie:** platforma nie wysyła e-maili o nowościach. Zaglądaj do niej i sprawdzaj liczniki w menu.
8. **Błędy w danych** (zła rola, brak powiązania z dzieckiem, brak w grupie) zgłaszaj administratorowi lub wychowawcy-administratorowi grupy.
