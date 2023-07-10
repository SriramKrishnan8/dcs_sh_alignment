import json
import sys
import os

from tqdm import tqdm

import common_methods as cm
import sandhi_words as sw
import anunAsika as an

script, sent, dcs_dir, sh_dir, new_sh_dir, missed, modified, not_modified = sys.argv

sandhi_cache = {}
ngram_ids_cache = {}
dcs_stems = []

def sandhi_components(comp1, comp2):
    """ Checks components if present in cache, else performs Sandhi """
    
    compound_str = ""
    key = comp1 + "-" + comp2
    if key in sandhi_cache.keys():
        compound_str = sandhi_cache[key]
    else:
        compound_str = sw.sandhi_join(comp1, comp2, False)
        sandhi_cache[key] = compound_str
    
    return compound_str


def check_sandhi(all_nodes, sentence, new_cur_list):
    """ Filtering based on sandhied compound present in sentence """
    
    cpd_temp = [all_nodes[int(check_id)][1] for check_id in new_cur_list]
    compound_str = ""
    for cpd_item in cpd_temp:
        compound_str = sandhi_components(compound_str, cpd_item)
    cpd_temp_str = "-".join(cpd_temp)
#    print("Checking compound entry: " + cpd_temp_str + " and sandhied_form: " + compound_str)
#    print(an.to_anunasika(sentence))
    
    return (compound_str in dcs_stems)
    

def get_ngram_ids(compound_lst):
    """ Getting n-gram ids """
    
    grams = range(2, len(compound_lst) + 1)
    ids_ = list(range(len(compound_lst)))
    
    all_entries = []
#    for g in grams:
#        for i in range(len(ids_) - g + 1):
#            all_entries.append(str(ids_[ i : (i + g) ]))
    
    all_entries = [ids_[ i : (i + g) ] for g in grams for i in range(len(ids_) - g + 1)]
    
    return all_entries


def extract_compositional_analysis(all_nodes, sentence, filtered_final_list):
    """ Given a set of compounds, extracts all possible and
        adds to the given list of nodes to be newly created
    """
    
    new_nodes = set()
    
    for compound_lst in filtered_final_list:
        cpd_ids_lst = []
        if len(compound_lst) in ngram_ids_cache.keys():
            cpd_ids_lst = ngram_ids_cache[len(compound_lst)]
        else:
            cpd_ids_lst = get_ngram_ids(list(range(len(compound_lst))))
            ngram_ids_cache[len(compound_lst)] = cpd_ids_lst
        
        for cpd_ids in cpd_ids_lst:
            compounded_stem = ""
            compounded_word = ""
            compounded_form = ""
            info = []
            for id_ in cpd_ids[:-1]:
                cur_component = compound_lst[id_]
                compounded_form = sandhi_components(compounded_form, cur_component[0])
                
#                wrd = cur_component[0]
#                others = cur_component[1:]
#                new_info = word + "(" + ",".join(others) +  ")"
#                info.append(new_info)

#                compounded_word = sandhi_components(compounded_word, compound_lst[id_][0])
#                compounded_stem = sandhi_components(compounded_stem, compound_lst[id_][3])
            
            last = compound_lst[cpd_ids[-1]]
            compounded_word = sandhi_components(compounded_form, last[0])
            compounded_stem = sandhi_components(compounded_form, last[3])
            
#            print(compounded_stem)
            if not compounded_stem in dcs_stems:
                continue
                
            new_cpd_item = (compounded_word, "-", "-", last[1], last[2], compounded_stem, last[4], last[5], last[6], last[7], last[8], last[9])
            new_nodes.add(new_cpd_item)
    
    new_segment_id = len(all_nodes)
    final_nodes = []
    for item in list(new_nodes):
        new_item = (str(new_segment_id), item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7], item[8], item[9], item[10], item[11])
        final_nodes.append(new_item)
        new_segment_id += 1
    
    return final_nodes
    

def analyse_sh_analysis(all_nodes, sentence, final_list, cur_list, cur_chunk, cur_pos_in_chunk, chkd_ids):
    """ Gets all possible components from all the nodes """
    
#    print("Checking " + str(cur_chunk) + ", " + str(cur_pos_in_chunk))
    
    for node in all_nodes:
        id_ = str(node[0])
        chunk_id = str(node[2])
        position_in_chunk = str(node[3])
        
        inf_morph = node[8]
        
        if (not (chunk_id == cur_chunk)) or (not (position_in_chunk == str(int(cur_pos_in_chunk) + 1))):
            continue
        
#        print("\nChecked " + str(chunk_id) + ", " + str(position_in_chunk) + " for node " + str(id_))
        if inf_morph == "iic.":
            new_cur_list = cur_list + [ id_ ]
            chkd_ids.add(id_)
#            print("Cur_list -> " + str(new_cur_list))
#            print("Checked_ids -> " + str(chkd_ids))
#            print("Going to Next Level")
            (chkd_ids, final_list) = analyse_sh_analysis(all_nodes, sentence, final_list, new_cur_list, chunk_id, position_in_chunk, chkd_ids)
        else:
            new_cur_list = cur_list + [ id_ ]
            chkd_ids.add(id_)
#            print("Cur_list -> " + str(new_cur_list))
#            print("Checked_ids -> " + str(chkd_ids))
#            print("Halt at this level and continue")
            
            final_list.append(new_cur_list)
#            if check_sandhi(all_nodes, sentence, new_cur_list):
#                final_list.append(new_cur_list)
            
            # The code below is shifted to the function check_sandhi()
#            cpd_temp = [all_nodes[int(check_id)][1] for check_id in new_cur_list]
#            compound_str = ""
#            for cpd_item in cpd_temp:
#                compound_str = sw.sandhi_join(compound_str, cpd_item, False)
#            cpd_temp_str = "-".join(cpd_temp)
#            print("Checking compound entry: " + cpd_temp_str + " and sandhied_form: " + compound_str)
#            if (compound_str in sentence):
#                final_list.append(new_cur_list)
        
    return (chkd_ids, final_list)
    

def filter_final_list(final_list, all_nodes):
    """ Filters the final list to remove duplicate nodes """
    
    new_list = []
    for cpd in final_list:
        new_cpd = []
        temp_compound = []
        for comp_id in cpd:
            node = all_nodes[int(comp_id)]
            word = node[1]
            phase = node[4]
            phase_color = node[5]
            stem = node[6]
            stem_sense = node[7]
            inf_morph = node[8]
            base = node[9]
            base_sense = node[10]
            der_morph = node[11]
            pre_verb = node[12]
            
            temp_compound.append((word + "(" + stem + "," + inf_morph +  ")"))
            item = (word, phase, phase_color, stem, stem_sense, inf_morph, base, base_sense, der_morph, pre_verb)
            new_cpd.append(item)
        
#        print("-".join(temp_compound))
        if new_cpd in new_list:
            continue
        else:
            new_list.append(new_cpd)
    
    return new_list
    

def loop_through_sh_analysis(all_nodes, sentence):
    """ Gets all possible components from all the nodes """
    
#    final_list = analyse_sh_analysis(all_nodes, [], [], 0, 0)
    
    checked_ids = set()
    cur_list = []
    final_list = []
    
    for node1 in all_nodes:
        id_ = str(node1[0])
        chunk_id = str(node1[2])
        position_in_chunk = str(node1[3])
        inf_morph = node1[8]
        
        if id_ in checked_ids:
            continue
        
        if not (inf_morph == "iic."):
            continue
        
        cur_list.append(id_)
        checked_ids.add(id_)
#        print("\n\nStarting for " + str(id_))
        (checked_ids, final_list) = analyse_sh_analysis(all_nodes, sentence, final_list, cur_list, chunk_id, position_in_chunk, checked_ids)
        cur_list = []
#        print("Final List Length: " + str(len(final_list)))
#        print("Ending for " + str(id_))
        
#    print("\n\nFinal List - " + str(len(final_list)) + ": " + str(final_list))
#    print("Checked IDS: " + str(checked_ids))
#    
    filtered_final_list = filter_final_list(final_list, all_nodes)
#    print("\n\nFiltered Final List - " + str(len(filtered_final_list)) + ": " + str(filtered_final_list))
    
    return filtered_final_list
    

lines = cm.list_from_file(sent)

missed_file = open(missed, "a+")
modified_file = open(modified, "a+")
not_modified_file = open(not_modified, "a+")

#for i in range(2, 20):
#    ngram_entries = get_ngram_ids(list(range(i)))
#    ngram_ids_cache[i] = ngram_entries

#for i in range(len(lines)):
for i in tqdm(range(len(lines))):
    line = lines[i]
    line_s = line.split("\t")
    
    sent_id = line_s[0]
    sentence = line_s[1]
    
    data = cm.get_dcs_json(sent_id, dcs_dir)
    dcs_stems = [an.to_anunasika(stem) for chunk in data["stem"] for stem in chunk]
    
#    print(dcs_stems)
    
    sh_path = os.path.join(sh_dir, (str(sent_id) + ".tsv"))
    if not os.path.isfile(sh_path):
        missed_file.write(line + "\n")
        continue
    
    all_nodes = cm.tuple_from_file(sh_path)
    filtered_final_list = loop_through_sh_analysis(all_nodes, sentence)
    
    new_nodes = extract_compositional_analysis(all_nodes, sentence, filtered_final_list)
    
    modified_nodes = all_nodes + new_nodes
    
    if len(new_nodes) > 0:
        modified_file.write(line + "\n")
    else:
        not_modified_file.write(line + "\n")
    
    sh_nodes_str = cm.list_to_string_for_file(modified_nodes)
    new_sh_path = os.path.join(new_sh_dir, (str(sent_id) + ".tsv"))
    with open(new_sh_path, 'w') as out_file:
        out_file.write(sh_nodes_str)

