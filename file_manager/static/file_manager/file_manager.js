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
            const name = files[i][0]
            let text = document.createTextNode(name);

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

            // Dots dropdown
            let td = document.createElement('td')
            let div = document.createElement('div')
            div.classList.add('dropstart')
            div.addEventListener('dblclick', (e) => {
                e.stopPropagation()
            })
            let dot_svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
            dot_svg.classList.add('bi')
            dot_svg.classList.add('dropdown-toggle')
            dot_svg.classList.add('dot_svg')
            dot_svg.setAttribute('data-bs-toggle', 'dropdown')
            let dot_use = document.createElementNS("http://www.w3.org/2000/svg", "use");
            dot_use.setAttribute('href', '#dots')
            div.appendChild(dot_svg).appendChild(dot_use)
            let ul = document.createElement("ul")
            ul.classList.add('dropdown-menu')
            const dropdown_names = ['move']
            for (let j = 0; j < 1; j++) {
                let li = document.createElement('li')
                let button = document.createElement('button')
                button.classList.add('dropdown-item')
                button.textContent = dropdown_names[j]
                button.setAttribute('data-bs-toggle', 'modal')
                button.setAttribute('data-bs-target', '#dropdown_modal')
                button.setAttribute('data-bs-path', _current_path.concat([name]).join('/'))
                button.setAttribute('data-bs-function', dropdown_names[j])
                li.appendChild(button)
                ul.appendChild(li)
            }
            ul.addEventListener('contextmenu', (e) => {
                e.stopPropagation()
            })
            div.appendChild(ul)
            td.appendChild(div)
            tr.addEventListener('contextmenu', (e) => {
                e.preventDefault();
                const x = e.clientX
                const y = e.clientY
                const dropdown = new bootstrap.Dropdown(dot_svg)
                dropdown.show()
                ul.style.transform = null
                ul.style.margin = null
                ul.style.position = 'fixed'
                ul.style.inset = `${y}px auto auto ${x}px`
                // ul.classList.add('show')
            })
            tr.appendChild(td)

            table_element.appendChild(tr)
        }
    }
}

const modal = document.getElementById("dropdown_modal")
const input_field = document.getElementById('modal_input')
const confirm = modal.querySelector('.modal-footer button')
modal.addEventListener('show.bs.modal', event => {
    const input_funcs = ['move']
    const all_funcs = [move_file]
    const button = event.relatedTarget;
    const path = button.getAttribute('data-bs-path')
    const func_name = button.getAttribute('data-bs-function')
    const title = modal.querySelector('.modal-header h1')
    title.textContent = func_name + ' file'
    input_field.value = path
    confirm.onclick = () => {
        for (let i = 0; i < 1; i++) {
            if (input_funcs[i] === func_name) {
                all_funcs[i]([path, input_field.value])
            }
        }
    }
})

input_field.addEventListener("keyup", function (event) {
    console.log(event)
    if (event.key === 'Enter') {
        event.preventDefault();
        confirm.click();
    }
});

modal.addEventListener('shown.bs.modal', () => {
    input_field.focus()
    input_field.select()
})