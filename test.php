<?php include 'html_generator.php';

/*

 * Autor: Tetauer Pavel
 * Login: xtetau00
 * Rok: 2021/2022

*/

const WRONG_ARGUMENTS_ERROR = 10;
const INPUT_FILE_OPENING_ERROR = 11;
const OUTPUT_FILE_OPENING_ERROR = 12;
const WRONG_DIRECTORY_ERROR = 41;

// funkce slouzici k naskenovani zadane slozky
function scan_directory($dir) : array
{
    $results= [];
    $files = scandir($dir);
    foreach($files as $file)
    {
        $path = realpath("$dir/$file");
        if (preg_match("/.+\.src/", $file))
        {
            $results[] = $path;
        }
    }
    return $results;
}

// funkce slouzici k naskenovani zadane slozky, pokud byl zadan argument --recursive
function scan_directory_recursive($dir, &$results)
{
    $files = scandir($dir);
    foreach ($files as $file)
    {
        $path = realpath("$dir/$file");
        if (preg_match("/.+\.src/", $file))
        {
            $results[] = $path;
        }
        else if (is_dir($path) && $file != "." && $file != "..")
        {
            scan_directory_recursive($path, $results);
        }
    }
    return $results;
}

/* funkce, ktera slouzi ke zkontrolovani testovacich souboru
    a pripadnemu vytvoreni novych prazdnych souboru, pokud se ve
    slozce nenachazely */
function check_input_files($input_file, $output_file, $return_code_file)
{
    if(!is_file($input_file))
    {
        $new_file = fopen($input_file, "w");
        fclose($new_file);
    }
    elseif(!is_readable($input_file))
    {
        fprintf(STDERR,"Couldn't open $input_file!");
        exit(INPUT_FILE_OPENING_ERROR);
    }
    if (!is_file($output_file))
    {
        $new_file = fopen($output_file, "w");
        fclose ($new_file);
    }
    elseif(!is_readable($output_file))
    {
        fprintf(STDERR,"Couldn't open $output_file!");
        exit(INPUT_FILE_OPENING_ERROR);
    }
    if (!is_file($return_code_file))
    {
        $new_file = fopen($return_code_file, "w");
        fprintf($new_file, "0");
        fclose ($new_file);
    }
    elseif(!is_readable($return_code_file))
    {
        fprintf(STDERR,"Couldn't open $return_code_file!");
        exit(INPUT_FILE_OPENING_ERROR);
    }
}

// funkce, ktera odstrani vytvorene pomocne soubory
function delete_tmp_files()
{
    $tmpdir = scandir("./tmp");
    $tmpdir = array_diff($tmpdir, array('.', ".."));
    foreach($tmpdir as $tmpfile)
    {
        unlink("./tmp/$tmpfile");
    }
    rmdir("tmp");
}

$directory_path = ".";
$all_tests_array = [];
$failed_tests = 0;
$failed_array = [];
$passed_tests = 0;
$passed_array = [];
$return_code = 0;
$output = null;
$jexamPath="/pub/courses/ipp/jexamxml";
$parse_script="./parse.php";
$int_script ="./interpret.py";
$recursiveArg=false;
$directoryArg=false;
$parseScriptArg=false;
$intScriptArg=false;
$parseOnlyArg=false;
$intOnlyArg=false;
$jexampathArg=false;
$nocleanArg=false;
$firstArg=true;


// cyklus pro parsovani argumentu a jejich kontrolu
foreach ($argv as $argument)
{
    if($firstArg)
    {
        $firstArg = false;
        continue;
    }
    // vypise napovedu, pripadne chybu pokud byly zadany i jine argumenty
    if ($argument == "--help")
    {
        if ($argc != 2)
        {
            fprintf(STDERR,"Can't use help with another argument!\n");
            exit(WRONG_ARGUMENTS_ERROR);
        }
        else
        {
            printf ("Použití: php8.1 test.php [parametry] < input_file
            
    parametry:
    --help - vypíše nápovědu, nelze kombinovat s jinými parametry
    --directory=path - testy bude hledat v zadaném adresáři
    --recursive - testy bude hledat nejen v zadaném adresáři, ale i rekurzivně ve všech jeho 
    podadresářích
    --parse-script=file - kde file je soubor se skriptem v PHP 8.1 pro parser
    --int-script=file - kde file je soubor se skriptem v Python 3.8 pro interpret 
    --parse-only - bude testován pouze parser
    --int-only bude testován pouze interpret
    --jexampath=path cesta k adresáři obsahující soubor jexamxml.jar s JAR balíčkem s ná-
    strojem A7Soft JExamXML a soubor s konfigurací jménem options
    
    chybové kódy: 
    10 - špatné argumenty, povolen je pouze samostatný argument --help
    11 - chyba při otevírání vstupních souborů (např. neexistence, nedostatečné oprávnění)
    12 - chyba při otevření výstupních souborů pro zápis(nedostatečné oprávnění)
    41 - jiná lexikální nebo syntaktická chyba zdrojového kódu zapsaného v IPPcode22\n");
            exit(0);
        }
    }
    else if (preg_match("/--directory=.+/", $argument))
    {
        $directoryArg = true;
        $directory_path = substr($argument, strpos($argument, "=") + 1);
    }
    else if ($argument == "--recursive")
    {
        $recursiveArg = true;
    }
    else if (preg_match("/--parse-script=.+\.php/", $argument))
    {
        if ($intOnlyArg)
        {
            fprintf(STDERR,"Can't use --parse-script with --int-only!\n");
            exit(WRONG_ARGUMENTS_ERROR);
        }
        $parseScriptArg = true;
        $parse_script = substr($argument, strpos($argument, "=") + 1);
        if (!is_readable($parse_script))
        {
            printf("Couldn't find the int script!\n");
            exit(WRONG_DIRECTORY_ERROR);
        }
    }
    else if (preg_match("/--int-script=.+\.py/", $argument))
    {
        if ($parseOnlyArg)
        {
            fprintf(STDERR,"Can't use --parse-only with --int-script!\n");
            exit(WRONG_ARGUMENTS_ERROR);
        }
        $intScriptArg = true;
        $int_script = substr($argument, strpos($argument, "=") + 1);
        if (!is_readable($int_script))
        {
            printf("Couldn't find the int script!\n");
            exit(WRONG_DIRECTORY_ERROR);
        }
    }
    else if ($argument == "--parse-only")
    {
        if ($intOnlyArg || $intScriptArg)
        {
            fprintf(STDERR,"Can't use --parse-only with --int-only or --int-script!\n");
            exit(WRONG_ARGUMENTS_ERROR);
        }
        $parseOnlyArg = true;
    }
    else if ($argument == "--int-only")
    {
        if ($parseOnlyArg || $jexampathArg || $parseScriptArg)
        {
            fprintf(STDERR,"Can't use --int-only with --jexampath, parse-only or --parse-script!\n");
            exit(WRONG_ARGUMENTS_ERROR);
        }
        $intOnlyArg = true;
    }
    else if (preg_match("/--jexampath=.+/", $argument))
    {
        if ($intOnlyArg)
        {
            fprintf(STDERR,"Can't use --int-only with --jexampath!\n");
            exit(WRONG_ARGUMENTS_ERROR);
        }
        $jexamPath = substr($argument, strpos($argument, "=") + 1);
        if (!is_readable($jexamPath))
        {
            printf("Couldn't reach the jexam path!\n");
            exit(WRONG_DIRECTORY_ERROR);
        }
        $jexampathArg = true;
    }
    else if ($argument == "--noclean")
    {
        $nocleanArg = true;
    }
    else
    {
        echo("unknown argument!\n");
        exit(10);
    }
}

// vytvori pomocnou slozku tmp
if (!is_dir("tmp"))
{
    mkdir("tmp");
}
// overi, zda lze do vytvorene slozky tmp zapisovat
if (!is_writable("./tmp"))
{
    printf("Couldn't write output files!\n");
    exit(OUTPUT_FILE_OPENING_ERROR);
}
// overi, zda zadana directory existuje a zda mame prava pro cteni
if (!is_dir($directory_path) || !is_readable($directory_path))
{
    printf("Couldn't reach the directory!\n");
    exit(WRONG_DIRECTORY_ERROR);
}

// ulozi vsechny testovaci soubory do pole $all_tests_only
$recursiveArg ? $all_tests_array = scan_directory_recursive($directory_path, $all_tests_array) : $all_tests_array = scan_directory($directory_path);

// hlavni cyklus, ve kterem se provadi veskere testovani
foreach ($all_tests_array as $src_file)
{
    $test_output_name = preg_replace("/\.src/", "_test.out", substr($src_file, strrpos($src_file, '/') + 1));
    $input_file = preg_replace("/\.src/", ".in", $src_file);
    $output_file = preg_replace("/\.src/", ".out", $src_file);
    $return_code_file = preg_replace("/\.src/", ".rc", $src_file);
    check_input_files($input_file, $output_file, $return_code_file);
    $return_code_file = fopen("$return_code_file", "r");
    $expected_return = fgets($return_code_file);
    fclose($return_code_file);

    // testuje se pouze parser
    if ($parseOnlyArg)
    {
        exec("php8.1 $parse_script < $src_file > ./tmp/$test_output_name", $output, $return_code);
        // ocekavany chybovy kod byl 0 a zaroven se z parseru vratil kod 0
        if ($expected_return == 0 and $return_code == 0)
        {
            exec("java -jar $jexamPath/jexamxml.jar ./tmp/$test_output_name $output_file delta.xml $jexamPath/options", $output, $return_code);
            if ($return_code == 0)
            {
                $passed_tests++;
                $passed_array[] = $src_file;
            }
            else
            {
                $failed_tests++;
                $failed_array[] = $src_file;
            }
        }
        // ocekavany kod nebyl 0 nebo se z parseru vratil nenulovy kod
        else
        {
            if ($expected_return == $return_code)
            {
                $passed_tests++;
                $passed_array[] = $src_file;
            }
            else
            {
                $failed_tests++;
                $failed_array[] = $src_file;
            }
        }
    }

    // testuje se pouze interpret
    else if ($intOnlyArg)
    {
        exec("python3 $int_script --source=$src_file --input=$input_file > ./tmp/$test_output_name", $output, $return_code);
        // ocekavany chybovy kod byl 0 a zaroven se z interpretu vratil kod 0
        if ($expected_return == 0 and $return_code == 0)
        {
            exec("diff ./tmp/$test_output_name $output_file", $output, $return_code);
            if ($return_code == 0)
            {
                $passed_tests++;
                $passed_array[] = $src_file;
            }
            else
            {
                $failed_tests++;
                $failed_array[] = $src_file;
            }
        }
        // ocekavany chybovy kod nebyl 0 nebo se z interpretu vratil nenulovy kod
        else
        {
            if ($expected_return == $return_code)
            {
                $passed_tests++;
                $passed_array[] = $src_file;
            }
            else
            {
                $failed_tests++;
                $failed_array[] = $src_file;
            }
        }
    }
    // testuje se interpret i parser zaroven
    else
    {
        // soubor, kam se ulozi xml reprezentace, ktera vyjde z parseru
        $parser_output = preg_replace("/\.src/", "_parser.out", substr($src_file, strrpos($src_file, '/') + 1));
        exec("php8.1 $parse_script < $src_file > ./tmp/$parser_output", $output, $return_code);
        // parser vratil return code 0, muze se pokracovat na interpret
        if ($return_code == 0)
        {
            exec("python3 $int_script --source=./tmp/$parser_output --input=$input_file > ./tmp/$test_output_name", $output, $return_code);
            // interpret vratil 0, otestuje se, zda maji stejny vystup
            if ($return_code == 0)
            {
                exec("diff ./tmp/$test_output_name $output_file", $output, $return_code);
                if ($return_code == 0 and $expected_return == 0)
                {
                    $passed_tests++;
                    $passed_array[] = $src_file;
                }
                else
                {
                    $failed_tests++;
                    $failed_array[] = $src_file;
                }
            }
            // interpret nevratil 0, zkontroluje se, zda navratova hodnota sedi s testovaci
            else
            {
                if ($expected_return == $return_code)
                {
                    $passed_tests++;
                    $passed_array[] = $src_file;
                }
                else
                {
                    $failed_tests++;
                    $failed_array[] = $src_file;
                }
            }
        }
        // parser vratil nenulovy navratovy kod, zkontroluje se, zda souhlasi s ocekavanym
        else
        {
            if ($expected_return == $return_code)
            {
                $passed_tests++;
                $passed_array[] = $src_file;
            }
            else
            {
                $failed_tests++;
                $failed_array[] = $src_file;
            }
        }
    }
}


$all_tests_num = sizeof($all_tests_array);
// generovani vystupniho HTML souboru pomoci funkci implementovanych v "html_generator.php"
if ($all_tests_num != 0)
{
    generate_HTML_file($failed_array, $failed_tests, $passed_array, $passed_tests, $all_tests_num);
}
// odstrani pomocne soubory
if (!$nocleanArg)
{
    delete_tmp_files();
}
