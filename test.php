<?php

const INPUT_FILE_OPENING_ERROR = 11;
const WRONG_DIRECTORY_ERROR = 41;

function scan_directory($dir)
{
    $results= [];
    $files = scandir($dir);
    foreach($files as $file)
    {
        $path = realpath("$dir/$file");
        if (preg_match("/.+\.src/", $file))
        {
            array_push($results, $path);
        }
    }
    return $results;
}

function scan_directory_recursive($dir, &$results)
{
    $files = scandir($dir);
    foreach ($files as $file)
    {
        $path = realpath("$dir/$file");
        if (preg_match("/.+\.src/", $file))
        {
            array_push($results, $path);
        }
        else if (is_dir($path) && $file != "." && $file != "..")
        {
            scan_directory_recursive($path, $results);
        }
    }
    return $results;
}


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
$return_code = 0;
$output = null;
$jexamPath="/pub/courses/ipp/jexamxml";
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
        $directory_path = substr($argument, strpos($argument,"=") + 1);
    }
    else if ($argument == "--recursive")
    {
        $recursiveArg = true;
    }
    else if (preg_match("/--parse-script=.+\.php/", $argument))
    {
        $parseScriptArg = true;
    }
    else if (preg_match("/--int-script=.+\.py/", $argument))
    {
        $intScriptArg = true;
    }
    else if ($argument == "--parse-only")
    {
        $parseOnlyArg = true;
    }
    else if ($argument == "--int-only")
    {
        $intOnlyArg = true;
    }
    else if (preg_match("/--jexampath=.+/", $argument))
    {
        $jexampathArg = true;
    }
    else if ($argument == "--noclean")
    {
        $nocleanArg = true;
    }
//    else
//    {
//        echo ("unknown argument!\n");
//        exit(10);
//    }
}

if (!is_dir("tmp"))
{
    mkdir("tmp");
}
if($parseOnlyArg)
{
        if (!is_dir($directory_path) || !is_readable($directory_path))
        {
            printf("Couldn't reach the directory!\n");
            exit(WRONG_DIRECTORY_ERROR);
        }
        $recursiveArg ? $all_tests_array = scan_directory_recursive($directory_path, $all_tests_array) : $all_tests_array = scan_directory($directory_path);
        foreach ($all_tests_array as $test)
        {
            if (preg_match("/.+\.src/", $test))
            {
                $test_output_name = preg_replace("/\.src/","_test.out", substr($test, strrpos($test, '/') + 1));
                $input_file = preg_replace("/\.src/",".in", $test);
                $output_file = preg_replace("/\.src/",".out", $test);
                $return_code_file = preg_replace("/\.src/",".rc", $test);
                check_input_files($input_file, $output_file, $return_code_file);
                $return_code_file = fopen("$return_code_file", "r");
                $expected_return = fgets($return_code_file);
                fclose($return_code_file);
                exec("php8.1 parse.php < $test > ./tmp/$test_output_name", $output, $return_code);
                if ($expected_return == 0)
                {
                    exec("java -jar $jexamPath/jexamxml.jar ./tmp/$test_output_name $output_file delta.xml $jexamPath/options", $output, $return_code);
                    if ($return_code == 0)
                    {
                        $passed_tests++;
                    }
                    else
                    {
                        $failed_tests++;
                        array_push($failed_array, $test);
                    }
                }
                else
                {
                    if ($expected_return == $return_code)
                    {
                        $passed_tests++;
                    }
                    else
                    {
                        $failed_tests++;
                        array_push($failed_array, $test);
                    }
                }
            }
        }
        printf("list of failed tests:\n");
        print_r($failed_array);
        printf("failed tests = %d\npassed tests = %d\n", $failed_tests, $passed_tests);
}

if (!$nocleanArg)
{
    delete_tmp_files();
}
