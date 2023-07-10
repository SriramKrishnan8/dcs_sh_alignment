import sys
import os

from tqdm import tqdm

import common_methods as cm
import extract_sh_analysis as es

script, sent, sh_dir, cgi_file, dcs_dir, timed, merged, missed = sys.argv

lines = cm.list_from_file(sent)

time_out_file = open(timed, "a+")
merged_file = open(merged, "a+")
missed_file = open(missed, "a+")

#for i in range(len(lines)):
for i in tqdm(range(len(lines))):
    line = lines[i]
    line_s = line.split("\t")
    
    sent_id = line_s[0]
    sentence = line_s[1]
    
    sh_path = os.path.join(sh_dir, (str(sent_id) + ".tsv"))
    if not os.path.isfile(sh_path):
        missed_file.write(line + "\n")
        continue
    
    all_nodes, modified_senses = es.get_she_analysis(
                                     sent_id, sentence, sh_path,
                                     cgi_file, time_out_file,
                                     extract=True
                                 )
    
    if len(modified_senses) > 0:
        ided_senses = [str(sent_id) + "\t" + x for x in modified_senses]
        senses_str = "\n".join(ided_senses)
        merged_file.write(senses_str + "\n")
