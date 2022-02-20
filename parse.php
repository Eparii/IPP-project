<?php

function RemoveNewlineAndCommentary ($line)
{
    $line = rtrim($line, "\n");
    if(strpos($line, '#'))
    {
        $line = substr($line, 0, strpos($line, '#'));
    }
    while (substr($line, -1) == ' ')
    {
        $line = rtrim($line, ' ');
    }
    return $line;
}


ini_set('display_errors', 'stderr');
echo("nejaka povinna hlavicka \n");
$first = true;
$file = fopen($argv[1], "r"); //TODO potom predelat na stdin

//if ($argc > 1)
//{
//    if ($argv[1] == "--help")
//    {
//        echo ("Usage: parser.php [options] <inputFile");
//        echo("\n");
//        exit(0);
//    }
//    else
//    {
//        exit(10);
//    }
//}

while ($line = fgets($file)) // TODO prepsat na stdin
{
    $line = RemoveNewlineAndCommentary($line);
    if ($first)
    {
        if ($line != ".IPPcode22")
        {
            exit (21);
        }
        $first = false;
    }
    else
    {
        $splitted = explode(' ', $line);
        switch(strtoupper($splitted[0]))
        {
            case 'BREAK':
            case 'RETURN':
                //TODO nejaka picovina co to ma delat
            case 'DEFVAR':
                echo ("\t<instruction opcode =".strtoupper($splitted[0]).">");
                if (preg_match("/(LF|GF|TF)@[a-zA-Z][a-zA-Z0-9]*/", $splitted[1]))
                    {
                        echo "ok";
                    }
        }
    }
}
echo "\n";

