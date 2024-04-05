const populate_usi = (usis) => {
    const usiObject = document.querySelector("#usiObject").contentDocument;
    const psmList = usiObject.querySelector("#psm-list");
    usis.forEach(usi => {
        let option = document.createElement("option");
        option.value = usi.psm;
        option.textContent = usi.psm;
        option.dataset.pxid = usi.pxid; // Store the pxid in the option for later access
        option.dataset.filename = usi.filename;
        option.dataset.scan = usi.scan;
        option.dataset.charge = usi.charge;
        psmList.appendChild(option);
    });

    psmList.addEventListener("change", e => {
        const selectedOption = e.target.options[e.target.selectedIndex];
        const pxid = selectedOption.dataset.pxid; // Retrieve the pxid from the selected option
        if (pxid) {
            populate_pxid([pxid]);
        }
    });

    if (psmList.options.length > 0) {
        psmList.selectedIndex = 0;
        const event = new Event('change', { bubbles: true }); // Create a new change event
        psmList.dispatchEvent(event); // Dispatch it on the psmList to trigger the population of pxid
    }
}

const populate_pxid = (pxids) => {
    const usiObject = document.querySelector("#usiObject").contentDocument;
    const pxidList = usiObject.querySelector("#pxid-list");
    clear_pxid();
    for (let pxid in pxids) {
        let option = document.createElement("option");
        option.value = pxids[pxid];
        option.textContent = pxids[pxid];
        pxidList.appendChild(option);
    }

    pxidList.addEventListener("change", e => {
        populate_info();
    });

    if (pxidList.options.length > 0) {
        pxidList.selectedIndex = 0;
        const event = new Event('change', { bubbles: true }); // Create a new change event
        pxidList.dispatchEvent(event); // Dispatch it on the psmList to trigger the population of pxid
    }
}

const clear_pxid = () => {
    const usiObject = document.querySelector("#usiObject").contentDocument;
    const pxidList = usiObject.querySelector("#pxid-list");
    while (pxidList.firstChild) {
        pxidList.removeChild(pxidList.firstChild);
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
    const lorikeetButton = usiObject.querySelector("#lorikeetButton");

    console.log(psmList.options[psmList.selectedIndex]);

    let psm_option = psmList.options[psmList.selectedIndex];
    let pxid_option = pxidList.options[pxidList.selectedIndex];

     let usi = buildUSI(
                    pxid_option.textContent,
                    psm_option.dataset.filename,
                    psm_option.dataset.scan,
                    psm_option.textContent,
                    psm_option.dataset.charge);

    usiObject.querySelector("#generatedUSI").textContent = usi;
    usiObject.querySelector("#selectedFilename").textContent = psm_option.dataset.filename;
    usiObject.querySelector("#selectedScan").textContent = psm_option.dataset.scan;
    usiObject.querySelector("#selectedCharge").textContent = psm_option.dataset.charge;

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