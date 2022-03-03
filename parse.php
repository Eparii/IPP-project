<?php

const MISSING_HEADER_ERROR = 21;
const WRONG_OPCODE_ERROR = 22;
const SYNTACTIC_OR_SEMANTIC_ERROR = 23;
ini_set('display_errors', 'stderr');

function is_label($code) : bool
{
    if (preg_match("/^[a-zA-Z_$&%*!?-][a-zA-Z0-9_$&%*!?-]*$/", $code))
    {
        return true;
    }
    return false;
}

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

function is_var($code) : bool
{
    if (preg_match("/^(LF|GF|TF)@[a-zA-Z_$&%*!?-][a-zA-Z0-9_$&%*!?-]*$/", $code))
    {
        return true;
    }
    return false;
}

function is_const($code) : bool
{
    if (preg_match("/^string@\S*$/", $code))
    {
        return true;
    }
    else if (preg_match("/^bool@(false|true)$/", $code))
    {
        return true;
    }
    else if (preg_match("/^int@[+-]?[a-zA-Z0-9_$&%*!?-]+$/", $code))
    {
        return true;
    }
    else if (preg_match("/^nil@nil$/", $code))
    {
        return true;
    }
    return false;
}


function check_and_print_var($code, $arg_num, $is_last_arg, $line)
{
    if (!is_var($code))
    {
        print_error(SYNTACTIC_OR_SEMANTIC_ERROR, $line);
    }
    printf("\t\t<arg%d type=\"var\">%s</arg%d>\n", $arg_num, $code, $arg_num);
    if ($is_last_arg)
    {
        printf("\t</instruction>\n");
    }
}

function check_and_print_const($code, $arg_num, $is_last_arg, $line)
{
    if (!is_const($code))
    {
        print_error(SYNTACTIC_OR_SEMANTIC_ERROR, $line);
    }
    $type = substr($code, 0, strpos($code, "@"));
    $value = substr($code, strpos($code, "@") + 1);
    printf("\t\t<arg%d type=\"%s\">%s</arg%d>\n",$arg_num, $type, $value, $arg_num);
    if ($is_last_arg)
    {
        printf("\t</instruction>\n");
    }
}

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


function print_error ($errorcode, $line)
{
    switch ($errorcode)
    {
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

function remove_commentary_and_whitespaces ($line) : string
{
    $line = rtrim($line, "\n");
    $line = ltrim($line);
    $line = preg_replace("/\s+/", ' ', $line);
    if(str_contains($line, '#'))
    {
        $line = substr($line, 0, strpos($line, '#'));
    }
    while (str_ends_with($line,' '))
    {
        $line = rtrim($line, ' ');
    }
    return $line;
}

function replace_problematic_characters($line) : string
{
    $problematic = ["<", ">"];
    $replacement = ["&lt;", "&gt;"];
    $line = str_replace("&", "&amp;", $line);
    $line = str_replace($problematic, $replacement, $line);
    return $line;
}

print ("<?xml version=\"1.0\" encoding=\"UTF-8\"?> \n");
$first = true;
$file = fopen($argv[1], "r"); //TODO potom predelat na stdin

//if ($argc > 1)
//{
// ($argv[1] == "--help")
//    {
//        echo "Usage: parser.php [options] <inputFile\n";
//        exit(0);
//    }
//    else
//    {
//        exit(10);
//    }
//}

$lineCounter = 0;
$instructionCounter = 0;
while ($line = fgets($file)) // TODO prepsat na stdin
{
    $lineCounter++;
    $line = remove_commentary_and_whitespaces($line);
    $line = replace_problematic_characters($line);
    if ($line == "")
    {
        continue;
    }
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
                if (sizeof($splitted) != 1)
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

