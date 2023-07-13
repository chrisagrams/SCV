class CoverageCard {
  protein_id;
  name;
  description;
  percent_coverage;
  coverage_arr;
  sequence;
  is_visible;
  ptms;
  card;
  canvas;
  ctx;
  sequence_p;

  constructor(protein_id, name, description, percent_coverage, coverage_arr, sequence, is_visible, ptms) {
    this.protein_id = protein_id;
    this.name = name;
    this.description = description;
    this.percent_coverage = percent_coverage;
    this.coverage_arr = coverage_arr;
    this.sequence = sequence;
    this.is_visible = is_visible;
    this.ptms= ptms;
  }

  createCard() {
    let textDiv = document.createElement('div');

    let p = document.createElement('p');
        p.classList.add('protein_id');
        p.textContent = this.name + "|" + this.protein_id;

    let description = document.createElement('p');
        description.textContent = this.description;
        description.classList.add('description');

        textDiv.append(p, description);

    let coverageDiv = document.createElement('div');
    let coverage_p = document.createElement('p');
        coverage_p.textContent = Math.round(this.percent_coverage * 10)/10 + "%";
        coverageDiv.append(coverage_p);

    this.canvas = document.createElement('canvas');

    this.sequence_p = document.createElement('p');
    let sequence_div = document.createElement('div');
        sequence_div.classList.add('sequence');
        sequence_div.append(this.sequence_p);
    this.annotateCoverage();
        // sequence_p.textContent = this.sequence;

    this.card = document.createElement('div');
    this.card.classList.add('protein-card');
    this.card.id = this.protein_id;
    this.card.append(textDiv, coverageDiv, this.canvas, sequence_div);

    if (this.is_visible) {
      this.card.addEventListener("click", e => {
        if(!this.card.classList.contains("selected")) {
          clear_selected();
          let prom = fetch_mol(this.protein_id); //fetch mol immediately on click, give promise to prom_handle
          this.card.classList.add("selected");
          document.querySelector('#molloading').classList.add('spin-ani');
          let container = glmol01.container[0].querySelector("canvas");
          container.style.opacity = "0";
          container.addEventListener("transitionend", e => prom_handle(prom), {once: true});
        }
      });
    }
    else
      this.card.classList.add('disabled');

    this.initCanvas();

    return this.card;
  }

  initCanvas() {
    this.ctx = this.canvas.getContext('2d');

    this.canvas.width = 1000;
    this.canvas.height = 50;

    let width = this.canvas.width;
    let height = this.canvas.height;

    this.ctx.fillStyle = '#dcdcdc';
    this.ctx.fillRect(0,0, width, height);

    this.canvas.addEventListener("mousemove", e => {
      if(this.card.classList.contains("selected")) {
        let rect = this.canvas.getBoundingClientRect();
        let x = e.clientX - rect.left;
        this.ctx.fillStyle = '#dcdcdc';
        this.ctx.fillRect(0, 0, width, height);
        this.drawCoverage(coverage_color);
        this.ctx.fillStyle = '#36e7ff';
        let canvas_x = x * (width / rect.width);
        this.ctx.fillRect(canvas_x, 0, 5, height);
        if(ribbon_range != null) {
          highlightMol(calcRibbonPos(x, rect.width, ribbon_range['min'], ribbon_range['max']), 54, 231, 255);
        }

      }
    });
    this.canvas.addEventListener("mouseleave", e => {
      if(this.card.classList.contains("selected")) {
        this.ctx.fillStyle = '#dcdcdc';
        this.ctx.fillRect(0, 0, width, height);
        this.drawCoverage(coverage_color);
        removeHighlightMol(54, 231, 255);
      }
    });
  }

  drawCoverage(coverage_color) {
    let width = this.canvas.width;
    let height = this.canvas.height;

    if(this.is_visible)
      this.ctx.fillStyle = coverage_color;
    else
      this.ctx.fillStyle = '#ababab';

    let non_zero_counter = 0;

    this.coverage_arr.forEach((i, index) => {
      if(i !== 0)
        non_zero_counter++;
      else {
        if(non_zero_counter / this.coverage_arr.length * 100 !== 0) {
          let rect_width = Math.floor(non_zero_counter / this.coverage_arr.length * width);
          let position = Math.floor(index / this.coverage_arr.length * width) - rect_width;
          this.ctx.fillRect(position, 0, rect_width, height);
          non_zero_counter = 0;
        }
      }
    });

    if(non_zero_counter / this.coverage_arr.length * 100 !== 0) {
      let rect_width = Math.floor(non_zero_counter / this.coverage_arr.length * width);
      let position = Math.floor(this.coverage_arr.length / this.coverage_arr.length * width) - rect_width;
      this.ctx.fillRect(position, 0, rect_width, height);
      non_zero_counter = 0;
    }

    if (this.ptms != undefined) {
      for (const [key, value] of Object.entries(this.ptms)) {
        let regex_val = ptm_annotations[key];
        if (regex_val != undefined) {
          this.ctx.fillStyle = 'rgb(' + regex_val[0] + ',' + regex_val[1] + ',' + regex_val[2] + ')';

          value.forEach(index => {
            let position = index / this.coverage_arr.length * width;
            this.ctx.fillRect(position, 0, 2, height);
          });
        }
      }
    }
  }

  annotateCoverage() {
    let res = "";

    let in_coverage = false;
    let in_ptm = false;

    this.coverage_arr.forEach((i, index) => {
      in_ptm = false;

      if(this.ptms != undefined) {
        for(const [key, value] of Object.entries(this.ptms)) {
          value.forEach(i => {
            if(i === index) {
              let mapping = check_ptm_annotations(this.ptms, i);
              let regex_val = ptm_annotations[key];
              if(mapping.length > 1 && get_ptm_not_group(mapping) !== key) return;
                res += '<mark style="background-color: ' + 'rgb(' + regex_val[0] + ',' + regex_val[1] + ',' + regex_val[2] + ')' + '">';
                res += this.sequence.substring(index, index + 1);
                res += '</mark>';
                in_ptm = true;
            }
          });
        }
      }
      if(!in_coverage && i !== 0)
        res += "<mark style='background-color: "+ coverage_color +"'>";
      else if(in_coverage && i === 0)
        res += "</mark>";
      if(!in_ptm)
        res += this.sequence.substring(index, index+1);
      in_coverage = (i !== 0);
    });
    this.sequence_p.innerHTML = res;
  }

}

const check_ptm_annotations = (ptms, val) => {
  let res = [];
  for (const [key, values] of Object.entries(ptms)) {
    values.forEach(value => {
      if (val === value)
        res.push(key);
    })
  }
  return res;
}

const get_ptm_not_group = (values) => {
  for (let i = 0; i < values.length; i++)
  {
    if (values[i].charAt(1) === '[')
      return values[i];
  }
  return undefined;
}


let job = (new URL(document.location)).searchParams.get('job');
let ptm_annotations;
let background_color;
let pdb_dest;
let coverage_cards = [];
let ribbon_range;

let coverage_color = '#FF3E3E';

console.log(job);

const get_anchor = () => {
  let curr_url = window.document.URL;
  console.log(curr_url);
  let url_parts   = curr_url.split('#');

  return (url_parts.length > 1) ? url_parts[1] : null;
}

const show_major_error = (status, message) => {
  const major_error = document.querySelector("#major_error");

  // Remove all child elements
  while (major_error.firstChild) {
    major_error.removeChild(major_error.firstChild);
  }

  let p_status = document.createElement("p");
  p_status.textContent = "Status: " + status;

  let p_message = document.createElement("p");
  p_message.textContent = message;
  major_error.append(p_status, p_message);

  major_error.style.display = "block";
}

window.onload = () => {
  let form = new FormData();
  form.append('job_number', job);

  // Fetch job details, update legend and background color
  let jobDetailsPromise = fetch('/job_details', {
    method: 'POST',
    body: form
  })
  .then(async response => {
    if (response.ok)
      return response.json();
    else
      throw new Error('Error in fetch /job_details', {
        cause: {status: response.status, response: await response.json()}
      });
  })
  .then(json => {
    console.log(json);
    show_legend(json['ptm_annotations']);
    background_color = json['background_color'];
    ptm_annotations = json['ptm_annotations'];
    return json; // Return the value from the jobDetailsPromise
  })
  .catch(err => {
      console.error(err);
      show_major_error(err.cause.status, err.cause.response.detail);
  });

  // Fetch coverage data
  let proteinListPromise = fetch('/protein-list', {
    method: 'POST',
    body: form
  })
  .then(async response => {
    if(response.ok) {
      document.querySelector("#list_loading").classList.remove("spin-ani");
      return response.json();
    }
    else
      throw new Error('Error in fetch /protein-list', {
        cause: {status: response.status, response: await response.json()}
      });
  })
  .catch(err => {
    console.error(err);
    show_major_error(err.cause.status, err.cause.response.detail);
  });

  // Once both promises are resolved, update the UI
  Promise.all([jobDetailsPromise, proteinListPromise])
  .then(([jobDetailsResult, proteinListResult]) => {
    console.log(proteinListResult);
    document.querySelector("#list_loading").classList.remove("spin-ani");

    // Sort by coverage
    proteinListResult.sort((a,b) => {
      return b['coverage'] - a['coverage'];
    })

    proteinListResult.forEach(i => {
      console.log(i);
      let c = new CoverageCard(
              i['protein_id'],
              i['UNID'],
              i['description'],
              i['coverage'] * 100, // convert to percent
              i['sequence_coverage'],
              i['sequence'],
              i["has_pdb"],
              i["ptms"]
      );
      document.querySelector('.protein-list-container').append(c.createCard());
      c.drawCoverage(coverage_color);
      c.annotateCoverage();
      coverage_cards.push(c);
    })

    // select first card
    console.log(get_anchor());
    let selection = document.querySelector("#"+get_anchor());
    if (selection == null)
        selection = document.querySelector(".protein-card");
    selection.click();
  });
}

document.onselectionchange = () => {
  // console.log(getSelection());
  // let selection = getSelection();
  // console.log(selection);
  let seq_div = document.querySelector(".selected").querySelector(".sequence");
  let offset = getSelectionOffsetRelativeTo(seq_div);
  let length = window.getSelection().getRangeAt(0).toString().length;
  console.log(offset);
  console.log(length);
  // if(length === 0)
  //   removeHighlightMol(0, 255, 255);
  // else
  let range = getRibbonRange();
  let max = seq_div.textContent.length;
  highlightMolRange(((offset+range['min'])/max)*range['max'], ((offset+length)/max)*range['max'], 0, 255, 255);

}

const getSelectionOffsetRelativeTo = (parentElement, currentNode) => {
  let currentSelection, currentRange,
          offset = 0,
          prevSibling,
          nodeContent;

  if (!currentNode){
    currentSelection = window.getSelection();
    currentRange = currentSelection.getRangeAt(0);
    currentNode = currentRange.startContainer;
    offset += currentRange.startOffset;
  }

  if (currentNode === parentElement){
    return offset;
  }

  if (!parentElement.contains(currentNode)){
    return -1;
  }

  while (prevSibling = (prevSibling  || currentNode).previousSibling){
    nodeContent = prevSibling.innerText || prevSibling.nodeValue || "";
    offset += nodeContent.length;
  }

  return offset + getSelectionOffsetRelativeTo(parentElement, currentNode.parentNode);
}


let inverval_id;

window.onresize = () => {
  glmol01.rebuildScene(true);
  glmol01.show();
}

const rebuild_glmol = () => {
  let near = glmol01.camera.near;
  let far = glmol01.camera.far;
  let camera = glmol01.camera;

  let x = glmol01.rotationGroup.position.x;
  let y = glmol01.rotationGroup.position.y;
  let z = glmol01.rotationGroup.position.z;

  glmol01.defineRepresentation();
  glmol01.rebuildScene(true);
  // glmol01.show();
  glmol01.rotationGroup.position.x = x;
  glmol01.rotationGroup.position.y = y;
  glmol01.rotationGroup.position.z = z;
  rotate(gl_r, gl_dx, gl_dy);
  // glmol01.camera.near = near;
  // glmol01.camera.far = far;
}

const create_color_circle = (name, r, g, b, index) => {
    let div = document.createElement('div');
    div.classList.add("legend-item");
    let p = document.createElement('p');
    p.textContent = name;
    let colorCircle = document.createElement('div');
    colorCircle.classList.add('colorCircle');
    colorCircle.style.backgroundColor = 'rgb(' + r + ',' + g +  ',' + b + ')';
    let colorInput = document.createElement('input');
    colorInput.type = "color";
    colorInput.value = rgbToHex(r,g,b);
    colorCircle.append(colorInput);
    colorInput.addEventListener("input", e => {
      colorCircle.style.backgroundColor = colorInput.value;
      let val = hexToRgb(colorInput.value);
      updateMolColor(index, val.r, val.g, val.b);
      update_regex_dict(index-2, [val.r, val.g, val.b]);
      if(p.textContent === "Coverage")
        coverage_color = colorInput.value;
      coverage_cards.forEach(i => {
        i.drawCoverage(coverage_color);
        i.annotateCoverage();
      });
    });
    div.append(p, colorCircle);
    return div;
}

const show_legend = (ptm_annotations) => {
  let legend = document.querySelector("#legend");

  legend.append(create_color_circle("Uncovered", 220, 220, 220, 0));
  legend.append(create_color_circle("Coverage", 255, 62,62, 1));
  for (const [index, [key, value]] of Object.entries(Object.entries(ptm_annotations))) {
    legend.append(create_color_circle(key, value[0], value[1], value[2], parseInt(index)+2));
  }
}

const start_autorotate = () => {
  // let r = Math.acos(glmol01.dq.x)/Math.PI;
  // let rs;
  // if (r == 0)
  //   rs = 0;
  // else
  //   rs = Math.sin(r * Math.PI) / r;
  // gl_r = r;
  // gl_dx = glmol01.dq.z/rs;
  // gl_dy = glmol01.dq.w/rs;
  autorotate = true;
  if(inverval_id != undefined)
    clearInterval(inverval_id);
  inverval_id = setInterval(rotate_ani, 1000/60);
  autorotate_button.classList.add("active");
}

const stop_autorotate = () => {
  autorotate = false;
  if(inverval_id != undefined)
    clearInterval(inverval_id);
  autorotate_button.classList.remove("active");
}

const toggle_autorotate = () => {
  if(autorotate)
    stop_autorotate();
  else
    start_autorotate();
}

const fetch_mol = (protein_id) => {
  // console.log(input);
  let form = new FormData();
  form.append('job_number', job);
  form.append('protein_id', protein_id);
  return fetch('/protein-structure', {
    method: 'POST',
    body: form
  })
  .then(async response => {
    if (response.ok)
      return await response.json();
    else
      throw new Error("Error in fetch /protein-structure", {
        cause: {status: response.status, response: await response.json()}
      });
  })
}

const draw_mol = (pdbstr, ret) => {
  let container = glmol01.container[0].querySelector("canvas");
  document.querySelector('#glmol01_src').textContent = pdbstr;
  document.querySelector('#glmol01_rep').textContent = ret;
  ribbon_range = getRibbonRange();
  glmol01.loadMolecule(true);
  glmol01.rebuildScene(true);
  container.style.opacity = "1";
  container.style.transition = "opacity 0.75s";
  glmol01.show();
  container.addEventListener("mousedown", e => stop_autorotate()); //stop autorotate when mouse is pressed
  container.addEventListener("touchstart", e => stop_autorotate()); //stop autorotate when touched on mobile
  start_autorotate();
}

const clear_selected = () => {
  document.querySelectorAll(".protein-card").forEach(i => {i.classList.remove('selected');})
}

const prom_handle = (prom) => {
  prom
      .then(response => {
      // console.log(response);
      document.querySelector('#molloading').classList.remove('spin-ani');
      draw_mol(response.pdb_str, response.ret);
      let coverage_rgb = hexToRgb(coverage_color);
      updateMolColor(1, coverage_rgb.r, coverage_rgb.g, coverage_rgb.b);

      let indicies = Object.keys(regex_dict);
      indicies.forEach(i => {
        let regex_val = regex_dict[i];
        if (regex_val != undefined) {
          updateMolColor(i + 2, regex_val[0], regex_val[1], regex_val[2]);
        }
      });
    })
    .catch(error => {
        show_error(error.cause.response.detail);
    });
}

const rotate = (r, dx ,dy) => {
  // console.log("r: " + r + " dx: " + dx + " dy: " + dy);
  let rs = Math.sin(r * Math.PI) / r;
  glmol01.dq.x = Math.cos(r * Math.PI);
  glmol01.dq.y = 0;
  glmol01.dq.z =  rs * dx;
  glmol01.dq.w =  rs * dy;
  glmol01.rotationGroup.quaternion = new THREE.Quaternion(1, 0, 0, 0);
  glmol01.rotationGroup.quaternion.multiplySelf(glmol01.dq);
  glmol01.rotationGroup.quaternion.multiplySelf(glmol01.cq);
  glmol01.show();
}

let gl_r = 0.02;
let gl_dx = 0.002;
let gl_dy = 0.002;

const rotate_ani = () => {
  rotate(gl_r, gl_dx, gl_dy);
  gl_r += 0.0002;
  gl_dx += 0.0002;
  // gl_dy += 0.001;
}

let autorotate_button = document.querySelector("#autorotate");
let autorotate = true;

autorotate_button.addEventListener("click", e => {toggle_autorotate();})

let capture_button = document.querySelector("#capture");

const capture_canvas = () => {
  let canvas = glmol01.container[0].querySelector("canvas");
  let image = canvas.toDataURL();
  let link = document.createElement('a');

  let curr_protein_id = document.querySelector(".selected").querySelector('.protein_id').textContent;

  let splits = pdb_dest.split('/');

  link.download = curr_protein_id.replace('|', '_') + "_" + splits[splits.length-1].replace('.db', '') + ".png";
  link.href = image;
  link.click();
}

capture_button.addEventListener("click", e => {
  capture_canvas();
});

const componentToHex = (c) => {
  let hex = c.toString(16);
  return hex.length == 1 ? "0" + hex : hex;
}

const rgbToHex = (r, g, b) => {
  return "#" + componentToHex(r) + componentToHex(g) + componentToHex(b);
}

const hexToRgb = (hex) => {
  let result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  } : null;
}

const update_regex_dict = (index, arr) => {
  regex_dict[Object.keys(regex_dict)[index]] = arr;
}

const updateMolColor = (index, r, g, b) => {
  let rep = document.querySelector('#glmol01_rep');
  let og_text = rep.textContent;
  // console.log(og_text);
  const re = new RegExp('color:(\\d.\\d+),(\\d.\\d+),(\\d.\\d+)', 'g');
  let matches = Array.from(og_text.matchAll(re));
  // console.log(matches[index]);
  // console.log(matches);
  if(matches[index] !== undefined) {
    let start_index = matches[index].index;
    let res_text = og_text.substring(0, start_index) +
            'color:' + (r / 255).toFixed(2) + ',' + (g / 255).toFixed(2) + ',' + (b / 255).toFixed(2) +
            og_text.substring(start_index + matches[index][0].length);
    // console.log(res_text);
    rep.textContent = res_text;
    rebuild_glmol();
  }
}

const highlightMol = (pos, r, g, b) => {
  let rep_elem = document.querySelector('#glmol01_rep');
  let rep = rep_elem.textContent;
  let str_index = rep.indexOf('color:' + (r/255).toFixed(2) + ',' + (g/255).toFixed(2) + ',' + (b/255).toFixed(2));
  let res = '';
  if (str_index === -1) {
    str_index = rep.indexOf('view:');
    res += rep.substring(0, str_index);
    res += 'color:' + (r / 255).toFixed(2) + ',' + (g / 255).toFixed(2) + ',' + (b / 255).toFixed(2) + ":" + (pos - 10) + '-' + (pos + 10) + '\n';
    res += rep.substring(str_index);
    // console.log(res);
  }
  else {
    let view_index = rep.indexOf('view:');
    res += rep.substring(0, str_index);
    res += 'color:' + (r / 255).toFixed(2) + ',' + (g / 255).toFixed(2) + ',' + (b / 255).toFixed(2) + ":" + (pos - 10) + '-' + (pos + 10) + '\n';
    res += rep.substring(view_index);
  }
  rep_elem.textContent = res;
  rebuild_glmol();
}

const highlightMolRange = (start, end, r, g, b) => {
  let rep_elem = document.querySelector('#glmol01_rep');
  let rep = rep_elem.textContent;
  let str_index = rep.indexOf('color:' + (r/255).toFixed(2) + ',' + (g/255).toFixed(2) + ',' + (b/255).toFixed(2));
  let res = '';
  if (str_index === -1) {
    str_index = rep.indexOf('view:');
    res += rep.substring(0, str_index);
    res += 'color:' + (r / 255).toFixed(2) + ',' + (g / 255).toFixed(2) + ',' + (b / 255).toFixed(2) + ":" + start + '-' + end + '\n';
    res += rep.substring(str_index);
    // console.log(res);
  }
  else {
    let view_index = rep.indexOf('view:');
    res += rep.substring(0, str_index);
    res += 'color:' + (r / 255).toFixed(2) + ',' + (g / 255).toFixed(2) + ',' + (b / 255).toFixed(2) + ":" + start + '-' + end + '\n';
    res += rep.substring(view_index);
  }
  rep_elem.textContent = res;
  rebuild_glmol();
}

const removeHighlightMol = (r, g, b) => {
  let rep_elem = document.querySelector('#glmol01_rep');
  let rep = rep_elem.textContent;
  let str_index = rep.indexOf('color:' + (r/255).toFixed(2) + ',' + (g/255).toFixed(2) + ',' + (b/255).toFixed(2));
  let res = '';
  if(str_index !== -1) {
    let view_index = rep.indexOf('view:');
    res += rep.substring(0, str_index);
    res += rep.substring(view_index);
  }
  rep_elem.textContent = res;
  rebuild_glmol();
}

const getRibbonRange = () => {
  let rep = document.querySelector('#glmol01_rep').textContent;
  const re = new RegExp('ribbon:(\\d+)-(\\d+)');
  let res = re.exec(rep);
  return {'min': parseInt(res[1]), 'max': parseInt(res[2])}
}

const calcRibbonPos = (x, rect_width, ribbon_min, ribbon_max) => {
  return Math.round((x/rect_width)*(ribbon_max-ribbon_min));
}
