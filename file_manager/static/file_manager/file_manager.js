const table_element = document.getElementById('table_body')
const file_path_element = document.getElementById("file_path")


function progress(n, id = "loading_bar") {
    const bar = document.getElementById(id)
    const progress = bar.querySelector('.progress-bar')
    progress.style.width = n
    if (n === '100%') {
        bar.style.display = 'none'
    } else {
        bar.style.display = 'inherit'
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
            th.classList.add('text-truncate')
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
            const dropdown_names = ['move', 'copy', 'delete']
            for (let j = 0; j < dropdown_names.length; j++) {
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
            tr.appendChild(td)
            table_element.appendChild(tr)
        }
    }
}

const modal = document.getElementById("dropdown_modal")
const input_field = document.getElementById('modal_input')
const confirm = modal.querySelector('.modal-footer button')
modal.addEventListener('show.bs.modal', event => {
    const input_funcs = ['move', 'copy']
    const single_input = ["create_folder", "create_file"]
    const button = event.relatedTarget;
    let path = button.getAttribute('data-bs-path')
    if (path === '.') {
        path = _current_path
    }
    const func_name = button.getAttribute('data-bs-function')
    const title = modal.querySelector('.modal-header h1')
    const body = modal.querySelector('.modal-body')
    title.textContent = func_name + ' file: ' + path
    let args = null
    let message = 'Name or path(relative to current path)'
    if (input_funcs.includes(func_name)) {
        args = [path]
        message = "Path(relative to root)"
    } else if (single_input.includes(func_name)) {
        args = []
    }
    if (args != null) {
        input_field.value = ''
        let label = modal.querySelector('label')
        label.textContent = message
        body.removeAttribute('hidden')
        confirm.onclick = () => {
            progress('25%')
            let tmp = ''
            if (args === []) {
                tmp = _current_path.join('/')
                if (tmp !== '') {
                    tmp += '/'
                }
            }
            args.push(tmp + input_field.value)
            file_operations(func_name)(args)
        }
    } else {
        input_field.value = path
        body.setAttribute('hidden', 'true')
        confirm.onclick = () => {
            progress('25%')
            file_operations(func_name)([path])
        }
    }
})

input_field.addEventListener("keyup", function (event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        confirm.click();
    }
});

modal.addEventListener('shown.bs.modal', () => {
    input_field.focus()
    input_field.select()
})

const upload_form = document.getElementById('upload_form')

async function upload_file(e) {
    let csrf_input = e.target[0]
    let data = new FormData()
    let file = e.target[1].files[0]
    data.append('file', file)
    data.append(csrf_input.name, csrf_input.value)
    const size = file.size

    let xhr = new XMLHttpRequest();
    xhr.open("POST", window.location.pathname);
    xhr.withCredentials = true;
    xhr.setRequestHeader('Current-Path', _current_path)
    xhr.onreadystatechange = () => {
        if (xhr.readyState !== 4) return;
        if (xhr.status === 201) {
            alert("upload succeeded")
            list_folder(_current_path)
        } else if (xhr.status === 400) {
            const message = JSON.parse(xhr.responseText)
            alert(message["message"])
        } else
            alert("upload failed with code " + xhr.status)
    }
    xhr.upload.addEventListener('progress', (e) => {
        progress(e.loaded / e.total * 100 + "%", "upload_bar")
    })
    xhr.send(data);
}

upload_form.addEventListener('submit', (e) => {
    e.preventDefault();
    upload_file(e).then()
})

