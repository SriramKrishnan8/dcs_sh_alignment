import sys
import os

import re
import json

def list_from_file(file_name):
    """ Returns contents of a file as a list of its lines """
    
    file_ = open(file_name, "r", encoding='utf8')
    all_text = file_.read()
    all_lines = all_text.split("\n")
    list_ = list(filter(None, all_lines))
    
    return list_


def tuple_from_file(file_name):
    """ Returns contents of a file(.tsv) as a list of tuples 
        of its lines
    """
    
    list_ = list_from_file(file_name)
#    [(entry.split("\t")[0], entry.split("\t")[1]) for entry in list_]

    return list(map(lambda x: tuple(x.split("\t")), list_))


def tuple_list_to_string_list(list_, separator="\t"):
    """ Converts a list of tuples to a list of strings with values
        separated by a "\t"
    """
    
    return [separator.join(item) for item in list_]
    

def list_to_string_for_file(list_):
    """ Returns the string to be written to file """
    
    return "\n".join(tuple_list_to_string_list(list_)) + "\n"
    

def int_list_to_str_list(list_):
    """ Returns a list of strings from a list of int """
    
    return [str(x) for x in list_]


def str_list_to_int_list(list_):
    """ Returns a list of strings from a list of int """
    
    return [int(x) for x in list_]
    
    
def get_dcs_json(sent_id, dcs_dir):
    """ Returns json data from file """
    
    json_path = os.path.join(dcs_dir, (str(sent_id) + ".json"))
    json_input = open(json_path, 'r')
    data = json.load(json_input)
    
    return data

    
def get_dcs_sh_morph_map(file_name):
    """ Returns dictionary of SH-DCS morphological analyses mapper """
    
    map_tuples = tuple_from_file(file_name)
    
    return dict((y, x) for x, y in map_tuples)
    
    
def get_all_required_constants():
    """ Creates all the required constants for the alignment """
    
    dcs_sh_morph_map = get_dcs_sh_morph_map("dcs_sh_morph_map.tsv")
    double_lettered_sandhis = tuple_from_file("double_lettered_sandhi.tsv")
    pronoun_map = dict(tuple_from_file("pronoun_map.tsv"))
    nijanta_map = dict(tuple_from_file("nijanta_map_updated.tsv"))
    avyayas_list = tuple_from_file("possible_avyayas_uniq.tsv")
    
    return (dcs_sh_morph_map, double_lettered_sandhis, 
            pronoun_map, nijanta_map, avyayas_list)
    
def print_list_of_tuples(list_):
    list_str = ["\t".join(x) for x in list_]
    str_ = "\n".join(list_str)
    
    print(str_)
