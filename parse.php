<?php

function RemoveNewlineAndCommentary ($line): string
{
    $line = rtrim($line, "\n");
    if(strpos($line, '#'))
    {
        $line = substr($line, 0, strpos($line, '#'));
    }
    while (str_ends_with($line,' '))
    {
        $line = rtrim($line, ' ');
    }
    return $line;
}


ini_set('display_errors', 'stderr');
echo"<?xml version=\"1.0\" encoding=\"UTF-8\"?> \n";
$first = true;
$file = fopen($argv[1], "r"); //TODO potom predelat na stdin

//if ($argc > 1)
//{
//    if ($argv[1] == "--help")
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
    $line = RemoveNewlineAndCommentary($line);
    if ($first)
    {
        if ($line != ".IPPcode22")
        {
            printf ("Missing or wrong header on line %d!\n", $lineCounter);
            exit (21);
        }
        echo "<program language=\"IPPcode22\">\n";
        $first = false;
    }
    else
    {
        $splitted = explode(' ', $line);
        switch(strtoupper($splitted[0]))
        {
            case "MOVE":
                break;
            case "POPFRAME":
            case "PUSHFRAME":
            case "CREATEFRAME":
            case "BREAK":
            case "RETURN":
                if (sizeof($splitted) == 1)
                {
                    printf ("\t<instruction order=\"%d\" opcode=\"%s\">\n\t<\instruction>\n", ++$instructionCounter, strtoupper($splitted[0]));
                }
                else
                {
                    printf("Unexpected %s arguments on line %d\n", strtoupper($splitted[0]), $lineCounter);
                    exit (22);

                }
                break;
            case "DEFVAR":
                printf ("\t<instruction order=\"%d\" opcode=\"%s\">\n", ++$instructionCounter, strtoupper($splitted[0]));
                if (sizeof($splitted) != 1 && preg_match("/(LF|GF|TF)@[a-zA-Z_$&%*!?-][a-zA-Z0-9_$&%*!?-]*/", $splitted[1]))
                    {
                        printf("\t\t<arg1 type=\"var\">%s</arg1>\n\t<\instruction>\n", $splitted[1]);
                    }
                else
                {
                    printf("Wrong DEFVAR arguments on line %d\n", $lineCounter);
                    exit (22);
                }
                break;
            case "LABEL":
            case "JUMP":
            case "CALL":
                printf ("\t<instruction order=\"%d\" opcode=\"%s\">\n", ++$instructionCounter, strtoupper($splitted[0]));
                if (sizeof($splitted) != 1 && preg_match("/[a-zA-Z_$&%*!?-][a-zA-Z0-9_$&%*!?-]*/", $splitted[1]))
                {
                    printf("\t\t<arg1 type=\"label\">%s</arg1>\n\t<\instruction>\n", $splitted[1]);
                }
                else
                {
                    printf("Wrong CALL arguments on line %d\n", $lineCounter);
                    exit (22);
                }
                break;
        }
    }
}

printf("</program>\n");

