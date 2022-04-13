Implementační dokumentace k 2. úloze do IPP 2019/2020\
Jméno a příjmení: Michal Halabica\
Login: xhalab00

## Interpret jazyka IPPCode20 (interpret.py)

Interpret jazyka IPPCode20 přijímá na standardním vstupu (nebo ze souboru pomocí parametru --source) XML soubor reprezentující jazyk IPPCode20.
Interpret provádí syntaktickou a lexikální analýzu obsahu a následnou interpretaci programu.

### Načítání dat a analýza dat

Základem načítání dat pro následnou interpretaci je třída `InstructionsParser` obsahující statické metody.
Po načtení parametrů z příkazové řádky se volá metoda `InstructionsParser.parse_file`, která provede načtení XML souboru a kontrola obsahu.
Po úspěšném načtení XML obsahu se provedou následující kontroly:

* Existence elementu program, attributu language a jeho správnosti.
* Načtení jednotlivých podřízených elementů reprezentující instrukce.
  * Při načítání jednotlivých instrukcí se provádí následující kontroly argumentů:
    * U proměnných a návěští správnost formátu
    * U typu `nil` probíhá kontrola, že hodnota je pouze nil.
    * Další kontroly správnosti datových typů jako string, bool, int, float.
    * Kontrola očekáváného typu argumentu a skutečně zadaným vstupem.

Funkce `InstructionsParser.parse_file` vrací objekt typu `Dict[int, InstructionBase]`, reprezentující seřazené asociativní pole, kde klíčem je obsah atributu `order` a hodnotou je instance třídy reperezentující instrukci.

#### Reprezentace instrukcí

Instrukce jsou implementovány jako třídy dědící z bázové třídy `InstructionBase`. Díky tomuto je dosáhnuto, že všechny instrukce budou mít implementovány stejné metody a zároveň dojde ke snížení množství duplicitního kódu.
Pro další zjednodušení kódu byly implementovány i další bázové třídy, jako například bázová třída pro aritmetické operace.

### Interpretace

Základem celé interpretace je třída `Program`, která zapouzdřuje důležité vlastnosti potřebné pro interpretaci (zásobníky, rámce, seznam návěští, seznam instrukcí).

Po úspěšném načtení instrukcí a vyhledání všech návěští se volá metoda `Run`, která volá metodu `execute` u jednotlivých instrukcí.

### Rozšíření

Do interpretu byly implementovány následující rozšíření:

* FLOAT - Podpora datového typu `float`. Podpora tohoto typu v instrukcích + nové instrukce pro práci s tímto typem (INT2FLOAT, DIV, ...).
* STACK - Podpora instrukcí pracující s datovým zásobníkem.
* STATI - Statistiky interpretace (počet provedených návěští, maximální počet inicializovaných proměnných v rámcích).

## Testovací skript (test.php)

Skript za pomocí testovacích dat automatické testy skriptů `parse.php` a `interpret.py`.

Skript při svém spuštění a načtení konfigurace z příkazové řádky provede vyhledání testů a jejich následné spuštění.

Vyhledávání testů je možné provádět rekurzivně (za pomocí parametru `--recursive`). Vyhledávání se odvíjí od zadaného adresáře v parametru `--directory={dir}`. Pokud není zadán, bere se aktuální adresář.

### Provádění testů

Prvně se provede vyhodnocení, ve kterém režimu se má testování provést. Jsou k dispozici následující režimy:

* `pipeline` - Výchozí režim, kdy se provádí testování obou skriptů najedno.
  * Testovací skript vezme zdrojový kód, ten předá skriptu `parse.php`, výstup tohoto skriptu je předán skriptu `interpret.py`.
* `interpret-only` - Testování probíhá pouze nad skriptem `interpret.py`. Spouští se pomocí parametru `--int-only`.
* `parser-only` - Testování probíhá pouze nad skriptem `parse.php`. Spouští se pomocí parametru `--parse-only`.

### Generování HTML reportu

Výstup skriptu `test.php` je HTML stránka vypsaná na standardní výstup. Obsahuje souhrnné informace o konfiguraci testovacího skriptu, souhrný výsledek testů v podobně počtu úspěšných/neúspěšných testů a jeho procentuální reprezentace. Dále jsou vypsány výstupy jednotlivých testů.
