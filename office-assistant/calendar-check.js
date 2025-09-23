// Simple Node.js-style script to check calendar rendering
// Run this in browser console or adapt for server-side

// Mock Date to September 2025 for testing
const testDate = new Date(2025, 8, 1); // September 1, 2025

// Calculate calendar grid for September 2025
const year = testDate.getFullYear(); // 2025
const month = testDate.getMonth(); // 8 (September)

const firstDay = new Date(year, month, 1); // Sep 1, 2025
const lastDay = new Date(year, month + 1, 0); // Sep 30, 2025
const daysInMonth = lastDay.getDate(); // 30 days
const startingDayOfWeek = firstDay.getDay(); // What day of week Sep 1 falls on

console.log('September 2025 Calendar Debug:');
console.log('First day:', firstDay.toDateString());
console.log('Last day:', lastDay.toDateString());
console.log('Days in month:', daysInMonth);
console.log('Starting day of week:', startingDayOfWeek, '(0=Sun, 6=Sat)');

// Generate the actual calendar layout
let calendar = [];
let cellIndex = 0;

// Leading empty cells
for (let i = 0; i < startingDayOfWeek; i++) {
    calendar.push({ type: 'empty', day: '', row: Math.floor(cellIndex / 7) + 1, col: (cellIndex % 7) + 1 });
    cellIndex++;
}

// Month days
for (let day = 1; day <= daysInMonth; day++) {
    calendar.push({
        type: 'day',
        day: day,
        row: Math.floor(cellIndex / 7) + 1,
        col: (cellIndex % 7) + 1,
        isTarget: day >= 21 && day <= 27
    });
    cellIndex++;
}

// Trailing empty cells to complete 42 cells (6 weeks × 7 days)
while (cellIndex < 42) {
    calendar.push({ type: 'empty', day: '', row: Math.floor(cellIndex / 7) + 1, col: (cellIndex % 7) + 1 });
    cellIndex++;
}

console.log('\nCalendar Layout (42 cells):');
console.log('Row | Sun  Mon  Tue  Wed  Thu  Fri  Sat');
console.log('----+--------------------------------');

for (let row = 1; row <= 6; row++) {
    let rowData = `${row}   | `;
    for (let col = 1; col <= 7; col++) {
        const cell = calendar.find(c => c.row === row && c.col === col);
        const dayStr = cell.day ? cell.day.toString().padStart(2, ' ') : '  ';
        const marker = cell.isTarget ? '*' : ' ';
        rowData += `${dayStr}${marker} `;
    }
    console.log(rowData);
}

console.log('\nTarget dates 21-27 positions:');
calendar.filter(c => c.isTarget).forEach(cell => {
    console.log(`Day ${cell.day}: Row ${cell.row}, Col ${cell.col}`);
});

console.log('\nExpected CSS grid positions for dates 21-27:');
console.log('These should all be in row 4 of the 6-row grid');
console.log('If they appear distorted, the CSS grid is not working properly');