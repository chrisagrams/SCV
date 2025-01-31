from hashlib import blake2b

import pymol


def fasta_reader(fasta_path: str):
    protein_dict = {}
    with open(fasta_path, "r") as f_o:
        file_split = f_o.read().split("\n>")

    for each in file_split:
        first_line, seq = each.split("\n")[0], "".join(each.split("\n")[1:])
        uniprot_id = first_line.split("|")[1]
        gene = (
            first_line.split("GN=")[1].split(" ")[0] if "GN=" in first_line else "N/A"
        )
        des = " ".join(first_line.split(" ")[1:]).split(" OS=")[0]
        protein_dict[uniprot_id] = {"sequence": seq, "gene": gene, "des": des}
    return protein_dict


def pymol_obj_extract(obj: list) -> dict:
    if float(pymol.cmd.get("pse_export_version")) != 1.74:
        raise Exception("PyMOL pse_export_version must be 1.74")
    ret = {
        "name": obj[0],
        "sphere": [],
        "trace": [],
        "ribbon": [],
        "stick": [],
        "surface": [],
        "line": [],
        "cross": [],
        "smallSphere": [],
        "helix": [],
        "sheet": [],
    }
    for atom in obj[5][7]:
        rep = atom[20] + [0] * 12
        serial = atom[22]
        ss = atom[10]
        bonded = atom[25] == 1
        if rep[5] == 1:
            ret["ribbon"].append(serial)
        if rep[1] == 1:
            ret["sphere"].append(serial)
        if rep[2] == 1:
            ret["surface"].append(serial)
        if rep[7] == 1:
            ret["line"].append(serial)
        if rep[6] == 1:
            ret["trace"].append(serial)
        if rep[4] == 1 and not bonded:
            ret["smallSphere"].append(serial)
        if rep[11] == 1 and not bonded:
            ret["cross"].append(serial)
        if rep[0] == 1 and bonded:
            ret["stick"].append(serial)
        if ss == "S":
            ret["sheet"].append(serial)
        if ss == "H":
            ret["helix"].append(serial)

    return ret


def compact_list(seq: list) -> str:
    """
    Compact a list of numbers into a string.
    For instance, the list [1, 2, 3, 5, 6, 8] is converted into the string "1-3,5-6,8".
    """
    if not seq or len(seq) == 0:
        return ""
    seq.sort()
    ret = []
    start = seq[0]
    end = seq[0]

    for num in seq[1:] + [None]:
        if num is not None and num == end + 1:
            end = num
        else:
            if start == end:
                ret.append(str(start))
            else:
                ret.append(f"{start}-{end}")
            start = num
            end = num

    return ",".join(ret)


def compact_range_list(seq: list) -> str:
    return ",".join([f"{start}-{end}" for start, end in seq])


def pymol_obj_dict_to_str(obj: dict) -> str:
    ret = []
    for k, v in obj.items():
        if k == "name":
            continue
        ret.append(f"{k}:{compact_list(v)}")
    return "\n".join(ret) + "\n"


def pymol_view_dict_to_str(view: dict) -> str:
    matrix = view["rotation_matrix"]
    view_values = [
        view["cx"],
        view["cy"],
        view["cz"],
        view["camera_z"],
        view["slab_near"],
        view["slab_far"],
        view["fog_start"],
        view["fov"],
        matrix["n11"],
        matrix["n21"],
        matrix["n31"],
        matrix["n12"],
        matrix["n22"],
        matrix["n32"],
        matrix["n13"],
        matrix["n23"],
        matrix["n33"],
    ]

    view_str = ",".join(
        [f"{round(val, 3)}" for val in view_values]
    )  # round to 3 decimal places
    return f"view:{view_str}\n"


def color_values_to_str(colors: list):
    return ",".join([f"{color/256:0<5.3f}" for color in colors])


def color_dict_to_str(color: dict) -> str:
    ret = ""
    sorted_items = sorted(
        color.items(), key=lambda x: (x[0] != "non_covered", x[0] != "covered", x[0])
    )
    for k, v in sorted_items:
        ret += f"color:{color_values_to_str(v['color'])}:{compact_range_list(v['indices'])}\n"
    return ret


def calc_hash_of_dict(target_dict):
    """
    Calculate the hash of a dictionary using its values
    :param seq_cov_dict:
    :return:
    """
    # Create new BLAKE2b hash object
    h = blake2b()

    # Sort keys for consistent hash
    sorted_keys = sorted(target_dict.keys())

    # Update hash with sorted keys
    for key in sorted_keys:
        value = target_dict[key]
        h.update(str(value).encode("utf-8"))

    # Compute hash digest
    digest = h.hexdigest()

    # Return hash digest
    return digest
