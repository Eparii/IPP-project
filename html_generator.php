<?php

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
function HTML_generate_table($failed_tests_num, $passed_tests_num, $all_tests_num)
{
    $successful_percentage = $all_tests_num/$passed_tests_num * 100;
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
function HTML_generate_end()
{
    print ("</body>\n</html>");
}

function generate_HTML_file($failed_array, $failed_tests_num, $passed_array, $passed_tests_num, $all_tests_num)
{
    for ($i = 0; $i < 50; $i++)
    {
        $failed_array[] = "dsadsadsadsadsadsadsadsadsadsadsadsa";
    }
    HTML_generate_start();
    HTML_generate_table($failed_tests_num, $passed_tests_num, $all_tests_num);
    HTML_generate_tests_lists($failed_array, $passed_array);
    HTML_generate_end();
}