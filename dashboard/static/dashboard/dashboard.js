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