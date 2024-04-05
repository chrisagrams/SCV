const USIValidatorURL = "https://proteomecentral.proteomexchange.org/api/proxi/v0.1/usi_validator";

const MassIVEURL = "https://massive.ucsd.edu/ProteoSAFe/proxi/v0.1/spectra";
const PeptideAtlasURL = "https://peptideatlas.org/api/proxi/v0.1/spectra";
const PRIDEURL = "https://www.ebi.ac.uk/pride/proxi/archive/v0.1/spectra";
const ProteomeCentralURL = "https://proteomecentral.proteomexchange.org/api/proxi/v0.1/spectra";

const spectraURLS = {
    'MassIVE': MassIVEURL,
    'PeptideAtlas': PeptideAtlasURL,
    'PRIDE': PRIDEURL,
    'ProteomeCentral': ProteomeCentralURL
}

const buildUSI = (PXID, name, scan_num, sequence, charge) => {
    return `mzspec:${PXID}:${name}:scan:${scan_num}:${sequence}/${charge}`;
}

const deconstructUSI = (usi) => {
    const parts = usi.split(":");

    if (parts.length !== 6 || parts[0] !== 'mzspec' || parts[3] !== 'scan') {
        throw new Error('Invalid USI format');
    }

    const PXID = parts[1];
    const name = parts[2];
    const scan_num = parts[4];

    const sequenceCharge = parts[5].split("/");
    const sequence = sequenceCharge[0];
    const charge = sequenceCharge[1];

    return { 'pxid': PXID, 'name': name, 'scan_num': scan_num, 'sequence': sequence, 'charge': charge };
};

const validateUSIs = (USIs) => {
    if (!Array.isArray(USIs)) {
        return Promise.reject(new Error("Input must be an array of strings."));
    }
    return new Promise((resolve, reject) => {
        fetch(USIValidatorURL, {
            method: "POST",
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(USIs)
        })
        .then(response => response.json())
        .then(json => {
            Object.entries(json['validation_results']).forEach((entry) => {
                const [key, value] = entry;
                if(value['error_code'] != null)
                    reject(new Error(value['error_message']));
                if(!value['is_valid'])
                    reject(new Error("Not a valid USI."));
            });
            resolve(json);
        })
        .catch(error => {
            reject(error);
        });
    });
}

const fetchFromRepo = (USI, repoURL) => {
    return new Promise((resolve, reject) => {
        validateUSIs([USI])
            .then(() => {
                fetch(repoURL + "?" + new URLSearchParams({
                    resultType: 'full',
                    usi: USI
                }))
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Response not OK.');
                    }
                    return response.json();
                })
                .then(json => resolve(json))
                .catch(error => reject(error));
            })
            .catch(error => reject(error));
    });
}

const repoToLorikeet = (repoResult) => {
    let result = {
        'sequence': null,
        'scanNum': null,
        'charge': null,
        'precursorMz': null,
        'fileName': null,
        'peaks': null,
    }

    let attributes = repoResult[0]['attributes'];
    let mzs = repoResult[0]['mzs'];
    let intensities = repoResult[0]['intensities'];
    let usi = deconstructUSI(repoResult[0]['usi']);

    result['scanNum'] = usi['scan_num'];
    result['fileName'] = usi['name'];
    result['sequence'] = usi['sequence'];
    result['charge'] = usi['charge'];

    attributes.forEach(i => {
        switch(i.name) {
            case "scan number":
                result['scanNum'] = parseInt(i.value);
                break;
            case "isolation window target m/z":
                result["precursorMz"] = parseFloat(i.value);
                break;
            case "charge state":
                result["charge"] = parseInt(i.value);
                break;
            case "spectrum name":
                result["fileName"] = i.value;
                break;
            case "unmodified peptide sequence":
                result["sequence"] = i.value;
                break;
        }
    });

    result['peaks'] = mzs.map((element, index) => [element, intensities[index]]);

    return result;
}

try {
    module.exports = { validateUSIs, fetchFromRepo, repoToLorikeet};
 } catch (e) {}