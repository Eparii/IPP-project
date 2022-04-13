<?php

/**
 * Skript pro parsing jazyka IPPCode20.
 * 
 * @author Michal Halabica xhalab00 (xhalab00@stud.fit.vutbr.cz)
 */


/**
 * Pomocna funkce pro vyhledavani podretezcu.
 * 
 * @param string $str Originalni retezc.
 * @param string $searched Hledany podretezec.
 */
function stringContains($str, $searched)
{
    return strpos($str, $searched) !== false;
}

/**
 * Trida pro uchovavani statistik.
 */
class Statistics
{
    /** Nazev souboru, do ktereho se budou uchovavat statistiky. */
    public static $statsFilename;

    /** Pocitadlo instrukci. */
    private static $instructionCount = 0;

    /** Pocitadlo komentaru. */
    private static $commentsCount = 0;

    /** Pocitadlo navesti. */
    private static $labels = [];

    /** Pocitadlo skokovych instrukci. */
    private static $jumpsCount = 0;

    /**
     * Obecna funkce pro inkrementaci hodnoty ve statistice.
     * 
     * @param string $type Pocitana kategorie.
     */
    public static function incrementStats($type, $optional = null)
    {
        switch ($type) {
            case "loc":
                self::$instructionCount++;
                break;
            case "comments":
                self::$commentsCount++;
                break;
            case "labels":
                if (!in_array($optional, self::$labels)) {
                    array_push(self::$labels, $optional);
                }
                break;
            case "jumps":
                self::$jumpsCount++;
                break;
        }
    }

    /**
     * Funkce pro pokus o aktivaci pocitadel statistik.
     * Uspech pouze v pripade, ze na prikazove radce je --stats={file}.
     * Pokud funkce narazi na vice parametru --stats={file}, pak zahlasi chybu.
     *
     * @param string[] $args Pole parametru na prikazove radce.
     */
    public static function enableStatistics($args)
    {
        foreach ($args as $arg) {
            if (preg_match("/--stats=(.+)/", $arg, $matches) === 1) {
                if (!empty(self::$statsFilename))
                    Output::error(Output::invalidArgs, "Multiple --stats arguments");

                self::$statsFilename = $matches[1];
                break;
            }
        }
    }

    /**
     * Funkce pro zapsání statistik do souboru.
     *
     * @param string[] $args Pole parametru na prikazove radce.
     */
    public static function saveStatistics($args)
    {
        if (empty(self::$statsFilename)) return;

        $file = fopen(self::$statsFilename, 'w');
        if ($file === false)
            Output::error(Output::fileOutputOpenError, "Cannot open file " . self::$statsFilename);

        foreach ($args as $arg) {
            switch ($arg) {
                case "--loc":
                    fwrite($file, self::$instructionCount . "\n");
                    break;
                case "--comments":
                    fwrite($file, self::$commentsCount . "\n");
                    break;
                case "--labels":
                    fwrite($file, count(self::$labels) . "\n");
                    break;
                case "--jumps":
                    fwrite($file, self::$jumpsCount . "\n");
                    break;
            }
        }

        fclose($file);
    }
}

/**
 * Obecna trida pro praci s instrukcemi.
 */
class Instruction
{
    /** Operacni kod. */
    public $name;

    /** Cislo radku na kterem se nachazi instrukce. */
    public $line;

    /** Identifikator instrukce. (Atribut order ve vystupnim XML.) */
    public $id;

    /** Pole zpracovanych parametru instrukce. */
    public $arguments;

    /**
     * Konstruktor instrukce. Provadi kontroly a zpracovani parametru instrukce.
     *
     * @param string $name Operacni kod.
     * @param int $id Identifikator instrukce
     * @param int $line Cislo radku na kterem se instrukce nachazi.
     * @param string[] $args Parametry instrukce.
     * @param string[] $expectedTypes Ocekavane parametry instrukce.
     */
    public function __construct($name, $id, $line, $args, $expectedTypes)
    {
        $this->name = $name;
        $this->line = $line;
        $this->id = $id;
        $this->arguments = [];

        $this->checkArguments($args, $expectedTypes);

        foreach ($args as $index => $arg) {
            $this->insertArgument($arg, $expectedTypes[$index]);
        }
    }

    /**
     * Kontrola parametru instrukce.
     *
     * @param string[] $args Parametry zadane u instrukce.
     * @param string[] $expectedTypes Ocekavane parametry instrukce.
     */
    private function checkArguments($args, $expectedTypes)
    {
        $expectedArgsCount = count($expectedTypes);
        if (count($args) != $expectedArgsCount)
            Output::error(Output::syntaxError, "Invalid syntax at instruction " . $this->name . " on line " . $this->line . "\nExpected: $expectedArgsCount, have " . count($args) . "\n" . implode(' ', $args));

        foreach ($expectedTypes as $index => $expectedType) {
            switch ($expectedType) {
                case DataTypes::label:
                    $this->checkLabel($args[$index]);
                    break;
                case DataTypes::variable:
                    $this->checkFrame($args[$index]);
                    break;
                case DataTypes::symbol:
                    $this->checkSymbol($args[$index]);
                    break;
                case DataTypes::type:
                    if (!$this->isValidType($args[$index], true))
                        Output::error(Output::syntaxError, "Invalid syntax at instruction " . $this->name . " on line " . $this->line . "\n" . $args[$index]);
                    break;
                default:
                    throw new Exception("Invalid type\n$expectedType");
            }
        }
    }

    /**
     * Funkce pro vlozeni potrebnych dat instrukce do XML.
     *
     * @param DOMDocument $document XML document, do ktereho se vkladaji DOM elementy. 
     * @param DOMElement $xmlElem Element, do ktereho se budou vkladat data.
     */
    public function setInstructionXml($document, $xmlElem)
    {
        $xmlElem->setAttribute("order", $this->id);
        $xmlElem->setAttribute("opcode", strtoupper($this->name));

        for ($i = 0; $i < count($this->arguments); $i++) {
            $argument = $this->arguments[$i];

            $argElem = $document->createElement("arg" . ($i + 1), trim($argument["value"]));
            $argElem->setAttribute("type", $argument["type"]);

            $xmlElem->appendChild($argElem);
        }
    }

    /**
     * Funkce pro kontrolu navesti.
     * Pokud dojde prazdne navesti, nebo chybne zdane, tak skript skonci s chybou 23.
     *
     * @param string $label Vstupni navesti.
     */
    private function checkLabel($label)
    {
        if (empty($label))
            Output::error(Output::syntaxError, "Invalid syntax at instruction " . $this->name . " on line " . $this->line . "\nLabel cannot be empty.");

        if (preg_match("/^[_\-$&%*!?a-zA-Z]\w*$/", $label) == 0)
            Output::error(Output::syntaxError, "Invalid syntax at instruction " . $this->name . " on line " . $this->line . "\nInvalid label format.");
    }

    /**
     * Funkce pro kontrolu ramcu promennych.
     *
     * @param string $frame Identifikator ramce.
     * @return boolean Vraci true, pokud bude ramec z mnoziny {GF, TF, LF}.
     */
    private function isValidFrame($frame)
    {
        return in_array($frame, ["GF", "TF", "LF"]);
    }

    /**
     * Funkce pro kontrolu parametru.
     * Funkce podporuje pouze kontroly pro promenne a symboly.
     * Pokud bude na vstupu neplatny format, tak skript skonci s chybou 23.
     *
     * @param string $param Vstupni promenna, nebo symbol.
     */
    private function checkParameter($param)
    {
        if (!stringContains($param, '@'))
            Output::error(Output::syntaxError, "Invalid syntax of second argument in instruction " . $this->name . " on line" . $this->line . "\n" . $param);
    }

    /**
     * Funkce pro kontrolu datovych typu.
     * Podporovany jsou pouze typy string, int, bool, nil.
     *
     * @param string $type Vstupni datovy typ.
     * @param boolean $noNil Volitelny parametr. Pokud bude mít hodnotu true, tak se z kontroly vynecha nil.
     * @return boolean
     */
    private function isValidType($type, $noNil = false)
    {
        $types = ["string", "int", "bool"];

        if (!$noNil)
            array_push($types, "nil");

        return in_array($type, $types);
    }

    /**
     * Funkce pro kontrolu symbolu.
     *
     * @param string $symbol Vstupni symbol.
     * @return void
     */
    private function checkSymbol($symbol)
    {
        $this->checkParameter($symbol);

        list($type, $value) = explode('@', $symbol, 2);

        if (!$this->isValidFrame($type) && !$this->isValidType($type))
            Output::error(Output::syntaxError, "Invalid symbol in argument at instruction " . $this->name . " on line " . $this->line . "\n$symbol");

        if ($type == "nil" && $symbol != "nil@nil")
            Output::error(Output::syntaxError, "Invalid symbol in argument at instruction " . $this->name . " on line " . $this->line . "\nAllowed only nil@nil\n$symbol");

        if ($type == "bool" && !in_array($value, ["true", "false"]))
            Output::error(Output::syntaxError, "Invalid symbol in argument at instruction " . $this->name . " on line " . $this->line . "\nAllowed only bool@true and bool@false\n$symbol");

        if ($type == "string") {
            // Pokud obsahuje escape sekvenci.
            if (stringContains($value, "\\") && preg_match("/\\\\\d{3}/", $value) == 0) {
                Output::error(Output::syntaxError, "Invalid escape sequence at instruction " . $this->name . " on line " . $this->line);
            }
        }
    }

    /**
     * Funkce pro kontrolu ramcu.
     * Pokud se na vstupu nachazi neplatny ramec, tak skript konci s chybou 23.
     *
     * @param string $var Vstupni ramec.
     * @return void
     */
    private function checkFrame($var)
    {
        $this->checkParameter($var);

        if (preg_match("/^[LGT]F@[_\-$&%*!?a-zA-Z]\S*$/", $var) == 0)
            Output::error(Output::syntaxError, "Invalid variable at instruction " . $this->name . " on line " . $this->line . "\nAllowed: GF, TF, LF");
    }

    /**
     * Funkce pro vlozeni zkontrolovanych parametru do mezipole, nez dojde k jeho vlozeni do XML.
     *
     * @param string $arg Vstupni parametr.
     * @param string $type Typ parametru. (var, symbol, type)
     * @return void
     */
    private function insertArgument($arg, $type)
    {
        $arg = @htmlspecialchars($arg);

        switch ($type) {
            case DataTypes::label:
                Statistics::incrementStats('labels', $arg);
                array_push($this->arguments, ["type" => $type, "value" => $arg]);
                break;
            case DataTypes::variable:
            case DataTypes::type:
                array_push($this->arguments, ["type" => $type, "value" => $arg]);
                break;
            case DataTypes::symbol:
                list($dataType, $value) = explode('@', $arg, 2);

                if ($this->isValidFrame($dataType)) {
                    $this->insertArgument($arg, DataTypes::variable);
                    return;
                }

                array_push($this->arguments, ["type" => $dataType, "value" => $value]);
                break;
            default:
                throw new Exception("Invalid argument\n$arg\n$type");
        }
    }
}

/**
 * Vyctova trida pro datove typy.
 */
class DataTypes
{
    /** Promenna */
    public const variable = "var";

    /** Navesti */
    public const label = "label";

    /** Symboly (muze obsahovat i nazvy promennych.) */
    public const symbol = "symbol";

    /** Typ */
    public const type = "type";
}

/**
 * Pomocna trida pro vystupni interakci.
 */
class Output
{
    /** Chybovy kod pro neplatne parametry na prikazove radce. */
    public const invalidArgs = 10;

    /** Nelze otevrit soubor. */
    public const fileOutputOpenError = 12;

    /** Neplatna nebo chybejici hlavicka. */
    public const invalidOrMissingHeader = 21;

    /** Neplatna (neznama) instrukce. */
    public const invalidInstruction = 22;

    /** Neplatna syntaxe. */
    public const syntaxError = 23;

    /**
     * Pomocna ladici funkce pro vypis diagnostickych zprav.
     * Vypisuje ladici vystupy na STDERR.
     *
     * @param string $message Vystupni zprava.
     * @return void
     */
    public static function debug($message)
    {
        fwrite(STDERR, "$message\n");
    }

    /**
     * Pomocna funkce pro hlaseni chyb. Vypise zpravu na vystup a ukonci program s chybovym kodem.
     *
     * @param int $code Navratovy kod.
     * @param string $message Zprav na STDERR.
     * @return void
     */
    public static function error($code, $message = null)
    {
        if (!empty($message)) self::debug($message);
        exit($code);
    }
}

/**
 * Logika programu.
 */
class Program
{
    /** Priznak, ze byla nalezena hlavicka. */
    private $haveHeader;

    /** Seznam nactenych instrukci. */
    private $instructions;

    /** Pocitadlo instrukci (identifikatory instrukci.) */
    private $counter;

    /** Seznam podporovanych instrukci. */
    private $instructionCollection;

    public function __construct()
    {
        $this->instructions = [];
        $this->counter = 1;
        $this->instructionCollection = [
            // Ramce, volani
            "MOVE" => [DataTypes::variable, DataTypes::symbol],
            "CREATEFRAME" => [],
            "PUSHFRAME" => [],
            "POPFRAME" => [],
            "DEFVAR" => [DataTypes::variable],
            "CALL" => [DataTypes::label],
            "RETURN" => [],

            // Prace s datovym zasobnikem.
            "PUSHS" => [DataTypes::symbol],
            "POPS" => [DataTypes::variable],

            // Aritmeticke, relacni, booleovske a konverzni instrukce.
            "ADD" => [DataTypes::variable, DataTypes::symbol, DataTypes::symbol],
            "SUB" => [DataTypes::variable, DataTypes::symbol, DataTypes::symbol],
            "MUL" => [DataTypes::variable, DataTypes::symbol, DataTypes::symbol],
            "IDIV" => [DataTypes::variable, DataTypes::symbol, DataTypes::symbol],
            "LT" => [DataTypes::variable, DataTypes::symbol, DataTypes::symbol],
            "GT" => [DataTypes::variable, DataTypes::symbol, DataTypes::symbol],
            "EQ" => [DataTypes::variable, DataTypes::symbol, DataTypes::symbol],
            "AND" => [DataTypes::variable, DataTypes::symbol, DataTypes::symbol],
            "OR" => [DataTypes::variable, DataTypes::symbol, DataTypes::symbol],
            "NOT" => [DataTypes::variable, DataTypes::symbol],
            "INT2CHAR" => [DataTypes::variable, DataTypes::symbol],
            "STRI2INT" => [DataTypes::variable, DataTypes::symbol, DataTypes::symbol],

            // Vstupne-vystupni instrukce
            "READ" => [DataTypes::variable, DataTypes::type],
            "WRITE" => [DataTypes::symbol],

            // Prace s retezci
            "CONCAT" => [DataTypes::variable, DataTypes::symbol, DataTypes::symbol],
            "STRLEN" => [DataTypes::variable, DataTypes::symbol],
            "GETCHAR" => [DataTypes::variable, DataTypes::symbol, DataTypes::symbol],
            "SETCHAR" => [DataTypes::variable, DataTypes::symbol, DataTypes::symbol],

            // Prace s typy
            "TYPE" => [DataTypes::variable, DataTypes::symbol],

            // Instrukce pro rizeni toku programu.
            "LABEL" => [DataTypes::label],
            "JUMP" => [DataTypes::label],
            "JUMPIFEQ" => [DataTypes::label, DataTypes::symbol, DataTypes::symbol],
            "JUMPIFNEQ" => [DataTypes::label, DataTypes::symbol, DataTypes::symbol],
            "EXIT" => [DataTypes::symbol],

            // Ladici instrukce
            "DPRINT" => [DataTypes::symbol],
            "BREAK" => []
        ];
    }

    /** Vlozeni instrukce nactene ze standardniho vstupu. */
    public function addInstruction($fields, $line)
    {
        $instructionName = trim(strtoupper($fields[0]));

        if ($instructionName == ".IPPCODE20" && !$this->haveHeader) {
            $this->haveHeader = true;
            return;
        }

        if (!$this->haveHeader)
            Output::error(Output::invalidOrMissingHeader, "Missing header row in source file.");

        if (!array_key_exists($instructionName, $this->instructionCollection))
            Output::error(Output::invalidInstruction, "Invalid instruction on row " . ($line + 1) . "\n" . implode(' ', $fields));

        Statistics::incrementStats('loc');

        if (in_array($instructionName, ["JUMP", "JUMPIFEQ", "JUMPIFNEQ", "CALL", "RETURN"]))
            Statistics::incrementStats('jumps');

        array_shift($fields);

        $allowedArgs = $this->instructionCollection[$instructionName];
        $instruction = new Instruction($instructionName, $this->counter++, $line + 1, $fields, $allowedArgs);
        array_push($this->instructions, $instruction);
    }

    /** Vygenerovani vytupniho XML. */
    private function generateXML()
    {
        $xml = new DOMDocument('1.0', 'UTF-8');
        $this->generateXmlProgram($xml);

        $xml->formatOutput = true;
        echo $xml->saveXML();
    }

    /**
     * Funkce pro vygenerovani XML dat do dokumentu.
     *
     * @param DOMDocument $document
     * @return void
     */
    private function generateXmlProgram($document)
    {
        $programElem = $document->createElement("program");
        $programElem->setAttribute('language', 'IPPcode20');

        foreach ($this->instructions as $instruction) {
            $instructionElem = $document->createElement("instruction");
            $instruction->setInstructionXml($document, $instructionElem);

            $programElem->appendChild($instructionElem);
        }

        $document->appendChild($programElem);
    }

    /**
     * Vypis napovedy.
     *
     * @return void
     */
    public function printHelp()
    {
        echo "IPP Projekt 2020
Autor: Michal Halabica (xhalab00)

Skript ocekava na standardnim vstupu instrukce jazyka IPPcode20.
Skript provede lexikalni a syntaktickou kontrolu a nasledne vypise na standardni vystup XML reprezentaci programu jazyka IPPcode20.

Priklady spusteni:

Spusteni zpracovani:
php parse.php <input.ippcode20

Napoveda:
php parse.php --help

Možno si nechat vygenerovat také statistiky skriptu:
--stats={cestaKSouboru}\tPovinný parametr, pokud jsou požadovány statistiky.
--loc\tTento parametr vypíše do statistik počet řádků s instrukcemi.
--comments\tTento parametr vypíše do statistik počet řádků, na kterých se vyskytuje komentář.
--labels\tTento parametr vypíše do statistik počet definovaných návěští.
--jumps\tTento parametr vypíše do statistik počet instrukcí pro skoky.

php parse.php --stats=file --loc --comments --labels --jumps <input.ippcode20
";
    }

    /**
     * Spusteni hlavniho chodu programu. Nacteni instrukce ze standardniho vstupu a jeji zpracovani.
     *
     * @param string[] $args Parametry na prikazove radce.
     * @return void
     */
    public function run($args)
    {
        $input = file('php://stdin');

        foreach ($input as $line => $instruction) {
            $instruction = preg_replace("/\s+/", " ", $instruction);

            $commentFields = explode('#', $instruction, 2);
            if (count($commentFields) > 1) {
                Statistics::incrementStats('comments');
            }

            $instruction = trim($commentFields[0]);

            if (empty($instruction))
                continue;

            $fields = explode(' ', trim($instruction));
            $this->addInstruction($fields, $line);
        }

        if ($this->haveHeader) {
            $this->generateXML();
            Statistics::saveStatistics($args);
        } else
            Output::error(Output::invalidOrMissingHeader, "Missing header row in source file.");
    }
}

$program = new Program();

if (in_array("--help", $argv)) {
    if ($argc > 2)
        Output::error(Output::invalidArgs, "Invalid arguments with help combination.");

    $program->printHelp();
} else if ($argc > 1) {
    Statistics::enableStatistics($argv);

    // Musi existovat parametr stats. 
    if (empty(Statistics::$statsFilename))
        Output::error(Output::invalidArgs, "Invalid arguments for statistics");

    $program->run($argv);
} else {
    $program->run($argv);
}
