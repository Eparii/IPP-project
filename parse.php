<?php

/*

 * Autor: Tetauer Pavel
 * Login: xtetau00
 * Rok: 2021/2022

*/

const WRONG_ARGUMENTS_ERROR = 10;
const MISSING_HEADER_ERROR = 21;
const WRONG_OPCODE_ERROR = 22;
const SYNTACTIC_OR_SEMANTIC_ERROR = 23;
ini_set('display_errors', 'stderr');

/* funkce sloužící pro kontrolu escape sekvencí */
function check_escapes($code) : bool
{
    for ($i = 0; $i < strlen($code); $i++)
    {
        if ($code[$i] == "\\")
        {
            // pokud nalezne \, následující 3 znaky musí být čísla
            if (strlen($code) < $i + 3 || !is_numeric($code[$i+1]) || !is_numeric($code[$i+2]) || !is_numeric($code[$i+3]))
            {
                return false;
            }
            else
            {
                $i+=3;
            }
        }
    }
    return true;
}


/* overuje, zda se jedna o spravne zapsany label */
function is_label($code) : bool
{
    return preg_match("/^[a-zA-Z_$&%*!?-][a-zA-Z0-9_$&%*!?-]*$/", $code);
}

/* overi label a pokud je spravne zapsany, vytiskne odpovidajici XML */
function check_and_print_label($code, $arg_num, $is_last_arg, $line)
{
    if (!is_label($code))
    {
        print_error(SYNTACTIC_OR_SEMANTIC_ERROR, $line);
    }
    printf("\t\t<arg%d type=\"label\">%s</arg%d>\n", $arg_num, $code, $arg_num);
    if ($is_last_arg)
    {
        printf("\t</instruction>\n");
    }
}
/* overi typ a pokud je spravne zapsany, vytiskne odpovidajici XML */
function check_and_print_type($code, $arg_num, $is_last_arg, $line)
{
    if ($code == "string" || $code == "int" || $code == "bool")
    {
        printf("\t\t<arg%d type=\"type\">%s</arg%d>\n", $arg_num, $code, $arg_num);
    }
    else
    {
        print_error(SYNTACTIC_OR_SEMANTIC_ERROR, $line);
    }
    if ($is_last_arg)
    {
        printf("\t</instruction>\n");
    }
}

/* overi promennou a pokud je spravne zapsana, vytiskne odpovidajici XML */
function is_var($code) : bool
{
    return preg_match("/^(LF|GF|TF)@[a-zA-Z_$&%*!?-][a-zA-Z0-9_$&%*!?-]*$/", $code);
}

/* overi konstantu a pokud je spravne zapsana, vytiskne odpovidajici XML */
function is_const($code) : bool
{
    // jedna se o string
    if (preg_match("/^string@\S*$/", $code))
    {
        return (check_escapes($code));
    }
    // jedna se o bool se spravnou hodnotou
    else if (preg_match("/^bool@(false|true)$/", $code))
    {
        return true;
    }
    // jedna se o integer
    else if (preg_match("/^int@[+-]?[a-zA-Z0-9_$&%*!?-]+$/", $code))
    {
        return true;
    }
    // jedna se o nil s jedinou moznou hodnotou nil
    else if (preg_match("/^nil@nil$/", $code))
    {
        return true;
    }
    return false;
}


function check_and_print_var($code, $arg_num, $is_last_arg, $line)
{
    if (!is_var($code)) // nejedna se o promennou
    {
        print_error(SYNTACTIC_OR_SEMANTIC_ERROR, $line);
    }
    /*  nahradi znaky, ktere by delaly problem ve vysledne XML reprezentaci
        jejich odpovidajicimi XML entitami */
    $code = replace_problematic_characters($code);
    printf("\t\t<arg%d type=\"var\">%s</arg%d>\n", $arg_num, $code, $arg_num);
    if ($is_last_arg)
    {
        printf("\t</instruction>\n");
    }
}

/* funkce, slouzici na kontrolu a nasledny zapis konstanty */
function check_and_print_const($code, $arg_num, $is_last_arg, $line)
{
    if (!is_const($code))
    {
        print_error(SYNTACTIC_OR_SEMANTIC_ERROR, $line);
    }
    $code = replace_problematic_characters($code);
    $type = substr($code, 0, strpos($code, "@"));
    $value = substr($code, strpos($code, "@") + 1);
    printf("\t\t<arg%d type=\"%s\">%s</arg%d>\n",$arg_num, $type, $value, $arg_num);
    if ($is_last_arg)
    {
        printf("\t</instruction>\n");
    }
}
/* funkce, ktera kontroluje operandy, ktere mohou byt promenna i konstanta */
function check_and_print_symb($code, $arg_num, $is_last_arg, $line)
{
    if (is_var($code))
    {
        check_and_print_var($code, $arg_num,$is_last_arg, $line);
    }
    else if (is_const($code))
    {
        check_and_print_const($code, $arg_num,$is_last_arg, $line);
    }
    else
    {
        print_error(SYNTACTIC_OR_SEMANTIC_ERROR, $line);
    }
}

/* funkce vypisujici errory */
function print_error ($errorcode, $line)
{
    switch ($errorcode)
    {
        case WRONG_ARGUMENTS_ERROR:
            fprintf (STDERR,"Unknown argument, missing stdin or forbidden arguments combination!\n");
            exit (MISSING_HEADER_ERROR);
        case MISSING_HEADER_ERROR:
            fprintf (STDERR,"Missing or wrong header on line %d!\n", $line);
            exit (MISSING_HEADER_ERROR);
        case WRONG_OPCODE_ERROR:
            fprintf(STDERR,"Wrong or unknown operation code on line %d!\n", $line);
            exit(WRONG_OPCODE_ERROR);
        case SYNTACTIC_OR_SEMANTIC_ERROR:
            fprintf(STDERR,"Syntactic or semantic error on line %d!\n", $line);
            exit(SYNTACTIC_OR_SEMANTIC_ERROR);
    }
}
/* funkce odstranujici komentare a prebytecne bile znaky */
function remove_commentary_and_whitespaces ($line) : string
{
    $line = rtrim($line, "\n"); // odstrani novy radek
    $line = ltrim($line); // odstrani mezery na zacatku radku
    $line = preg_replace("/\s+/", ' ', $line); // odstrani prebytecne mezery uvnitr retezce
    if(str_contains($line, '#')) // odstrani komentar
    {
        $line = substr($line, 0, strpos($line, '#'));
    }
    // po odstraneni komentare odstrani pripadne vznikle mezery na konci radku
    while (str_ends_with($line,' '))
    {
        $line = rtrim($line, ' ');
    }
    return $line;
}

/* funkce nahrazujici znaky, ktere by delaly problemy v XML reprezentaci */
function replace_problematic_characters($line) : string
{
    $problematic = ["<", ">", "'", "\""];
    $replacement = ["&lt;", "&gt;", "&apos;", "&quot;"];
    $line = str_replace("&", "&amp;", $line);
    return str_replace($problematic, $replacement, $line);
}

$first = true;
if ($argc == 2)
{
    if ($argv[1] == "--help")
    {
        printf ("Použití: parser.php [--help] < input_file
    chybové kódy:
    10 - špatné argumenty, povolen je pouze samostatný argument --help
    21 - chybná nebo chybějící hlavička ve zdrojovém kódu zapsaném v IPPcode22
    22 - neznámý nebo chybný operační kód ve zdrojovém kódu zapsaném v IPPcode22
    23 - jiná lexikální nebo syntaktická chyba zdrojového kódu zapsaného v IPPcode22\n");
        exit(0);
    }
    else
    {
        print_error(WRONG_ARGUMENTS_ERROR, NULL);
        exit(10);
    }
}
elseif ($argc > 2)
{
    print_error(WRONG_ARGUMENTS_ERROR, NULL);
}
$lineCounter = 0;
$instructionCounter = 0;
if (ftell(STDIN) !== FALSE)
{
    print ("<?xml version=\"1.0\" encoding=\"UTF-8\"?> \n");
    while ($line = fgets(STDIN))
    {
        $lineCounter++;
        $line = remove_commentary_and_whitespaces($line);
        if ($line == "")
        {
            continue;
        }
        // pokud se jedna o prvni radek, musi obsahovat identifikator jazyka
        if ($first)
        {
            if ($line != ".IPPcode22")
            {
                print_error(MISSING_HEADER_ERROR, $lineCounter);
            }
            print ("<program language=\"IPPcode22\">\n");
            $first = false;
        }
        else
        {
            $splitted = explode(' ', $line);
            switch(strtoupper($splitted[0]))
            {
                case "MOVE":
                case "TYPE":
                case "INT2CHAR":
                case "STRLEN":
                case "NOT":
                    if (sizeof($splitted) == 3)
                    {
                        printf ("\t<instruction order=\"%d\" opcode=\"%s\">\n", ++$instructionCounter, strtoupper($splitted[0]));
                        check_and_print_var($splitted[1], 1, false, $lineCounter);
                        check_and_print_symb($splitted[2], 2, true, $lineCounter);
                    }
                    else
                    {
                        print_error(SYNTACTIC_OR_SEMANTIC_ERROR, $lineCounter);
                    }
                    break;
                case "POPFRAME":
                case "PUSHFRAME":
                case "CREATEFRAME":
                case "BREAK":
                case "RETURN":
                    if (sizeof($splitted) == 1)
                    {
                        printf ("\t<instruction order=\"%d\" opcode=\"%s\">\n\t</instruction>\n", ++$instructionCounter, strtoupper($splitted[0]));
                    }
                    else
                    {
                        print_error(SYNTACTIC_OR_SEMANTIC_ERROR, $lineCounter);
                    }
                    break;
                case "DEFVAR":
                case "POPS":
                    if (sizeof($splitted) == 2)
                    {
                        printf ("\t<instruction order=\"%d\" opcode=\"%s\">\n", ++$instructionCounter, strtoupper($splitted[0]));
                        check_and_print_var($splitted[1], 1, true, $lineCounter);
                    }
                    else
                    {
                        print_error(SYNTACTIC_OR_SEMANTIC_ERROR, $lineCounter);
                    }
                    break;
                case "LABEL":
                case "JUMP":
                case "CALL":
                    if (sizeof($splitted) == 2)
                    {
                        printf ("\t<instruction order=\"%d\" opcode=\"%s\">\n", ++$instructionCounter, strtoupper($splitted[0]));
                        check_and_print_label($splitted[1], 1, true, $lineCounter);
                    }
                    else
                    {
                        print_error(SYNTACTIC_OR_SEMANTIC_ERROR, $lineCounter);
                    }
                    break;
                case "PUSHS":
                case "EXIT":
                case "WRITE":
                case "DPRINT":
                    if (sizeof($splitted) == 2)
                    {
                        printf ("\t<instruction order=\"%d\" opcode=\"%s\">\n", ++$instructionCounter, strtoupper($splitted[0]));
                        check_and_print_symb($splitted[1], 1, true, $lineCounter);
                    }
                    else
                    {
                        print_error(SYNTACTIC_OR_SEMANTIC_ERROR, $lineCounter);
                    }
                    break;
                case "JUMPIFEQ":
                case "JUMPIFNEQ":
                    if (sizeof($splitted) == 4)
                    {
                        printf ("\t<instruction order=\"%d\" opcode=\"%s\">\n", ++$instructionCounter, strtoupper($splitted[0]));
                        check_and_print_label($splitted[1], 1, false, $lineCounter);
                        check_and_print_symb($splitted[2], 2, false, $lineCounter);
                        check_and_print_symb($splitted[3], 3, true, $lineCounter);
                    }
                    else
                    {
                        print_error(SYNTACTIC_OR_SEMANTIC_ERROR, $lineCounter);
                    }
                    break;
                case "GETCHAR":
                case "SETCHAR":
                case "CONCAT":
                case "AND":
                case "OR":
                case "STRI2INT":
                case "LT":
                case "GT":
                case "EQ":
                case "IDIV":
                case "MUL":
                case "SUB":
                case "ADD":
                    if (sizeof($splitted) == 4)
                    {
                        printf ("\t<instruction order=\"%d\" opcode=\"%s\">\n", ++$instructionCounter, strtoupper($splitted[0]));
                        check_and_print_var($splitted[1], 1, false, $lineCounter);
                        check_and_print_symb($splitted[2], 2, false, $lineCounter);
                        check_and_print_symb($splitted[3], 3, true, $lineCounter);
                    }
                    else
                    {
                        print_error(SYNTACTIC_OR_SEMANTIC_ERROR, $lineCounter);
                    }
                    break;
                case "READ":
                    if (sizeof($splitted) == 3)
                    {
                        printf ("\t<instruction order=\"%d\" opcode=\"%s\">\n", ++$instructionCounter, strtoupper($splitted[0]));
                        check_and_print_var($splitted[1], 1, false, $lineCounter);
                        check_and_print_type($splitted[2], 2, true, $lineCounter);
                    }
                    else
                    {
                        print_error(SYNTACTIC_OR_SEMANTIC_ERROR, $lineCounter);
                    }
                    break;
                default:
                    print_error(WRONG_OPCODE_ERROR, $lineCounter);
                    break;
            }
        }
    }
    printf("</program>\n");
}
else
{
    print_error(WRONG_ARGUMENTS_ERROR, NULL);
}
?>