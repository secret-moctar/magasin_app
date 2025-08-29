document.addEventListener('DOMContentLoaded', () => {
    const searchTool = document.getElementById('searchTool');
    const searchEmployee = document.getElementById('searchEmployee');
    const table = document.getElementById('toolsTable').getElementsByTagName('tbody')[0];

    function filterTable() {
        const toolQuery = searchTool.value.toLowerCase();
        const empQuery = searchEmployee.value.toLowerCase();

        Array.from(table.rows).forEach(row => {
            const toolID = row.cells[0].textContent.toLowerCase();
            const empName = row.cells[2].textContent.toLowerCase();

            if (toolID.includes(toolQuery) && empName.includes(empQuery)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    searchTool.addEventListener('input', filterTable);
    searchEmployee.addEventListener('input', filterTable);
});
