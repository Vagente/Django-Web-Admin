function formatBytes(bytes, decimals) {
    if (bytes === 0) return '0 Bytes';
    let k = 1024,
        dm = decimals || 2,
        sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'],
        i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

function decodeHtml(html) {
    let txt = document.createElement("textarea");
    txt.innerHTML = html;
    return txt.value;
}

function seconds_to_string(seconds) {
    return luxon.DateTime.fromSeconds(seconds).toLocaleString({
        year: 'numeric',
        month: 'numeric',
        day: 'numeric',
        hour: 'numeric',
        minute: 'numeric'
    })
}

function update_table(input) {
    let ids = ["#folder-fill", "#file-embark-fill"]
    let table = document.getElementById("table_body")
    for (let idx = 0; idx < 2; idx++) {
        const files = input[idx]
        for (let i = 0; i < files.length; i++) {
            let tr = document.createElement("tr");
            let th = document.createElement("th");
            th.setAttribute("scope", "row");
            let svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
            svg.setAttribute("class", "bi");
            let use = document.createElementNS("http://www.w3.org/2000/svg", "use");
            let id = ids[idx]
            use.setAttribute("href", id);
            let text = document.createTextNode(files[i][0]);

            th.appendChild(svg).appendChild(use);
            th.appendChild(text);
            tr.appendChild(th);

            let funcs = [seconds_to_string, (x) => x, formatBytes]
            for (let j = 0; j < 3; j++) {
                let td = document.createElement("td")
                td.innerText = funcs[j](files[i][j + 1])
                tr.appendChild(td)
            }
            table.appendChild(tr)
        }
    }
}

const socket = new WebSocket(
    'wss://localhost/ws/xterm/'
)