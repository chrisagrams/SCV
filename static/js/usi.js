const populate_usi = (usis) => {
    if(document.querySelector("#usiObject") === null)
        return;
    const usiObject = document.querySelector("#usiObject").contentDocument;
    const psmList = usiObject.querySelector("#psm-list");
    const psms = Object.keys(usis);
    psms.forEach(psm => {
        let option = document.createElement("option");
        option.value = psm;
        option.textContent = psm;
        option.dataset.usi = JSON.stringify(usis[psm]); // Store the USI information for later access
        psmList.appendChild(option);
    });

    psmList.addEventListener("change", e => {
        const selectedOption = e.target.options[e.target.selectedIndex];
        const usi = JSON.parse(selectedOption.dataset.usi); // Retrieve the USI information from the selected option
        populate_pxid(usi);
    });

    if (psmList.options.length > 0) {
        psmList.selectedIndex = 0;
        const event = new Event('change', { bubbles: true }); // Create a new change event
        psmList.dispatchEvent(event); // Dispatch it on the psmList to trigger the population of pxid
    }
}

const populate_pxid = (usi) => {
    const usiObject = document.querySelector("#usiObject").contentDocument;
    const pxidList = usiObject.querySelector("#pxid-list");
    clear_pxid();
    Object.keys(usi).forEach(pxid => {
        let option = document.createElement("option");
        option.value = pxid;
        option.textContent = pxid;
        option.dataset.pxid = JSON.stringify(usi[pxid]);
        pxidList.appendChild(option);
    });

    pxidList.addEventListener("change", e => {
        const selectedOption = e.target.options[e.target.selectedIndex];
        const pxid = JSON.parse(selectedOption.dataset.pxid);
        populate_files(pxid);
    });

    if (pxidList.options.length > 0) {
        pxidList.selectedIndex = 0;
        const event = new Event('change', { bubbles: true }); // Create a new change event
        pxidList.dispatchEvent(event); // Dispatch it on the psmList to trigger the population of pxid
    }
}

const populate_files = (pxid) => {
    const usiObject = document.querySelector("#usiObject").contentDocument;
    const fileList = usiObject.querySelector("#file-list");
    clear_files();
    Object.keys(pxid).forEach(file => {
        let option = document.createElement("option");
        option.value = file;
        option.textContent = file;
        option.dataset.scans = JSON.stringify(pxid[file]);
        fileList.appendChild(option);
    });

    fileList.addEventListener("change", e => {
        const selectedOption = e.target.options[e.target.selectedIndex];
        const scans = JSON.parse(selectedOption.dataset.scans);
        populate_scans(scans);
    });

    if (fileList.options.length > 0) {
        fileList.selectedIndex = 0;
        const event = new Event('change', { bubbles: true }); // Create a new change event
        fileList.dispatchEvent(event);
    }
}

const populate_scans = (scans) => {
    const usiObject = document.querySelector("#usiObject").contentDocument;
    const scanList = usiObject.querySelector("#scan-list");
    clear_scans();
    Object.keys(scans).forEach(scan => {
        let option = document.createElement("option");
        option.value = scan;
        option.textContent = scan;
        option.dataset.charge = scans[scan];
        scanList.appendChild(option);
    })
    scanList.addEventListener("change", e => {
        populate_info();
    });

    if (scanList.options.length > 0) {
        scanList.selectedIndex = 0;
        const event = new Event('change', { bubbles: true }); // Create a new change event
        scanList.dispatchEvent(event);
    }

}

const clear_pxid = () => {
    const usiObject = document.querySelector("#usiObject").contentDocument;
    const pxidList = usiObject.querySelector("#pxid-list");
    while (pxidList.firstChild) {
        pxidList.removeChild(pxidList.firstChild);
    }
}

const clear_files = () => {
    const usiObject = document.querySelector("#usiObject").contentDocument;
    const fileList = usiObject.querySelector("#file-list");
    while (fileList.firstChild) {
        fileList.removeChild(fileList.firstChild);
    }
}

const clear_scans = () => {
    const usiObject = document.querySelector("#usiObject").contentDocument;
    const scanList = usiObject.querySelector("#scan-list");
    while (scanList.firstChild) {
        scanList.removeChild(scanList.firstChild);
    }
}

const set_loading = () => {
    const usiObject = document.querySelector("#usiObject").contentDocument;
    usiObject.querySelector(".parent-select-wrapper").classList.add("blur");
    usiObject.querySelector("#usiLoading").classList.remove("hide");
}

const unset_loading = () => {
    const usiObject = document.querySelector("#usiObject").contentDocument;
    usiObject.querySelector(".parent-select-wrapper").classList.remove("blur");
    usiObject.querySelector("#usiLoading").classList.add("hide");
}

let lorikeetClickListener = null;
const populate_info = () => {

    const usiObject = document.querySelector("#usiObject").contentDocument;
    const psmList = usiObject.querySelector("#psm-list");
    const pxidList = usiObject.querySelector("#pxid-list");
    const fileList = usiObject.querySelector("#file-list");
    const scanList = usiObject.querySelector("#scan-list");
    const lorikeetButton = usiObject.querySelector("#lorikeetButton");

    let psm_option = psmList.options[psmList.selectedIndex];
    let pxid_option = pxidList.options[pxidList.selectedIndex];
    let file_option = fileList.options[fileList.selectedIndex];
    let scan_option = scanList.options[scanList.selectedIndex];

     let usi = buildUSI(
                    pxid_option.textContent,
                    file_option.textContent,
                    scan_option.textContent,
                    psm_option.textContent,
                    parseInt(scan_option.dataset.charge));

    usiObject.querySelector("#generatedUSI").textContent = usi;
    usiObject.querySelector("#selectedFilename").textContent = file_option.textContent;
    usiObject.querySelector("#selectedScan").textContent = scan_option.textContent;
    usiObject.querySelector("#selectedCharge").textContent = scan_option.dataset.charge;

    if (lorikeetClickListener !== null) {
        lorikeetButton.removeEventListener("click", lorikeetClickListener);
    }

    lorikeetClickListener = () => {
        set_loading();
        localStorage.removeItem('lorikeetData');
        fetchFromRepo(usi, spectraURLS['PRIDE'])
            .then(result => {
                window.open("lorikeetPopup.html", "lorikeetPopup", "width=1100,height=750");
                localStorage.setItem('lorikeetData', JSON.stringify(repoToLorikeet(result)));
            })
            .catch(error => {
                console.error(error);
                window.alert("Error in fetching USI. USI possibly not found.");
            })
            .finally(() => {
                unset_loading();
            })
    }

    lorikeetButton.addEventListener("click", lorikeetClickListener);
}