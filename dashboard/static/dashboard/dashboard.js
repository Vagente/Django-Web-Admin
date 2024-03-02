const formats = ['years', 'months', 'days', 'hours', 'minutes']
const uptime_element = document.getElementById("uptime")
const server_time = document.getElementById("server_time")
const timezone = document.getElementById("timezone")

function update_uptime() {
    const uptime = dateTime.now().diff(boot_date, formats)
    let text = ""
    let loop = 0
    for (const key in uptime.values) {
        loop += 1
        let found = false
        const num = Math.round(uptime[key])
        if (!(num === 0) || found) {
            found = true
            const num = Math.round(uptime[key])
            text += `${num} ${key}`
            if (loop < formats.length) {
                text += `, `
            }
        }
    }
    uptime_element.innerText = text

}

function update_server_time() {
    const time = dateTime.now().setZone(_server_timezone)
    server_time.innerText = time.toLocaleString({
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: 'numeric',
        minute: 'numeric'
    })
}

function update_data() {
    update_server_time()
    update_uptime()
}

update_server_time()
update_uptime()
setInterval(update_data, 60 * 1000)

const _time = dateTime.now().setZone(_server_timezone)
timezone.innerText = `UTC${_time.offset / 60}`

let ws_protocol = 'ws://'
if (window.location.protocol === 'https:')
    ws_protocol = 'wss://'
const socket = new WebSocket(
    ws_protocol + location.host + '/ws/stats/'
)


const cpu_usage_element = document.getElementById("cpu_usage")
const memory_usage_element = document.getElementById("memory_usage")
const swap_usage_element = document.getElementById("swap_usage")
const disk_usage_element = document.getElementById("disk_usage")
const _stats_elements = [null, memory_usage_element, swap_usage_element, disk_usage_element]

function formatBytes(bytes, decimals) {
    if (bytes === 0) return '0 Bytes';
    let k = 1024,
        dm = decimals || 2,
        sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'],
        i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

socket.onmessage = function (e) {
    let data = JSON.parse(e.data);
    cpu_usage_element.textContent = data[0] + '%'
    for (let i = 1; i < 4; i++) {
        const used = formatBytes(data[i][1])
        const total = formatBytes(data[i][2])
        const text = `${used} (${data[i][0]}%) of ${total}`
        _stats_elements[i].textContent = text
    }
}


// const ctx = document.getElementById('myChart')
// const data = {
//     labels: [
//         'Red',
//         'Blue',
//         'Yellow'
//     ],
//     datasets: [{
//         label: 'My First Dataset',
//         data: [300, 50, 100],
//         backgroundColor: [
//             'rgb(255, 99, 132)',
//             'rgb(54, 162, 235)',
//             'rgb(255, 205, 86)'
//         ],
//         hoverOffset: 4
//     }]
// };
// const config = {
//     type: 'pie',
//     data: data,
// };
//
// const my_chart = new Chart(ctx, config)