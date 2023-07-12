const set_demo = () => {
    document.querySelector('#psm_textarea').value =
        "{EQNEASPTPR\n" +
        "YCQEQDMCCR\n" +
        "ELAPGLHLR\n" +
        "GVVSDNCYPFSGR\n" +
        "C[143]TCHEGGHWECDQEPCLVDPDMIK}[group1]\n" +
        "GRADECALPYLGATCYCDLFCN[115]R\n" +
        "GTNECDIETFVLGVWGR\n" +
        "EQNEASPTPR\n" +
        "GNYGWQAGN[115]HSAFWGMTLDEGIR\n" +
        "CPNGQVDSNDIYQVTPAYR\n" +
        "DLSWQVRSLLLDHNR\n" +
        "CNCALRPLCTWLR\n" +
        "RPGSRNRPGYGTGYF\n" +
        "RPDGDAASQPRTPILLLR\n" +
        "QSLRQELYVQDYASIDWPAQR\n" +
        "GTNGSQIWDTSFAIQALLEAGAHHR\n" +
        "ETLNQGLDFCRRKQR\n" +
        "SYFTDLPKAQTAHEGALN[115]GVTFYAK\n" +
        "CDGEANVFSDLHSLRQFTSR\n" +
        "ETFHGLKELAFSYLVWDSK\n" +
        "IKNIYVSDVLNMK";
    get_psm_ptm(document.querySelector('#psm_textarea').value);
    let color_choosers = document.querySelectorAll('.colorChooser');
    color_choosers[0].value = '#0022ff';
    color_choosers[1].value = '#ff00f7';
    color_choosers[2].value = '#00ff08';
    document.querySelectorAll('.mdc-checkbox').forEach(i => {i.querySelector('input').checked = true});
    document.querySelector("#background_color").value = "#FFFFFF";
    selected_ptms.add("group1");
    selected_ptms.add("N[115]");
    selected_ptms.add("C[143]");
}


document.querySelector('#nextDiv').addEventListener("click", e => {send_job();});

const checkbox_template = document.createElement('div');
checkbox_template.classList.add('mdc-touch-target-wrapper');
checkbox_template.innerHTML = '<div class="mdc-touch-target-wrapper">\n' +
                            '  <div class="mdc-checkbox mdc-checkbox--touch">\n' +
                            '    <input oninput="checkbox_handler(this);"type="checkbox"\n' +
                            '           class="mdc-checkbox__native-control"\n' +
                            '           id="checkbox-1"/>\n' +
                            '    <div class="mdc-checkbox__background">\n' +
                            '      <svg class="mdc-checkbox__checkmark"\n' +
                            '           viewBox="0 0 24 24">\n' +
                            '        <path class="mdc-checkbox__checkmark-path"\n' +
                            '              fill="none"\n' +
                            '              d="M1.73,12.91 8.1,19.28 22.79,4.59"/>\n' +
                            '      </svg>\n' +
                            '      <div class="mdc-checkbox__mixedmark"></div>\n' +
                            '    </div>\n' +
                            '    <div class="mdc-checkbox__ripple"></div>\n' +
                            '  </div>\n' +
                            '</div>';

const ptm_map = new Set();
const selected_ptms = new Set();
const regx_group = /(\(([\w]+)\)\[\d+\.?\d+\])/gm;
const regx = /(\w{1}\[\d+\.?\d+\])/gm;
const regx_psm_group = /\{([^\}]+)\}\[([^\]]+)\]|([^\n]+)/gms;

 const createPtmCard = (ptm, id=null) => {
    const div = document.createElement('div');
    div.classList.add('ptm-card');
    if (id) div.id = id;

    const p = document.createElement('p');
    p.textContent = ptm;

    const checkbox = checkbox_template.cloneNode(true);
    checkbox.dataset.ptm = ptm;

    const colorChooser = document.createElement('input');
    colorChooser.classList.add('colorChooser');
    colorChooser.type = 'color';
    colorChooser.value = '#ff0000';
    colorChooser.dataset.ptm = ptm;

    div.append(checkbox, p, colorChooser);

    return div;
}

const add_to_ptm_grid = (ptm) => {
    const ptmGrid = document.querySelector('#ptm-grid');
    const id = ptm.replace('[', '_').replace(']', '_');
    const ptmCard = createPtmCard(ptm, id);
    ptmGrid.append(ptmCard);
}


const remove_from_ptm_grid = (ptm) => {
    let ptmGrid = document.querySelector('#ptm-grid');
    ptmGrid.querySelector("#"+ptm.replace('[', '_').replace(']', '_')).remove();
}

const get_psm_ptm = (input) => {
    // ptm_map = new Set();
    let new_ptm_map = new Set();

    // clear_ptm_grid();

    let groups  = {};
    groups['unlabeled'] = [];
    let matches = Array.from(input.matchAll(regx_psm_group));
    matches.forEach(i => {
        console.log(i);
        if(i.length > 3 && i[1] !== undefined && i[2] !== undefined) {
            new_ptm_map.add(i[2]);
            groups[i[2]] = i[1].split(/\r?\n/);
            groups[i[2]].forEach(pep => {
                let ptm_matches = pep.match(regx);
                if (ptm_matches !=  null) {
                    ptm_matches.forEach(match => {
                        new_ptm_map.add(match);
                    });
                }
            })
        }
        else if(i.length > 3 && i[3] !== undefined) {
            groups['unlabeled'].push(i[3]);
            let ptm_matches = i[3].match(regx);
            if (ptm_matches !=  null) {
                ptm_matches.forEach(match => {
                    new_ptm_map.add(match);
                });
            }
        }
    });

    let toRemove = new Set(
        [...ptm_map].filter(x => !new_ptm_map.has(x)));

    let toAdd = new Set(
        [...new_ptm_map].filter(x => !ptm_map.has(x)));

    console.log(toAdd);
    console.log(toRemove);

    toAdd.forEach(i => {ptm_map.add(i); add_to_ptm_grid(i);});
    toRemove.forEach(i => {ptm_map.delete(i); remove_from_ptm_grid(i);});

    return groups;
}

const checkbox_handler = (checkbox) => {
    if(checkbox.checked)
        selected_ptms.add(checkbox.parentNode.parentNode.parentNode.dataset.ptm);
    else
        selected_ptms.delete(checkbox.parentNode.parentNode.parentNode.dataset.ptm);
}


const get_selected_ptms = () => {
    let colorChoosers = document.querySelectorAll('.colorChooser');
    let ptms = {};

    selected_ptms.forEach(ptm => {
        colorChoosers.forEach(chooser => {
            if (chooser.dataset.ptm == ptm) {
                // ptms.push(JSON.stringify({[ptm]:chooser.value}));
                let group_match = ptm.match(regx_group);
                if(group_match != null) {
                    group_match.forEach(m => {
                        let par_regex = /([\w]+)/gm;
                        let num_regex = /(\[\d+\.?\d+\])/gm;
                        let num = m.match(num_regex);
                        let sub = m.match(par_regex);

                        for(let i = 0; i < sub[0].length; i++)
                            ptms[sub[0].charAt(i) + num[0]] = get_rgb_arr(chooser.value);
                    })

                }
                else
                    ptms[ptm] = get_rgb_arr(chooser.value);

            }
        });
    });
    return ptms;
}

const show_error = (text) => {
    let error = document.querySelector('#error_box');
        error.querySelector("#error_message").innerText = text;
        error.style.opacity = 1;
        error.style.transform = 'translate(-50%, 0%)';

    setTimeout(() => {
        error.style.opacity = 0;
        error.style.transform = 'translate(-50%, -100%)';
    }, 5000);
}

const send_job = () => {
    let ptms = get_selected_ptms();
    let body = {
        psms: get_psm_ptm(document.querySelector("#psm_textarea").value),
        ptm_annotations: ptms,
        background_color: get_glmol_color(document.querySelector('#background_color').value),
        species: species_menu.value
    };

    let form = new FormData();

    form.append('job', JSON.stringify(body));

    let user_file = document.querySelector("#user_upload").files[0];
    if (user_file)
        form.append('file', user_file);

    fetch('/job', {
        method: 'POST',
        body: form
    })
    .then(async response => {
        if (response.ok)
            return response.json();
        else
            throw new Error('Error in fetch /job', {
                cause: {status: response.status, response: await response.json()}
            });
    })
    .then(json => {
        console.log("received:" + json);
        transition_to_submitted(json['job_number']);
    })
    .catch(error => {
        console.error(error);
        console.error(error.cause);
        switch (error.cause.status)
        {
            case 400:
                show_error(error.cause.response.detail[0].msg);
                break;
            case 500:
                show_error("Internal server error");
                break;
        }

    });
}


const species_menu = new mdc.select.MDCSelect(document.querySelector('.mdc-select'));

const copy_to_clipboard = () => {
    let text = document.querySelector("#urlArea").querySelector('a').textContent;
    navigator.clipboard.writeText(text);
}

const transition_to_submitted = (job_number) => {
    let main = document.querySelector("#main");
    main.scrollTop = 0;
    main.style.overflowY = "hidden";
    let content = document.querySelector("#content");
    content.style.opacity = "0";
    content.addEventListener("transitionend", e=> {
        let submitted = document.querySelector("#submitted");
        submitted.style.opacity = "1";
        submitted.style.zIndex = "1";
        let urlField = document.querySelector("#urlField");
        urlField.textContent = window.location.href + "view?job="+job_number;
        urlField.href = window.location.href + "view?job="+job_number;

    });
}
document.querySelector("#copy_button").addEventListener("click", e => {
    copy_to_clipboard();
});

const gen_hex = (r, g, b) => {
    return ~~(r * 255) << 16 ^ ~~(g * 255) << 8 ^ ~~(b * 255);
}

const get_glmol_color = (hex) => {
    const r = parseInt(hex.substr(1,2), 16)
    const g = parseInt(hex.substr(3,2), 16)
    const b = parseInt(hex.substr(5,2), 16)
    return gen_hex(r/255, g/255, b/255);
}

const get_rgb_arr = (hex) => {
    const r = parseInt(hex.substr(1,2), 16)
    const g = parseInt(hex.substr(3,2), 16)
    const b = parseInt(hex.substr(5,2), 16)
    return [r, g, b];
}
