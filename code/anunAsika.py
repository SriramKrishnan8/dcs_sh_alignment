import sys
import os

import re
import json


substitutions = {
    "Mk" : "fk", "MK" : "fK", "Mg" : "fg", "MG" : "fG", "Mf" : "ff",
    "Mc" : "Fc", "MC" : "FC", "Mj" : "Fj", "MJ" : "FJ", "MF" : "FF",
    "Mt" : "Nt", "MT" : "NT", "Md" : "Nd", "MD" : "ND", "MN" : "NN",
    "Mw" : "nw", "MW" : "nW", "Mx" : "nx", "MX" : "nX", "Mn" : "nn",
    "Mp" : "mp", "MP" : "mP", "Mb" : "mb", "MB" : "mB", "Mm" : "mm",
    "rwwa" : "rwa", "rwwA" : "rwA", "rwwi" : "rwi", "rwwI" : "rwI",
    "rwwu" : "rwu", "rwwU" : "rwU", "rwwq" : "rwq", "rwwQ" : "rwQ",
    "rwwe" : "rwe", "rwwE" : "rwE", "rwwo" : "rwo", "rwwO" : "rwO",
}

def replace_anusvAra(match_obj, y):
    match = ""
    if match_obj.group(1) is not None:
        print(match_obj.group(1))
        match = match_obj.group(1)
    
    return y + match

def to_anunasika(string_):
    new_string = string_
    replacements = [
        (r'M([kKgGf])', "f"),
        (r'M([cCjJF])', "F"),
        (r'M([tTdDN])', "N"),
        (r'M([wWxXn])', "n"),
        (r'M([pPbBm])', "m"),
        (r'M$', "m"),
        (r'rww([aeiouAEIOUqQ])', "rw")
    ]
    
    for x, y in substitutions.items():
        new_string = new_string.replace(x, y)
#        new_string = re.sub(x, lambda match_obj, r_text=y: replace_anusvAra(match_obj, r_text), new_string)
        
    return new_string

def handle_anunasika(data):
    new_data = data
    
    stems = new_data.get("stem", [])
    words = new_data.get("word", [])
    
    new_stems = []
    new_words = []
    
    for i in range(len(stems)):
        new_inner_stems = []
        new_inner_words = []
        
        for j in range(len(stems[i])):
            new_inner_stems.append(to_anunasika(stems[i][j]))
            new_inner_words.append(to_anunasika(words[i][j]))
        
        new_stems.append(new_inner_stems)
        new_words.append(new_inner_words)
    
    new_data["stem"] = new_stems
    new_data["word"] = new_words
    
    return new_data
