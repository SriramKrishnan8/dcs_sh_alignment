import sys
import os
import subprocess as sp

import re
import json

from tqdm import tqdm
import signal
import psutil

import common_methods as cm


# The analyses from SH are in the form of a list of tuples, each of
# which is termed a node, hereafter. Each node has the following
# parameters(the number corresponds to the id in the tuple):
#0 - node_id
#1 - word
#2 - chunk_id
#3 - position_in_chunk
#4 - phase
#5 - phase_color
#6 - stem
#7 - stem_sense
#8 - inflectional_morph
#9 - base_stem
#10 - base_stem_sense
#11 - derivational_morph
#12 - pre_verb
#13 - character_position_in_chunk


def update_nodes(id_, sense_lst, duplicates):
    """ Returns the node_ids which are duplicates"""
    
    ids = set(
        [x for x,y in sense_lst if ((not x == id_) and not (x in duplicates))]
    )
    
    return duplicates + list(ids)
    
    
def get_new_sense(senses, id_, sense, duplicates):
    """  """
    
    new_sense = sense
    if len(senses) > 0:
        senses.add((id_, sense))
        duplicates = update_nodes(id_, senses, duplicates)
        senses_int_lst = cm.str_list_to_int_list([y for x,y in senses])
        senses_str_lst = cm.int_list_to_str_list(sorted(senses_int_lst))
        new_sense = ",".join(senses_str_lst)
    
    return new_sense, senses, duplicates



def merge_senses(nodes):
    """ Each stem is associated with a single sense value. Due to
        homonymy, a single stem could have multiple senses denoting
        multiple possible meanings. This method combines the multiple
        senses into a comma separated string of the possible senses.
        All nodes which have the same values for every parameter, 
        except the sense or base_sense, are considered as duplicates.
        This method removes all those duplicates and maintains only
        one node with all the senses separated by comma.
        
        The sense attribute is not looked into at this stage of 
        alignment. But for future purposes, they are stored under a
        single parameter.
        
        Input -> list of nodes from SH analyses
        Returns -> list of nodes (having merged the senses and removed
                   the duplicates)
    """
    
    duplicates = []
    new_nodes = []
    modified_senses = []
    
    new_id = 0
    
    for j in range(len(nodes)):
        first = nodes[j]
        
        node_id = first[0]
        word = first[1]
        chunk_id = first[2]
        position_in_chunk = first[3]
        phase = first[4]
        phase_color = first[5]
        stem = first[6]
        sense = first[7]
        inflectional_morph = first[8]
        base_stem = first[9]
        base_sense = first[10]
        derivational_morph = first[11]
        pre_verb = first[12]
        
        if node_id in duplicates:
            continue
        
        senses = set()
        base_senses = set()
        
        for i in range(len(nodes)):
            if i == j:
                continue
            
            word_condition = (word == nodes[i][1])
            chunk_conditions = (
                (chunk_id == nodes[i][2]) and
                (position_in_chunk == nodes[i][3])
            )
            phase_conditions = (
                (phase == nodes[i][4]) and
                (phase_color == nodes[i][5])
            )
            stem_condition = (stem == nodes[i][6])
            base_stem_condition = (base_stem == nodes[i][9])
            morph_conditions = (
                (inflectional_morph == nodes[i][8]) and
                (derivational_morph == nodes[i][11])
            )
            stem_sense_condition = (not (sense == nodes[i][7]))
            base_stem_sense_condition = (not (base_sense == nodes[i][10]))
            
            if (word_condition and chunk_conditions and phase_conditions and 
                stem_condition and base_stem_condition and morph_conditions):
                # This checks if all the parameters are the same
                # except the sense and base_sense parameters
                if stem_sense_condition:
                    senses.add((nodes[i][0], nodes[i][7]))
                if base_stem_sense_condition:
                    base_senses.add((nodes[i][0], nodes[i][10]))
        
        new_sense, senses, duplicates = get_new_sense(senses, node_id,
                                                      sense, duplicates)
        new_base_sense, base_senses, duplicates = get_new_sense(base_senses,
                                                                node_id, 
                                                                base_sense, 
                                                                duplicates)
        
        new_node = (
            str(new_id), word, chunk_id, position_in_chunk, phase,
            phase_color, stem, new_sense, inflectional_morph, base_stem,
            new_base_sense, derivational_morph, pre_verb
        )
        new_nodes.append(new_node)
        
        if not (new_sense == sense and new_base_sense == base_sense):
            items_str = (
                chunk_id, position_in_chunk, stem, new_sense,
                base_stem, new_base_sense, str(new_id)
            )
#            print(items_str)
            modified_senses.append("\t".join(items_str))
        
        new_id += 1
    
    return new_nodes, modified_senses


def kill(proc_pid):
    """ Kills a sub-process(pid) and its children """
    
    process = psutil.Process(proc_pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()
    
    
def extract_analysis(sent_id, sentence, cgi_file, time_out_file):
    """ Runs the cgi file with a given sentence.  Gets all the analyses
        in the form a list of tuples (called nodes).
        
        Returns the final nodes (list of tuples of SH analyses, where
        each tuple corresponds to an individual segment)
    """
    
    env_vars = [
        "lex=SH", "cache=t", "st=t", "us=f", "font=roma", "pipeline=t",
        "text=" + sentence.replace(" ", "+"), "t=WX", "topic=", "mode=g"
    ]
#    query_string = "QUERY_STRING=\"lex=SH&cache=t&st=t&us=f&font=roma&"
#                   + "pipeline=t&text=" + sentence.replace(" ", "+") 
#                   + "&t=WX&topic=&mode=g&corpmode=&corpdir=&sentno=\""
    query_string = "QUERY_STRING=\"" + "&".join(env_vars) + "\""
    command = query_string + " " + cgi_file
    time_out = 10
    
    p = sp.Popen(command, stdout=sp.PIPE, shell=True)
    try:
        outs, errs = p.communicate(timeout=time_out)
    except sp.TimeoutExpired:
        kill(p.pid)
        result = ""
    else:
        result = outs.decode('utf-8')
    
    if result == "":
        time_out_file.write(str(sent_id) + "\t" + sentence + "\n")
        return []
    
    all_nodes_str = result.split("\n")
    all_nodes = [tuple(node_str.split("\t")) for node_str in all_nodes_str]
    
    return (all_nodes, result)
    

def discard_chunk_info(nodes):
    """ Removes duplicates after discarding chunk information """
    
    new_nodes = []
    uniq_nodes = []
    new_id = 0
    
    for node in nodes:
#        segment_id = str(node[0])
        word = node[1]
        chunk_id = str(node[2])
        position_in_chunk = str(node[3])
        phase = node[4]
        phase_color = node[5]
        stem = node[6]
        stem_sense = node[7]
        inf_morph = node[8]
        base_stem = node[9]
        base_sense = node[10]
        der_morph = node[11]
        pre_verb = node[12]
        
        node_detail = (word, phase, phase_color, stem, stem_sense, inf_morph, 
                    base_stem, base_sense, der_morph, pre_verb)
        
        if not node_detail in uniq_nodes:
            new_node = (str(new_id), word, phase, phase_color, stem, stem_sense, 
                        inf_morph, base_stem, base_sense, der_morph, pre_verb)
            
            uniq_nodes.append(node_detail)
            new_nodes.append(new_node)
            
            new_id += 1
    
    return new_nodes
    


def get_she_analysis(sent_id, sentence, sh_path,
                     cgi_file, time_out_file, extract=False):
    """ Extracts SH analyses, performs merging senses and 
        changing anusvaara if required.  Writes the analyses
        into a .tsv file in the corresponding directory
    """
    
    if extract:
        (all_nodes, sh_nodes_str) = extract_analysis(sent_id, sentence, 
                                                     cgi_file, time_out_file)
        all_nodes, modified_senses = merge_senses(all_nodes)
        sh_nodes_str = cm.list_to_string_for_file(all_nodes)
        
        write_she_path = os.path.join(sh_path, (str(sent_id) + ".tsv"))
        with open(write_she_path, 'w') as out_file:
            out_file.write(sh_nodes_str)
    else:
        all_nodes = cm.tuple_from_file(sh_path)
        sh_nodes_str = cm.list_to_string_for_file(all_nodes)
        modified_senses = []
    
    return all_nodes, modified_senses
    

