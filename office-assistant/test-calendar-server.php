<?php
// Simple PHP script to test calendar layout server-side
header('Content-Type: text/html; charset=utf-8');

function generateCalendar($year, $month) {
    // Create first and last day of month
    $firstDay = new DateTime("$year-" . sprintf("%02d", $month) . "-01");
    $lastDay = clone $firstDay;
    $lastDay->modify('last day of this month');

    $daysInMonth = (int)$lastDay->format('d');
    $startingDayOfWeek = (int)$firstDay->format('w'); // 0 = Sunday

    echo "<h2>September 2025 Calendar Analysis</h2>\n";
    echo "<p><strong>First day:</strong> " . $firstDay->format('Y-m-d (l)') . "</p>\n";
    echo "<p><strong>Last day:</strong> " . $lastDay->format('Y-m-d (l)') . "</p>\n";
    echo "<p><strong>Days in month:</strong> $daysInMonth</p>\n";
    echo "<p><strong>Starting day of week:</strong> $startingDayOfWeek (0=Sun)</p>\n";

    // Generate calendar grid
    $calendar = [];
    $cellIndex = 0;

    // Leading empty cells
    for ($i = 0; $i < $startingDayOfWeek; $i++) {
        $calendar[] = [
            'type' => 'empty',
            'day' => '',
            'row' => floor($cellIndex / 7) + 1,
            'col' => ($cellIndex % 7) + 1,
            'index' => $cellIndex
        ];
        $cellIndex++;
    }

    // Month days
    for ($day = 1; $day <= $daysInMonth; $day++) {
        $calendar[] = [
            'type' => 'day',
            'day' => $day,
            'row' => floor($cellIndex / 7) + 1,
            'col' => ($cellIndex % 7) + 1,
            'index' => $cellIndex,
            'isTarget' => ($day >= 21 && $day <= 27)
        ];
        $cellIndex++;
    }

    // Trailing empty cells
    while ($cellIndex < 42) {
        $calendar[] = [
            'type' => 'empty',
            'day' => '',
            'row' => floor($cellIndex / 7) + 1,
            'col' => ($cellIndex % 7) + 1,
            'index' => $cellIndex
        ];
        $cellIndex++;
    }

    echo "<h3>Calendar Layout (42 cells)</h3>\n";
    echo "<pre>\n";
    echo "Row | Sun  Mon  Tue  Wed  Thu  Fri  Sat\n";
    echo "----+--------------------------------\n";

    for ($row = 1; $row <= 6; $row++) {
        $rowData = sprintf("%d   | ", $row);
        for ($col = 1; $col <= 7; $col++) {
            $cell = null;
            foreach ($calendar as $c) {
                if ($c['row'] == $row && $c['col'] == $col) {
                    $cell = $c;
                    break;
                }
            }
            $dayStr = $cell['day'] ? sprintf("%2d", $cell['day']) : "  ";
            $marker = (isset($cell['isTarget']) && $cell['isTarget']) ? '*' : ' ';
            $rowData .= $dayStr . $marker . ' ';
        }
        echo $rowData . "\n";
    }
    echo "</pre>\n";

    echo "<h3>Target dates 21-27 positions:</h3>\n";
    echo "<ul>\n";
    foreach ($calendar as $cell) {
        if (isset($cell['isTarget']) && $cell['isTarget']) {
            echo "<li>Day {$cell['day']}: Row {$cell['row']}, Col {$cell['col']}, Index {$cell['index']}</li>\n";
        }
    }
    echo "</ul>\n";

    echo "<h3>HTML Calendar Rendering Test:</h3>\n";
    echo "<div class='calendar-test-grid'>\n";

    foreach ($calendar as $cell) {
        $classes = ['calendar-day'];
        if ($cell['type'] === 'empty') {
            $classes[] = 'empty';
        }
        if (isset($cell['isTarget']) && $cell['isTarget']) {
            $classes[] = 'target-date';
        }

        $classStr = implode(' ', $classes);
        $content = $cell['day'] ? "<div class='day-number'>{$cell['day']}</div>" : '';

        echo "<div class='$classStr' data-row='{$cell['row']}' data-col='{$cell['col']}'>\n";
        echo "  $content\n";
        echo "</div>\n";
    }

    echo "</div>\n";

    return $calendar;
}

?>
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Server-Side Calendar Test</title>
    <link rel="stylesheet" href="css/main.css">
    <link rel="stylesheet" href="css/components.css">
    <style>
        .calendar-test-grid {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            grid-template-rows: repeat(6, 1fr);
            gap: 1px;
            background-color: #e9ecef;
            height: 480px;
            max-width: 800px;
            margin: 20px 0;
        }
        .target-date {
            background-color: #ffeb3b !important;
            border: 2px solid #f44336 !important;
        }
        .target-date .day-number {
            font-weight: bold;
            color: #d32f2f;
        }
        pre {
            background: #f5f5f5;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
        }
    </style>
</head>
<body>
    <h1>Calendar Layout Server-Side Test</h1>

    <?php
    $calendar = generateCalendar(2025, 9); // September 2025
    ?>

    <h3>Analysis:</h3>
    <p><strong>Expected:</strong> Dates 21-27 should all be in row 4 of the 6-row grid.</p>
    <p><strong>CSS Fix:</strong> The .calendar-days class should have <code>grid-template-rows: repeat(6, 1fr)</code> and a fixed height.</p>
    <p><strong>Visual Test:</strong> Yellow highlighted dates (21-27) should form a complete row in the grid above.</p>

</body>
</html>