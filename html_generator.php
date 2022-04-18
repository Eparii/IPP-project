<?php

// zahajeni generovani HTML souboru
function HTML_generate_start()
{
    print ("<!DOCTYPE html>
<html lang=\"en\">
<head>
<title>IPP Tests output</title>
 <link rel=\"stylesheet\" href=\"styles.css\">
</head>
<body>\n");
}
// vygeneruje tabulku s vysledky testu
function HTML_generate_table($failed_tests_num, $passed_tests_num, $all_tests_num)
{
    // vypocita procentualni uspesnost zaokrouhlenou na 2 desetinna mista
    $successful_percentage = round($passed_tests_num/$all_tests_num * 100, 2);
    print ("\t<table>
        <tr>
            <th colspan='2'>Test stats</th>
        </tr>
        <tr>
            <td>Total tests</td>
            <td>$all_tests_num</td>
        </tr>
        <tr>
            <td>Passed tests</td>
            <td>$passed_tests_num</td>
        </tr>
        <tr>
            <td>Failed tests</td>
            <td>$failed_tests_num</td>
        </tr>
        <tr>
            <td>Successful percentage</td>
            <td><b>$successful_percentage%</b></td>
        </tr>
    </table>\n");
}

// vygeneruje seznamy uspesnych a neuspesnych testu
function HTML_generate_tests_lists($failed_array, $passed_array)
{
    print("\t<div class = \"tests_lists\">
        <div class = \"passed_list\">
            <h2>List of passed tests</h2>
            <p>\n");

    foreach ($passed_array as $passed_test)
    {
        print("\t\t\t\t$passed_test<br>\n");
    }

    print("\t\t\t</p>
        </div>
        <div class = \"failed_list\">
        <h2>List of failed tests</h2>
            <p>\n");

    foreach ($failed_array as $failed_test)
    {
        print("\t\t\t\t$failed_test<br>\n");
    }

    print("\t\t\t</p>
\t\t</div>
\t</div>\n");
}
// ukonci html soubor
function HTML_generate_end()
{
    print ("</body>\n</html>");
}

// hlavni funkce, ze ktere se vola cele generovani souboru
function generate_HTML_file($failed_array, $failed_tests_num, $passed_array, $passed_tests_num, $all_tests_num)
{
    HTML_generate_start();
    HTML_generate_table($failed_tests_num, $passed_tests_num, $all_tests_num);
    HTML_generate_tests_lists($failed_array, $passed_array);
    HTML_generate_end();
}