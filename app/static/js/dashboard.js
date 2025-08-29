document.addEventListener('DOMContentLoaded', async function() {
    try {
        // Fetch data from Flask API
        const response = await fetch("{{ url_for('view.cart') }}");
        const data = await response.json();

        // Destructure API values
        const { total_tools,active_tools, active_percent,maintenance_tools, out_of_service_tools  } = data;

        // ----------------- Status Chart -----------------
        const statusCtx = document.getElementById('statusChart').getContext('2d');
        new Chart(statusCtx, {
            type: 'doughnut',
            data: {
                labels: ['Available', 'In Maintenance', 'Out of Service'],
                datasets: [{
                    data: [active_tools, maintenance_tools, out_of_service_tools],
                    backgroundColor: ['#10B981', '#F59E0B', '#EF4444']
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });

        // ----------------- Inventory Chart (example) -----------------
        const inventoryCtx = document.getElementById('inventoryChart').getContext('2d');
    new Chart(inventoryCtx, {
    type: 'doughnut',
    data: {
        labels: ['Active %', 'Total Tools'],
        datasets: [{
            label: 'Inventory Stats',
            data: [active_percent, total_tools],
            backgroundColor: ['#3B82F6', '#6366F1']
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: { position: 'bottom' }
        }
    }
});
    } catch (error) {
        console.error("Error loading dashboard data:", error);
    }
});
