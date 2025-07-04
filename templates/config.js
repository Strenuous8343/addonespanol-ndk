function loadData() {
    const currentUrl = window.location.href;
    let data = currentUrl.match(/\/([^\/]+)\/configure$/);
    if (data && data[1].startsWith("ey")) {
        data = atob(data[1]);
        data = JSON.parse(data);
        document.getElementById('debrid-api').value = data.debridKey;
        document.getElementById('tmdb-api').value = data.tmdbApi;
        document.getElementById('service').value = data.service;
        if(data.maxSize) {
            document.getElementById('maxSize').value = data.maxSize;
        }
        if(data.selectedQualityExclusion && Array.isArray(data.selectedQualityExclusion)) {
            data.selectedQualityExclusion.forEach(q => {
                let elem = document.getElementById(q);
                if(elem) elem.checked = true;
            });
        }
    }
}

loadData();

function getLink(method) {
    const addonHost = new URL(window.location.href).protocol.replace(':', '') + "://" + new URL(window.location.href).host;
    const debridApi = document.getElementById('debrid-api').value;
    const tmdbApi = document.getElementById('tmdb-api').value;
    const service = document.getElementById('service').value;
    let selectedCatalogs = getCheckedOrder();
    const maxSize = document.getElementById('maxSize').value;
    
    let selectedQualityExclusion = [];
    const qualityList = ['4k', '1080p', '720p', '480p', 'rips', 'cam', 'unknown'];
    qualityList.forEach(q => {
        if (document.getElementById(q).checked) {
            selectedQualityExclusion.push(q);
        }
    });

    let data = {
        addonHost,
        service,
        debridKey: debridApi,
        debrid: 'true',
        metadataProvider: 'cinemeta',
        tmdbApi,
        maxSize,
        selectedQualityExclusion,
        selectedCatalogs
    };

    if ((debridApi === '') || (tmdbApi === '') || (maxSize === '')) {
        alert('Please fill all required fields');
        return false;
    }
    let stremio_link = `${window.location.host}/${btoa(JSON.stringify(data))}/manifest.json`;
    console.log(stremio_link);
    if (method === 'link') {
        window.open(`stremio://${stremio_link}`, "_blank");
    } else if (method === 'copy') {
        const link = window.location.protocol + '//' + stremio_link;

        if (!navigator.clipboard) {
            alert('Your browser does not support clipboard');
            console.log(link);
            return;
        }

        navigator.clipboard.writeText(link).then(() => {
            alert('Link copied to clipboard');
        }, () => {
            alert('Error copying link to clipboard');
        });
    }
}

function toggleCheckbox(id) {
    const checkbox = document.getElementById(id);
    checkbox.checked = !checkbox.checked;
}

function toggleSelectAll() {
    const checkboxes = document.querySelectorAll('input[name="catalogos"]');
    const allChecked = Array.from(checkboxes).every(checkbox => checkbox.checked);
    checkboxes.forEach(checkbox => {
        checkbox.checked = !allChecked;
    });
}


// Catalog Drag n Drop
const catalogList = document.getElementById('catalog-list');

let draggedItem = null;

// Event listener para iniciar el arrastre
catalogList.addEventListener('dragstart', (e) => {
    draggedItem = e.target;
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', e.target.outerHTML);
    setTimeout(() => e.target.classList.add('hidden'), 0);
});

// Event listener para permitir soltar
catalogList.addEventListener('dragover', (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';

    const draggingOver = e.target.closest('.draggable-item');
    if (draggingOver && draggingOver !== draggedItem) {
        const bounding = draggingOver.getBoundingClientRect();
        const offset = e.clientY - bounding.top;
        if (offset > bounding.height / 2) {
            catalogList.insertBefore(draggingOver, draggedItem);
        } else {
            catalogList.insertBefore(draggedItem, draggingOver);
        }
    }
});

// Event listener para soltar el elemento
catalogList.addEventListener('drop', (e) => {
    e.preventDefault();
    const dropIndex = [...catalogList.children].indexOf(draggedItem);
    draggedItem.classList.remove('hidden');
    draggedItem = null;
});

// Event listener para limpiar el estado si el arrastre es cancelado
catalogList.addEventListener('dragend', () => {
    if (draggedItem) draggedItem.classList.remove('hidden');
    draggedItem = null;
});

// Función para obtener el nuevo orden
function getOrder() {
    return [...catalogList.children].map(item => item.dataset.id);
}

// Función para obtener el nuevo orden de los marcados
function getCheckedOrder() {
    return [...catalogList.children]
        .filter(item => item.querySelector('input[type="checkbox"]').checked)
        .map(item => item.dataset.id);
}
