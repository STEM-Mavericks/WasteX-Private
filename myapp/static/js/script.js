document.addEventListener('DOMContentLoaded', function() {
    var ctx = document.getElementById('wasteChart').getContext('2d');

    // Check if total_dry and total_wet are defined
    var totalDry = {{ total_dry | tojson }};
    var totalWet = {{ total_wet | tojson }};
    
    console.log('Total Dry Waste:', totalDry);
    console.log('Total Wet Waste:', totalWet);
    
    if (typeof totalDry === 'number' && typeof totalWet === 'number') {
        var wasteChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Dry Waste', 'Wet Waste'],
                datasets: [{
                    label: 'Waste Data (kg)',
                    data: [totalDry, totalWet],
                    backgroundColor: ['#ff6384', '#36a2eb'],
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Weight (kg)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Waste Type'
                        }
                    }
                }
            }
        });
    } else {
        console.error('Total waste data is not defined or is not a number. Values:', totalDry, totalWet);
    }
});
