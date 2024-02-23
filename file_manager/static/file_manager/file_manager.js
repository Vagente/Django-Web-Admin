const table_element = document.getElementById('table_body')
const file_path_element = document.getElementById("file_path")
const _bar = document.getElementById("bar")
const _progress = document.getElementById("progress")

function progress(n) {
    _progress.style.width = n
    if (n === '0%') {
        _bar.style.display = 'none'
    } else {
        _bar.style.display = 'inherit'
    }
}

function formatBytes(bytes, decimals) {
    if (bytes === 0) return '0 Bytes';
    let k = 1024,
        dm = decimals || 2,
        sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'],
        i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
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

function clear_file_path() {
    file_path_element.innerText = ''
    append_path('Root', [], true)
}

function append_path(name, path, is_root = false) {
    let li = document.createElement('li')
    if (!is_root) {
        let svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        let use = document.createElementNS("http://www.w3.org/2000/svg", "use");
        svg.setAttribute('class', 'bi')
        use.setAttribute('href', '#chevron-right')
        li.appendChild(svg).appendChild(use)
    }
    li.setAttribute('class', 'list-group-item')
    let button = document.createElement('button')
    button.setAttribute('class', 'btn')
    button.textContent = name
    button.onclick = () => {
        progress('25%')
        change_path(path)
        list_folder(path)
        progress('75%')
    }
    li.appendChild(button)
    file_path_element.appendChild(li)
}

function update_file_path(path) {
    for (let i = 0; i < path.length; i++) {
        append_path(path[i], path.slice(0, i + 1))
    }

}

function update_table(input) {
    table_element.innerText = ''
    let ids = ["#folder-fill", "#file-embark-fill"]
    for (let idx = 0; idx < 2; idx++) {
        const files = input[idx]
        for (let i = 0; i < files.length; i++) {
            let tr = document.createElement("tr");
            let th = document.createElement("th");
            th.setAttribute("scope", "row");
            let svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
            svg.setAttribute("class", "bi");
            let use = document.createElementNS("http://www.w3.org/2000/svg", "use");
            let id = ids[idx];
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
            if (idx === 0) {
                tr.addEventListener("dblclick", folder_dblclick(text.textContent))
            }
            let td = document.createElement('td')
            let dot_svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
            dot_svg.classList.add('bi')
            let dot_use = document.createElementNS("http://www.w3.org/2000/svg", "use");
            dot_use.setAttribute('href', '#dots')
            td.appendChild(dot_svg).appendChild(dot_use)
            tr.appendChild(td)

            table_element.appendChild(tr)
        }
    }
}
