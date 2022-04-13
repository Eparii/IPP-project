<?php
if (!isset($ARG_PARSE)) include 'ArgumentParser.class.php';
if (!isset($HELPER)) include 'helper.php';
if (!isset($TEST_LOADER)) include 'TestLoader.class.php';
if (!isset($HTML_GENERATOR)) include 'HTMLGenerator.class.php';

$config = parseCommandLineArgs();
if ($config->help) {
    echo "Testovací skript pro spuštění testů nad analyzátorem a interpretem kódu IPPCode20.

Test je možno ovlivnit následujícími parametry (Všechny parametry jsou volitelné a mají nastavenou výchozí hodnotu.):

--help\tOtevře nápovědu.
--directory={path}\tCesta k testům. Výchozí je './'.
--recursive\tZapnutí vyhledávání testů bude probíhat rekurzivně.
--parse-script={filepath}\Nastavení cesty k analyzátoru kódu IPPCode20. Cesta musí obsahovat i název souboru. Výchozí je './parse.php'.
--int-script={filepath}\tNastavení cesty k interpreteru kódu IPPCode20. Cesta musí obsahovat i název souboru. Výchozí je './interpret.py'.
--parse-only\tSpuštění testů pouze nad analyzátorem kódu. Nesmí se kombinovat s přepínači --int-script a --int-only.
--int-only\tSpuštění testů pouze nad interpretací kódu IPPCode20. Nesmí se kombinovat s přepínači --parse-script a --parse-only
--jexamxml={filepath}\tNastavení cesty k porovnávacímu nástroji jexamxml. Výchozí je (/pub/courses/ipp/jexamxml/jexamlxml.jar). Předpokládá se, že konfigurační soubor bude ve stejném adresáři.

";

    exit(AppCodes::Success);
}

$tests = TestsLoader::findTests($config);
$testResults = [];
foreach ($tests as $key => $test) {
    try {
        $test->initTest();
        $testResults[$key] = $test->runTest($config);
    } catch (Exception $e) {
        output($e->getMessage(), true);
    }
}

HTMLGenerator::render($testResults, $config);
exit(AppCodes::Success);
