function loadData() {
    const currentUrl = window.location.href;
    let data = currentUrl.match(/\/([^\/]+)\/configure$/);
    if (data && data[1].startsWith("ey")) {
        data = atob(data[1]);
        data = JSON.parse(data);
        document.getElementById('debrid-api').value = data.debridKey;
        document.getElementById('debrid-http').value = data.debridHttp;
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
    const debridHttp = document.getElementById('debrid-http').value;
    const tmdbApi = document.getElementById('tmdb-api').value;
    const service = document.getElementById('service').value;
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
        debridHttp: debridHttp,
        debrid: 'true',
        metadataProvider: 'cinemeta',
        tmdbApi,
        maxSize,
        selectedQualityExclusion
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
