/*
   GLmol - Molecular Viewer on WebGL/Javascript
   (C) Copyright 2011-2012, biochem_fan

   License: dual license of MIT or LGPL3

    This program uses
      Three.js
         https://github.com/mrdoob/three.js
         Copyright (c) 2010-2011 three.js Authors. All rights reserved.
      jQuery
         http://jquery.org/
         Copyright (c) 2011 John Resig
*/

var glmol01 = new GLmol('glmol01', true);
  $('#glmol01_reload').click(function(ev) {
    glmol01.rebuildScene(true);
    glmol01.show();
  });
  function defineRep() {
    var idHeader = "#" + this.id + '_';

    this.parseRep(this.modelGroup, $('#glmol01_rep').val());
  }

  function expandSeq(str) {
    var nums = str.split(',');
    var ret = []
    for (var i = 0, lim = nums.length; i < lim; i++) {
      var tmp = nums[i].split('-');
      if (tmp.length == 1) tmp.push(tmp[0]);
      tmp[0] = parseInt(tmp[0]); tmp[1] = parseInt(tmp[1]);
      for (var j = tmp[0]; j <= tmp[1]; j++) ret.push(j);
    }
    return ret;
  }

  glmol01.parseSS = function(str, ss) {
    var nums = str.split(',');
    var ret = []
    var atoms = this.atoms;
    for (var i = 0, lim = nums.length; i < lim; i++) {
      var tmp = nums[i].split('-');
      if (tmp.length == 1) tmp[1] = tmp[0];

      var start = parseInt(tmp[0]), end = parseInt(tmp[1]);
      for (var j = start; j <= end; j++) {
        if (atoms[j]) atoms[j].ss = ss;
      }
      if (atoms[start]) atoms[start].ssbegin = true;
      if (atoms[end]) atoms[end].ssend = true;
    }
  };

  function parseRep(parentgroup, str) { // TODO: implement!
    var lines = str.split("\n");
    var group = new THREE.Object3D();
    var rgroup = new THREE.Object3D();
    rgroup.add(group);
    parentgroup.add(rgroup);

    // 1st pass; parse colors and dists
    for (var i = 0, lim = lines.length; i < lim; i++) {
      vals = lines[i].split(':');
      type = vals[0];
      if (type == 'color') {
        rgb = vals[1].split(',');
        if (rgb.length != 3) continue;
        var c = 0;
        c += Math.floor((parseFloat(rgb[0]) * 255)) << 16 ;
        c += Math.floor((parseFloat(rgb[1]) * 255)) << 8;
        c += Math.floor(parseFloat(rgb[2]) * 255);
        var atoms = expandSeq(vals[2]);
        this.colorAtoms(atoms, c);
      } else if (type == 'dists') {
        var c = vals[1].split(',');
        var color = new THREE.Color();
        color.r = parseFloat(c[0]);
        color.g = parseFloat(c[1]);
        color.b = parseFloat(c[2]);
        var points = vals[2].split(',');
        var out = [];
        for (var j = 0, jlim = Math.floor(points.length / 3); j < jlim; j++) {
          out.push(new THREE.Vector3(parseFloat(points[3 * j]), parseFloat(points[3 * j + 1]), parseFloat(points[3 * j + 2])));
        }
        this.drawDottedLines(group, out, color);
      } else if (type == 'helix') {
        glmol01.parseSS(vals[1], 'h');
      } else if (type == 'sheet') {
        glmol01.parseSS(vals[1], 's');
      } else if (type == 'view') {
        view = vals[1].split(',');
        if (view.length < 17) continue;
        for (var j = 0; j < 17; j++) view[j] = parseFloat(view[j]);
        rgroup.matrixAutoUpdate = false;
        rgroup.matrix.n11 = view[8];
        rgroup.matrix.n21 = view[9];
        rgroup.matrix.n31 = view[10];
        rgroup.matrix.n12 = view[11];
        rgroup.matrix.n22 = view[12];
        rgroup.matrix.n32 = view[13];
        rgroup.matrix.n13 = view[14];
        rgroup.matrix.n23 = view[15];
        rgroup.matrix.n33 = view[16];
        group.position.x = view[0]; group.position.y = view[1]; group.position.z = view[2];
        this.rotationGroup.position.z = view[3];
        this.slabNear = view[4]; this.slabFar = view[5];
        this.fogStart = view[6]; this.fov = view[7];
      } else if (type == 'bgcolor') {
        this.setBackground(vals[1]);
      }
    }
    // 2nd pass; parse representations
    for (var i = 0, lim = lines.length; i < lim; i++) {
      vals = lines[i].split(':');
      type = vals[0];
      if (vals.length < 2) continue;
      var atoms = expandSeq(vals[1]);
      if (atoms.length == 0) continue;
      if (type == 'sphere') {
        this.drawAtomsAsSphere(group, atoms);
      } else if (type == 'stick') {
        this.drawBondsAsStick(group, atoms, this.cylinderRadius, this.cylinderRadius, true);
      } else if (type == 'surface') {
//         this.generateMesh(group, atoms, 4);
      } else if (type == 'ribbon') {
        this.drawCartoon(group, atoms, this.curveWidth);
        this.drawCartoonNucleicAcid(group, atoms);
      } else if (type == 'trace') {
        this.drawMainchainCurve(group, atoms, this.curveWidth, 'CA', 1);
        this.drawMainchainCurve(group, atoms, this.curveWidth, 'O3\'', 1);
      } else if (type == 'line') {
        this.drawBondsAsLine(group, atoms, this.lineWidth * 2);
      } else if (type == 'cross') {
        this.drawAsCross(group, atoms, 0.3);
      } else if (type == 'smallSphere') {
        this.drawAtomsAsSphere(group, atoms, 0.3, true);
      } else if (type == 'sphere') {
        this.drawAtomsAsSphere(group, atoms, this.sphereRadius, false);
      }
    }
  }

  glmol01.rebuildScene = function(repressDraw) {
    time = new Date();

    this.initializeScene();
    this.defineRepresentation();

    // console.log("builded scene in " + (+new Date() - time) + "ms");

    // if (repressDraw) return;
    this.show();
  };

  glmol01.parseRep = parseRep;
  glmol01.defineRepresentation = defineRep;
  // glmol01.loadMolecule(true);
  // $('#loading').hide();