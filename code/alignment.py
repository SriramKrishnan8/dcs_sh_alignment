import sys
import os
import subprocess as sp

import re
import json

from tqdm import tqdm

import common_methods as cm
import extract_sh_analysis as es
import anunAsika as an

script, sent, sh_dir, cgi_file, dcs_dir, out_dir, timed, missed, multiple, \
aligned, parallel, comp, pada, comp_trans, pada_trans, \
not_generated, sh_file_missing, missed_chunks = sys.argv

# Node parameters:
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

#The values for the following constants are obtained later.
# Mapper for morphological analyses of DCS and SH
dcs_sh_morph_map = {}

# Specific sandhi rules have two letters of the first word combined
# with one letter of the second word.  
double_lettered_sandhis = []

# Differences of pronoun stems between DCS and SH
pronoun_map = {}

# DCS stores the causative form of verbs as stems, while SH has the
# derived stem with the causative form and base stem with the root.  
nijanta_map = {}

# DCS does not have morphological analysis for avyayas.  To include
# these and map accordingly so that these are available in the 
# resultant dataset.  These entries are already obtained through
# some basic heuristics.
avyayas_list = []

# All possible SH phases for the non-final components of compounds.  
iics = [
    "Iic", "Iiv", "Iivc", "Iivv", "Iicc", "Iicv", "Iiy", "Iiif", 
    "A", "An", "Ai", "Ani", "Iik", "Iikv", "Iikc", 
    "Auxiinv", "Auxiick", "Cachei"
    ]
# All possible SH phases for the final components of compounds.  
ifcs = [
    "Ifc", "Ifcv", "Ifcc"
    ]
# All possible morph analyses of Avyayas
avyayas = [
    "part.", "prep.", "conj.", "abs.", "adv.", "tasil.", "ind."
    ]
    
    
def iic_phase(phase):
    """ Returns True if phase belongs to iic category """
    
    return phase in iics


def ifc_phase(phase):
    """ Returns True if phase belongs to ifc category """
    
    return phase in ifcs
    

def compound_component(phase):
    """ Returns True if phase belongs to iic or ifc category """
    
    return (iic_phase(phase) or ifc_phase(phase))
    

def transition_check(prev, next, dls):
    """ Returns sandhi effecting letters as a tuple """
    
    return ((prev, next) if (prev, next) in dls else (prev[1], next))
    

def check_for_avyaya(sent_id, chunk_id, position_in_chunk, stem, word, 
                     inf_morph, der_morph):
    """ Checks the list of all avyayas whose morph analyses is not 
        present in the DCS. This list is obtained prior to the 
        alignment process.
    """
    
#    print("\t".join((sent_id, chunk_id, position_in_chunk, stem, word, inf_morph, der_morph)))
    chunk_id_i = str(int(chunk_id) + 1)
    position_in_chunk_i = str(int(position_in_chunk) + 1)
    
    condition = (
        (inf_morph in avyayas) and
        (((sent_id, chunk_id_i, position_in_chunk_i, stem) in avyayas_list) or
        ((sent_id, chunk_id_i, position_in_chunk_i, word) in avyayas_list))
    )
    
    return condition


def align_morph(sent_id, chunk_id, position_in_chunk, stem, word, dcs_morph,
                  inf_morph, der_morph):
    """ Conditions for mapping DCS and SH morph analyses """
    
    if dcs_morph == "":
        return check_for_avyaya(sent_id, chunk_id, position_in_chunk, stem, 
                                word, inf_morph, der_morph)
        
    
    sh_morph = inf_morph if der_morph == "" else inf_morph + ";" + der_morph

    if sh_morph in dcs_sh_morph_map.keys():
        morph_conditions = (dcs_sh_morph_map[sh_morph] == dcs_morph)
    elif inf_morph in dcs_sh_morph_map.keys():
        morph_conditions = (dcs_sh_morph_map[inf_morph] == dcs_morph)
    elif der_morph in dcs_sh_morph_map.keys():
        morph_conditions = (dcs_sh_morph_map[der_morph] == dcs_morph)
    else:
        morph_conditions = False
    
    return morph_conditions
    

def pronoun_mapping(dcs_stem, stem, base_stem):
    """ Conditions to check for Pronouns """
    
    conditions = (
        (dcs_stem == pronoun_map.get(stem, "")) or
        (dcs_stem == pronoun_map.get(base_stem, "")) or
        (stem == pronoun_map.get(dcs_stem, "")) or
        ((not (base_stem == "")) and 
        (base_stem == pronoun_map.get(dcs_stem, "")))
    )
    
    return conditions


def nijanta_mapping(dcs_stem, stem, base_stem):
    """ Conditions to check for Pronouns """
    
    conditions = (
        (dcs_stem == nijanta_map.get(stem, "")) or
        (dcs_stem == nijanta_map.get(base_stem, "")) or
        (stem == nijanta_map.get(dcs_stem, "")) or
        ((not (base_stem == "")) and 
        (base_stem == nijanta_map.get(dcs_stem, "")))
    )
    
    return conditions
    
    
def stem_mapping(dcs_stem, stem, base_stem, phase, word):
    """ Conditions for mapping DCS and SH stem analyses """
    
    stems_conditions = (
        (dcs_stem == stem) or (dcs_stem == base_stem) or
        pronoun_mapping(dcs_stem, stem, base_stem) or
        nijanta_mapping(dcs_stem, stem, base_stem)
#        ((iic_phase(phase)) and (dcs_stem == word))
    )
    
    return stems_conditions
    
    
def align_stem(dcs_stem, stem, base_stem, phase, word):
    """ Alignment of DCS stem with SH's stem """
    
    stem_alignment = stem_mapping(dcs_stem, stem, base_stem, phase, word)
    if not stem_alignment:
        stem_alignment = stem_mapping(an.to_anunasika(dcs_stem),
                                      an.to_anunasika(stem),
                                      an.to_anunasika(base_stem),
                                      phase,
                                      an.to_anunasika(word))
    return stem_alignment
    
    
def compare_dcs_sh(sent_id, dcs_chunk_id, dcs_position_in_chunk, 
                   dcs_stem, dcs_morph, sh_nodes):
    """ For a specific dcs_entry, check all the nodes from SH and
        compare all the values in a systematic way to choose the 
        possible alignment. Compares stem and morphological analyses 
        and chooses the SH node which matches the DCS entry.
        
        Input:
        dcs_entry -> contains the analyses of DCS for a segment
        sh_nodes -> all the nodes for a sentence
        
        Returns all the nodes aligned with the dcs_entry
    """
    
#    print(", ".join((dcs_chunk_id, dcs_position_in_chunk, dcs_stem, dcs_morph)))
    
    segment_nodes = []
    for node in sh_nodes:
        segment_id = str(node[0])
        chunk_id = str(node[1])
        position_in_chunk = str(node[2])
        phase_id = str(node[3])
        prev_phase_ids = node[4]
        word = node[5]
        phase = node[6]
        phase_color = node[7]
        stem = node[8]
        stem_sense = node[9]
        inf_morph = node[10]
        base_stem = node[11]
        base_sense = node[12]
        der_morph = node[13]
        pre_verb = node[14]
        
        chunk_conditions = (
            (chunk_id == dcs_chunk_id) and 
            (position_in_chunk == dcs_position_in_chunk)
        )
        # Temporarily using only the chunk id to map the systems
        if not (chunk_id == dcs_chunk_id):
            continue
            
        stems_conditions = align_stem(dcs_stem, stem, base_stem, 
                                        phase, word)
        
        morphs_condition = align_morph(sent_id, chunk_id, position_in_chunk,
                                         dcs_stem, word, dcs_morph, 
                                         inf_morph, der_morph)
        
        if stems_conditions and morphs_condition:
            segment_nodes.append(node)
        
    return segment_nodes
    

def align(data, all_nodes):
    """ The Alignment process which runs through all the segments from
        DCS data (ground-truth data), and tries to match with each of
        the nodes obtained from the SH analyses.
        
        Input:
        data -> DCS data (json)
        all_nodes -> list of tuples from SH analyses
        
        Returns the following:
        final_segment_nodes -> SH nodes of aligned segments 
        single_alignments -> segments which have exactly one match
        multiple_alignments -> segments which have multiple matches
        missed_alignments -> segments which have no matches
        generate_parallel -> True if all segments have only one match
    """
    
    sent_id = data.get("sent_id")
    stems = data.get("stem", [])
    morphs = data.get("morph", [])
    stem_ids = data.get("stem_id", [])
    unsegmented_forms = data.get("unsegmented_form", [])
    
    generate_parallel = True
    single_alignments = []
    multiple_alignments = []
    missed_alignments = []
    final_segment_nodes = []
    incorrect_chunk_segmentations = []
    for i in range(len(stems)):
        final_segment_nodes_inner = []
        expected_stem_morph = []
        for j in range(len(stems[i])):
            segment_nodes = compare_dcs_sh(str(sent_id), str(i), str(j),
                                           stems[i][j], morphs[i][j],
                                           all_nodes)

#            print(segment_nodes)
            if len(segment_nodes) == 0:
                expected_stem_morph.append(stems[i][j]
                                           + "("
                                           + morphs[i][j]
                                           + ")")
                missed_alignments.append((str(sent_id), str(i), str(j),
                                         str(stem_ids[i][j]), stems[i][j],
                                         morphs[i][j]))
                generate_parallel = False
            elif len(segment_nodes) > 1:
                final_segment_nodes_inner.append(segment_nodes)
                multiple_alignments.append((str(sent_id), str(i), str(j),
                                           str(stem_ids[i][j]), stems[i][j],
                                           morphs[i][j]))
                generate_parallel = False
            else:
                final_segment_nodes_inner.append(segment_nodes)
                single_alignments.append((str(sent_id), str(i), str(j),
                                         str(segment_nodes[0][5]),
                                         str(stem_ids[i][j]), stems[i][j],
                                         morphs[i][j]))
            
#            print(generate_parallel)
        # This condition is to check if alignment is obtained for all 
        # the segments in this chunk.  If not, then collect the chunks
        #  and its expected stems and morphs from DCS
        if len(final_segment_nodes_inner) < len(stems[i]):
            expected_stem_morph_str = "\t".join(expected_stem_morph)
            incorrect_chunk_segmentations.append((str(sent_id),
                                                  unsegmented_forms[i],
                                                  expected_stem_morph_str))
            
        final_segment_nodes.append(final_segment_nodes_inner)
    
    return (final_segment_nodes, single_alignments, multiple_alignments, 
            missed_alignments, generate_parallel,
            incorrect_chunk_segmentations)


def create_new_data(data, segment_nodes):
    """ Creates a new dataset after the alignment of DCS data with 
        SH's segment nodes.
        
        Input -> data (DCS data), segment_nodes (aligned nodes from SH)
    """
    
#    print(segment_nodes)
    
    segmented_sentence = ""
    comp_entries = []
    pada_entries = []
    comp_trans_entries = []
    pada_trans_entries = []
    
    # New json data is built to include the SH parameters.  
    # This again has the values in the list of lists format, where the
    # outer list has the chunk elements and inner lists have segments
    
    new_data = {}
    new_data["text"] = data.get("text")
    new_data["text_id"] = data.get("text_id")
    new_data["chapter"] = data.get("chapter")
    new_data["chapter_id"] = data.get("chapter_id")
    new_data["sent_counter"] = data.get("sent_counter")
    new_data["sent_sub_counter"] = data.get("sent_sub_counter")
    new_data["sent_id"] = data.get("sent_id")
    new_data["joint_sentence"] = data.get("joint_sentence")
    new_data["position"] = data.get("position")
    new_data["unsegmented_form"] = data.get("unsegmented_form")
    
    dcs_stems = data.get("stem")
    dcs_stem_ids = data.get("stem_id")
    dcs_morphs = data.get("morph")
    dcs_words = data.get("word")
    
    node_ids = []
    sh_words = []
    words = []
    phases = []
    phase_colors = []
    sh_stems = []
    stems = []
    sh_stems_senses = []
    sh_bases = []
    bases = []
    sh_base_senses = []
    sh_morphs = []
    sh_base_morphs = []
    pre_verbs = []
    
    position = new_data["position"]
    for i in range(len(position)):
        inner_node_id = []
        inner_sh_word = []
        inner_word = []
        inner_phase = []
        inner_phase_color = []
        inner_sh_stem = []
        inner_sh_stem_sense = []
        inner_stem = []
        inner_sh_base = []
        inner_sh_base_sense = []
        inner_base = []
        inner_sh_morph = []
        inner_sh_base_morph = []
        inner_pre_verb = []
        
        # Some segments do not have their phase marked as Ifc.  
        # This state is maintained to operate on those segments too.  
        # When an iic is obtained, this state is toggled to True.  When
        # any other phase is obtained, this state is toggled to False.
        iic_state = False
        
        # These two store the sandhi effecting letters.  
        prev = ""
        next = ""
        
        for j in range(len(position[i])):
            current_segment_nodes = segment_nodes[i][j][0]
            
            node_id = current_segment_nodes[0]
            chunk_id = current_segment_nodes[1]
            sub_chunk_id = current_segment_nodes[2]
            sh_word = current_segment_nodes[5]
            word = an.to_anunasika(sh_word)
            phase = current_segment_nodes[6]
            phase_color = current_segment_nodes[7]
            sh_stem = current_segment_nodes[8]
            sh_stem_sense = current_segment_nodes[9]
            stem = an.to_anunasika(sh_stem)
            sh_morph = current_segment_nodes[10]
            sh_base = current_segment_nodes[11]
            sh_base_sense = current_segment_nodes[12]
            base = an.to_anunasika(sh_base)
            sh_base_morph = current_segment_nodes[13]
            pre_verb = current_segment_nodes[14]
            
            dcs_stem = dcs_stems[i][j]
            dcs_stem_id = dcs_stem_ids[i][j]
            dcs_morph = dcs_morphs[i][j]
            dcs_word = dcs_words[i][j]
            
            inner_node_id.append(node_id)
            inner_word.append(word)
            inner_sh_word.append(sh_word)
            
            # Construct segmented sentence using the phase.
            # Compound words will have a hyphen("-") between components
            # Words will have space(" ") between them
            cur_segment = (word + "-") if iic_phase(phase) else word + " "
            segmented_sentence = "".join((segmented_sentence, cur_segment))
            
            if compound_component(phase) or iic_state:
                comp_entries.append((sent_id, chunk_id, sub_chunk_id,
                                    dcs_stem, dcs_stem_id, 
                                    dcs_morph, dcs_word,
                                    sh_word, phase, sh_stem, sh_stem_sense,
                                    sh_base, sh_base_sense,
                                    sh_morph, sh_base_morph,
                                    word, stem, base))
            else:
                pada_entries.append((sent_id, chunk_id, sub_chunk_id,
                                    dcs_stem, dcs_stem_id, 
                                    dcs_morph, dcs_word,
                                    sh_word, phase, sh_stem, sh_stem_sense,
                                    sh_base, sh_base_sense,
                                    sh_morph, sh_base_morph,
                                    word, stem, base))
                
            if prev == "":
               prev = word[-2:]
            else:
                next = word[0]
                trans_tuple = transition_check(prev, next,
                                               double_lettered_sandhis)
                if iic_state:
                    comp_trans_entries.append(trans_tuple)
                else:
                    pada_trans_entries.append(trans_tuple)
                prev = word[-2:]
                
            iic_state = iic_phase(phase)
            
            inner_phase.append(phase)
            inner_phase_color.append(phase_color)
            inner_sh_stem.append(sh_stem)
            inner_sh_stem_sense.append(sh_stem_sense)
            inner_stem.append(stem)
            inner_sh_base.append(sh_base)
            inner_sh_base_sense.append(sh_base_sense)
            inner_base.append(base)
            inner_sh_morph.append(sh_morph)
            inner_sh_base_morph.append(sh_base_morph)
            inner_pre_verb.append(pre_verb)
        node_ids.append(inner_node_id)
        words.append(inner_word)
        sh_words.append(inner_sh_word)
        phases.append(inner_phase)
        phase_colors.append(inner_phase_color)
        sh_stems.append(inner_sh_stem)
        sh_stems_senses.append(inner_sh_stem_sense)
        stems.append(inner_stem)
        sh_bases.append(inner_sh_base)
        sh_base_senses.append(inner_sh_base_sense)
        bases.append(inner_base)
        sh_morphs.append(inner_sh_morph)
        sh_base_morphs.append(inner_sh_base_morph)
        pre_verbs.append(inner_pre_verb)
    
    new_data["node_id"] = node_ids
    new_data["dcs_word"] = dcs_words
    new_data["sh_word"] = sh_words
    new_data["word"] = words
    new_data["phase"] = phases
    new_data["phase_color"] = phase_colors
    new_data["dcs_stem"] = dcs_stems
    new_data["sh_stem"] = sh_stems
    new_data["sh_stem_sense"] = sh_stems_senses
    new_data["stem"] = stems
    new_data["sh_base"] = sh_bases
    new_data["sh_base_sense"] = sh_base_senses
    new_data["base"] = bases
    new_data["dcs_morph"] = dcs_morphs
    new_data["sh_morph"] = sh_morphs
    new_data["sh_base_morph"] = sh_base_morphs
    new_data["pre_verb"] = pre_verbs
    
    new_data["upos"] = data.get("upos")
    new_data["xpos"] = data.get("xpos")
    new_data["head"] = data.get("head")
    new_data["deprel"] = data.get("deprel")
#    new_data["deps"] = data.get("deps")
    new_data["misc"] = data.get("misc")
    new_data["sem_ids"] = data.get("sem_ids")
    
    pc_entries = (
        sent_id,
        sentence,
        segmented_sentence.strip()
    )
    
    return (new_data, pc_entries,
            pada_entries, comp_entries,
            pada_trans_entries, comp_trans_entries)


# Constants required for the alignment process are obtained here.  
dcs_sh_morph_map, double_lettered_sandhis, \
pronoun_map, nijanta_map, avyayas_list = cm.get_all_required_constants()

# Results are written into these files.  
# To save sentences which take huge time to retrieve analyses from SH.
time_out_file = open(timed, "a+")
# To record DCS stems whose match couldn't be found in SH analyses.  
missed_file = open(missed, "a+")
# To record DCS stems which have multiple maps with SH analyses.  
multiple_file = open(multiple, "a+")
# To record DCS stems which have exactly one mapping with SH analyses.
aligned_file = open(aligned, "a+")
# To save sentences where each of the DCS stems in a sentence have 
# exactly one match with SH analyses..
parallel_file = open(parallel, "a+")
# To record all segments which are a part of a compound, along with 
# their features from both DCS and SH.
comp_file = open(comp, "a+")
# To record all segments which are not a part of any compound, along  
# with their features from both DCS and SH.
pada_file = open(pada, "a+")
# To record all the instances of sandhi happening within a compound.
comp_trans_file = open(comp_trans, "a+")
# To record all the instances of sandhi happening between words.
pada_trans_file = open(pada_trans, "a+")
# To record all sentences for which alignment has not been done.  
not_generated_file = open(not_generated, "a+")
# To record all sentences whose sh file is missing
sh_file_missing_file = open(sh_file_missing, "a+")
# To record all the chunks whose segmentation is incorrect.  
missed_chunks_file = open(missed_chunks, "a+")

lines = cm.list_from_file(sent)

for i in range(len(lines)):
#for i in tqdm(range(len(lines))):
    line = lines[i]
    line_s = line.split("\t")
    
    sent_id = line_s[0]
    sentence = line_s[1]
    
#    print("\n")
#    print(sent_id)
    
    sh_path = os.path.join(sh_dir, (str(sent_id) + ".tsv"))
    if not os.path.isfile(sh_path):
        sh_file_missing_file.write(line + "\n")
#        print("SH file missing")
        continue
    
    all_nodes, modified_senses = es.get_she_analysis(sent_id, sentence,
                                                     sh_path, cgi_file,
                                                     time_out_file)
                                                     
#    print(cm.list_to_string_for_file(all_nodes))
    
    data = cm.get_dcs_json(sent_id, dcs_dir)
    
    segment_nodes, single_alignments, \
    multiple_alignments, missed_alignments, \
    generate_parallel, incorrect_chunks = align(data, all_nodes)
    
    if len(missed_alignments) > 0:
        missed_file.write(cm.list_to_string_for_file(missed_alignments))
    
    if len(multiple_alignments) > 0:
        multiple_file.write(cm.list_to_string_for_file(multiple_alignments))
    
    if len(single_alignments) > 0:
        aligned_file.write(cm.list_to_string_for_file(single_alignments))
        
    if len(incorrect_chunks) > 0:
        missed_chunks_file.write(cm.list_to_string_for_file(incorrect_chunks))
    
    if not generate_parallel:
        not_generated_file.write(line + "\n")
#        print("Not Generated")
        continue
    
    new_data, pc_entries, pada_entries, comp_entries, pada_trans_entries, \
    comp_trans_entries = create_new_data(data, segment_nodes)
    
    parallel_file.write("\t".join(pc_entries) + "\n")
#    print("Generated")
    
    pada_file.write(cm.list_to_string_for_file(pada_entries))
    comp_file.write(cm.list_to_string_for_file(comp_entries))
    pada_trans_file.write(cm.list_to_string_for_file(pada_trans_entries))
    comp_trans_file.write(cm.list_to_string_for_file(comp_trans_entries))
    
    new_json_path = os.path.join(out_dir, (str(sent_id) + ".json"))
    with open(new_json_path, 'w', encoding='utf-8') as out_file:
        json.dump(new_data, out_file, ensure_ascii=False)
