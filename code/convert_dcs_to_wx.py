import sys
import os
import subprocess as sp

import json

from tqdm import tqdm

import common_methods as cm
from devconvert import dev2slp, iast2slp, slp2dev, slp2iast, slp2tex, slp2wx, wx2slp, dev2wx

script, sent, dcs_dir, new_dcs_dir, missed, already = sys.argv


letter_dict = {
    "Ā" : "ā", "Ī" : "ī", "Ū" : "ū", "Ṛ" : "ṛ", "Ṝ" : "ṝ", "Ḷ" : "ḷ",
    "Ḹ" : "ḹ", "Ṅ" : "ṅ", "Ñ" : "ñ", "Ṭ" : "ṭ", "Ḍ" : "ḍ", "Ṇ" : "ṇ",
    "Ś" : "ś", "Ṣ" : "ṣ"
}

def iast2wx(text):
    """ Converts the input string text from iast to wx notation. """
    
    return slp2wx.convert(iast2slp.convert(text))
    

def uncapitalise(text):
    """ Converts all the upper case letters to its corresponding lower
        case letters
    """
    
    for key, value in letter_dict.items():
        text = text.replace(key, value)
    
    return text.lower()
    

def u_and_c(text):
    """ Uncapitalises first and then converts the text from iast 
        to wx notation
    """
    
    return iast2wx(uncapitalise(text))


def convert_to_wx(data):
    """ Converts all the details in data from iast to wx notation.
        
        Input -> data (data from DCS), source, destination notations
    """
    
    new_data = {}
    
    new_data["text"] = u_and_c(data.get("text", ""))
    new_data["text_id"] = data.get("text_id", "")
    new_data["chapter"] = u_and_c(data.get("chapter", ""))
    new_data["chapter_id"] = data.get("chapter_id", "")
    new_data["sent_counter"] = data.get("sent_counter", "")
    new_data["sent_sub_counter"] = data.get("sent_sub_counter", "")
    new_data["layer"] = data.get("layer", "")
    new_data["citation_text"] = u_and_c(data.get("citation_text", ""))
    new_data["citation_chapter"] = data.get("citation_chapter", "")
    
    new_data["sent_id"] = data.get("sent_id", "")
    new_data["joint_sentence"] = iast2wx(data.get("joint_sentence", ""))
    new_data["position"] = data.get("position", [])
    
    dcs_unsegmented_forms = data.get("unsegmented_form", [])
    dcs_word_forms = data.get("word_form", [])
    dcs_stems = data.get("stem", [])
    dcs_words = data.get("word", [])
    dcs_miscs = data.get("misc", [])
    dcs_preverbs = data.get("preverbs", [])
    
    new_unsegmented_forms = []
    new_stems = []
    new_words = []
    new_word_forms = []
    new_preverbs = []
    new_miscs = []
    
    position = new_data["position"]
    for i in range(len(position)):
        new_unsegmented_forms.append(iast2wx(dcs_unsegmented_forms[i]))
        new_inner_stems = []
        new_inner_words = []
        new_inner_word_forms = []
        new_inner_preverbs = []
        new_inner_miscs = []
        
        for j in range(len(position[i])):
            new_inner_stems.append(iast2wx(dcs_stems[i][j]))
            new_inner_words.append(iast2wx(dcs_words[i][j]))
            new_inner_word_forms.append(iast2wx(dcs_word_forms[i][j]))
            new_inner_preverbs.append(iast2wx(dcs_preverbs[i][j]))

            misc_lst = dcs_miscs[i][j].split("|")
            new_misc_lst = []
            for misc_item in misc_lst:
                misc_item_split = misc_item.split("=")
                new_misc_val = misc_item_split[1]
                if misc_item_split[0] == "Unsandhied":
                    new_misc_val = iast2wx(new_misc_val)
                new_misc_lst.append("=".join((misc_item_split[0], new_misc_val)))
                    
            new_inner_miscs.append("|".join(new_misc_lst))
        
        new_stems.append(new_inner_stems)
        new_words.append(new_inner_words)
        new_word_forms.append(new_inner_word_forms)
        new_preverbs.append(new_inner_preverbs)
        new_miscs.append(new_inner_miscs)
    
    new_data["unsegmented_form"] = new_unsegmented_forms
    new_data["stem"] = new_stems
    new_data["stem_id"] = data.get("stem_id")
    new_data["morph"] = data.get("morph")
    new_data["word"] = new_words
    new_data["word_form"] = new_word_forms
    new_data["preverbs"] = new_preverbs
    
    new_data["upos"] = data.get("upos")
    new_data["xpos"] = data.get("xpos")
    new_data["head"] = data.get("head")
    new_data["deprel"] = data.get("deprel")
    new_data["deps"] = data.get("deps")
    new_data["misc"] = new_miscs
    new_data["sem_ids"] = data.get("sem_ids")
    new_data["word_reconstructed"] = data.get("word_reconstructed")
    new_data["occ_ids"] = data.get("occ_ids")
    new_data["grammar"] = data.get("grammar")
    new_data["punctuation"] = data.get("punctuation")
    new_data["meanings"] = data.get("meanings")
    new_data["is_mantra"] = data.get("is_mantra")
    
    return new_data
        

lines = cm.list_from_file(sent)
missed_file = open(missed, 'w')
already_file = open(already, 'w')

#for x in range(len(lines)):
for i in tqdm(range(len(lines))):
    line = lines[i]
    line_s = line.split("\t")
    
    sent_id = line_s[0]
    sentence = line_s[1]
    
    dcs_path = os.path.join(dcs_dir, (str(sent_id) + ".json"))
    if not os.path.isfile(dcs_path):
        missed_file.write(line + "\n")
        continue
    
    new_json_path = os.path.join(new_dcs_dir, (str(sent_id) + ".json"))
    if os.path.isfile(new_json_path):
        already_file.write(line + "\n")
        continue
    
    dcs_data = cm.get_dcs_json(sent_id, dcs_dir)
    new_data = convert_to_wx(dcs_data)
    
    with open(new_json_path, 'w', encoding='utf-8') as out_file:
        json.dump(new_data, out_file, ensure_ascii=False)
