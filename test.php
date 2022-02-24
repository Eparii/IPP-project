<?php

$recursiveArg=false;
$directoryArg=false;
$parseScriptArg=false;
$intScriptArg=false;
$parseOnlyArg=false;
$intOnlyArg=false;
$jexampathArg=false;
$nocleanArg=false;

foreach ($argv as $argument)
{
    if ($argument == "--help")
    {
        if ($argc != 2)
        {
            echo("You can't use '--help' with another argument!\n");
            exit(1);
        }
        else
        {
            echo("help\n");
            exit(0);
        }
    }
    else if (preg_match("/--directory=.+/", $argument))
    {
        $directoryArg = true;
        echo ("directory vole\n");
    }
    else if ($argument == "--recursive")
    {
        $recursiveArg = true;
        echo ("rekurzivni vole\n");
    }
    else if (preg_match("/--parse-script=.+\.php/", $argument))
    {
        $parseScriptArg = true;
        echo ("parse Script vole\n");
    }
    else if (preg_match("/--int-script=.+\.py/", $argument))
    {
        $intScriptArg = true;
        echo ("interpret script vole\n");
    }
    else if ($argument == "--parse-only")
    {
        $parseOnlyArg = true;
        echo ("parse only vole\n");

    }
    else if ($argument == "--int-only")
    {
        $intOnlyArg = true;
        echo("int only vole\b");
    }
    else if (preg_match("/--jexampath=.+/", $argument))
    {
        $jexampathArg = true;
        echo ("jexampath vole\n");
    }
    else if ($argument == "--noclean")
    {
        $nocleanArg = true;
        echo ("noclean vole\n");
    }
//    else
//    {
//        echo ("unknown argument!\n");
//        exit(10);
//    }
}

if($parseOnlyArg)
{
    if (!$recursiveArg)
    {
        $dir = scandir(".");
        foreach ($dir as $file)
        {
            if (preg_match("/.+\.src/", $file))
            {
                $filename = preg_replace("/\.src/","_test.out", $file);
                exec("php8.1 parse.php test.src > $filename");
                xmldi
            }
        }
    }
}