/* globals Chart:false */

(() => {
    'use strict'

    // Graphs
    const ctx = document.getElementById('myChart')
    // eslint-disable-next-line no-unused-vars
    const myChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [
                60,
                50,
                40,
                30,
                20,
                10,
                0
            ],
            datasets: [{
                label: 'CPU Usage',
                data: [
                    0.2,
                    0.3,
                    0.45,
                    0.34,
                    0.23,
                    0.32,
                    0.29
                ],
                lineTension: 0,
                backgroundColor: 'transparent',
                borderColor: '#007bff',
                borderWidth: 4,
                pointBackgroundColor: '#007bff'
            }]
        },
        options: {
            animation: false,
            title: {
                display: true,
                text: 'CPU Usage Graph'
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    boxPadding: 3
                },
                scales: {
                    xAxes: [{
                        type: 'time',
                        time: {
                            unit: 'second',
                            autoSkip:true,
                            maxTicks: 10
                        }
                    }],
                    yAxes: [{
                        min:0
                    }]
                }
            }
        }
    })
})()
