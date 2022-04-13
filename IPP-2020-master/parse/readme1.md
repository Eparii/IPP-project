Implementační dokumentace k 1. úloze do IPP 2019/2020\
Jméno a příjmení: Michal Halabica\
Login: xhalab00

## Analyzátor zdrojového kódu IPPcode20 (parse.php)
Skript parse.php přijímá na standardním vstupu zdrojový kód psaný v jazyce IPPcode20 provede syntaktickou a lexikální analýzu a na standardní výstpu vypíše XML reprezentaci programu jazyka IPPcode20.

Základem celého skriptu je třída `Program`, ve kterém jsou uložené potřebné vlastnosti a metody pro zpracování zdrojového kódu v jazyce IPPcode20.

### Definice podporovaných instrukcí
Instrukce, které může skript `parse.php` zpracovat jsou definovány v poli `instructionCollection`. Pole `instructionCollection` se nachází v třídě `Program`.

Podporované instrukce jsou definované jako asociativní pole, kde na zadaném klíči (jako klíč se používá název instrukce (Uppercase)) se nachází pole řetězců definující, které operandy jsou pro danou instrukci podporovány. Pro zjednodušení zápisu definice podporovaných instrukcí je definována výčtová třída (třída obsahující pouze konstanty) možných druhů operandů.

Výsledná definice jednoho prvku v poli podporovaných instrukcí vypadá následovně:
```php
"READ" => [DataTypes::variable, DataTypes::type],
"MOVE" => [DataTypes::variable, DataTypes::symbol]
```

### Analýza instrukcí
Analýza instrukcí zdrojového kódu jazyka IPPcode20 probíhá v následujících krocích:
1) Načtení řádku ze standardního vstupu.
2) Očištění přebytečných bílích znaků. Očištění od komentářů. Pokud skript narazí po potřebných očištění na prázdný řádek, tak jej přeskočí a pokračuje znovu od kroku 1.
3) Zavolá se funkce `addInstruction`, která provede lexikální a syntaktickou kontrolu a uloží zpracovanou instrukci do pomocného pole. Funkce `addInstruction` se skládá z následujících podkroků:
    -  Provede se kontrola, že byla načtena hlavička zdrojového kódu (řetězec `.IPPcode20` (case insensitive)). Pokud bude zjištěna přítomnost více hlaviček, tak skript končí chybou 21.
    -  Kontrola, že byla načtena instrukce s podporovaným operačním kódem. Pokud bude načtena instrukce s nepodporovaným operačním kódem, tak skript končí chybou 22.
    -  Vytvoří se instance třídy `Instruction` a provede se lexikální a syntaktická kontrola operandů. Pokud bude nalezena lexikální, nebo syntaktická chyba, tak skript končí chybou 23.
    -  Instance třídy `Instruction` se uloží do pomocného pole pro pozdější generování výslední XML reprezentace.

### Výsledná reprezentace
Po úspěšné lexikální a syntaktické kontrole dochází ke generování výsledné XML reprezentace programu psaného v jazyce IPPCode20.

Z pomocného pole instancí třídy `Instruction` se provede generování výsledné XML reprezentace.

V hlavní třídě `Program` se nachází metoda `generateXml`, která vytvoří základní kostru XML dokumentu (XML hlavičku, kořenový element s požadovanými attributy) a nad každou načtenou instrukcí zavolá metodu `setInstructionXml`, která doplní kompletní XML reprezentaci. 

### Statistiky
Jako rozšíření byly implementovány statistiky v podobě počítadel jednotlivých částí kódu.

Rozšíření umožňuje vygenerování následujících statistik: Počet komentářů,  instrukcí, unikátních návěští a skokových instrukcí.
