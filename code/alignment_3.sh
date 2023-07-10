# Use the DCS sentences available from ./data/dcs/

# Converting DCS analysis from IAST to WX

mkdir -p observations/alignment_3/dcs_conversion/
python3 convert_dcs_to_wx.py ../data/dcs/dcs_sentences.tsv ../data/dcs_json_files/ ../dcs_json_wx/ dcs_conversion/missed.tsv dcs_conversion/already.tsv

# Extracting SH analyses

mkdir -p observations/alignment_3/she_extraction/
mv ../data/dcs/dcs_sentences.tsv ../data/dcs/dcs_sentences_iast.tsv 
transliterate -d iast -e wx -i ../data/dcs/dcs_sentences_iast.tsv -o ../data/dcs/dcs_sentences.tsv
sh extract_she_analysis.sh ../data/dcs/dcs_sentences.tsv ../data/sh/sh_files/ cgi_file ../data/dcs/dcs_json_wx observations/alignment_3/she_extraction/timed observations/alignment_3/she_extraction/merged observations/alignment_3/she_extraction/missed

# Alignment 2

# Step 1 and 2 - Normalization and Alignment

mkdir -p observations/alignment_3/step_1/aligned_dataset
mkdir -p observations/alignment_3/modifications
mkdir -p observations/alignment_3/step_2/aligned_dataset

STEP_1=observations/alignment_3/step_1
MOD=observations/alignment_3/modifications
STEP_2=observations/alignment_3/step_2

python3 alignment_without_chunk.py ../data/dcs/dcs_sentences.tsv ../data/sh/sh_files/ sktgraph ../data/dcs/dcs_json_wx/ $STEP_1/aligned_dataset/ $STEP_1/time_out.tsv $STEP_1/missed.tsv $STEP_1/multiple.tsv $STEP_1/aligned.tsv $STEP_1/parallel.tsv $STEP_1/comp_entries.tsv $STEP_1/pada_entries.tsv $STEP_1/comp_transitions.tsv $STEP_1/pada_transitions.tsv $STEP_1/not_generated.tsv $STEP_1/sh_file_missing.tsv $STEP_1/missed_chunks.tsv $STEP_1/dcs_file_missing.tsv

# Step 3 - Modifications to SH analyses

cp $STEP_1/not_generated.tsv $MOD/to_be_modified.tsv
mkdir -p ../data/sh/modified_sh_files/

python3 compounding.py $MOD/to_be_modified.tsv ../data/dcs/dcs_json_wx/ ../data/sh/sh_files/ ../data/sh/modified_sh_files/ $MOD/missed.tsv $MOD/modified.tsv $MOD/not_modified.tsv

# Step 4 - Re-alignment for modified sentences

python3 alignment_without_chunk.py $MOD/modified.tsv ../data/sh/modified_sh_files/ sktgraph ../data/dcs/dcs_json_wx/ $STEP_2/aligned_dataset/ $STEP_2/time_out.tsv $STEP_2/missed.tsv $STEP_2/multiple.tsv $STEP_2/aligned.tsv $STEP_2/parallel.tsv $STEP_2/comp_entries.tsv $STEP_2/pada_entries.tsv $STEP_2/comp_transitions.tsv $STEP_2/pada_transitions.tsv $STEP_2/not_generated.tsv $STEP_2/sh_file_missing.tsv $STEP_2/missed_chunks.tsv $STEP_2/dcs_file_missing.tsv

# Step 5 - Final aggregation of results

mkdir -p observations/alignment_3/final
mkdir -p observations/alignment_3/final/aligned_dataset/

FINAL=observations/alignment_3/final

cat $STEP_1/parallel.tsv $STEP_2/parallel.tsv >> $FINAL/parallel.tsv
cat $STEP_1/aligned.tsv $STEP_2/aligned.tsv >> $FINAL/aligned.tsv
cat $STEP_1/comp_entries.tsv $STEP_2/comp_entries.tsv >> $FINAL/comp_entries.tsv
cat $STEP_1/pada_entries.tsv $STEP_2/pada_entries.tsv >> $FINAL/pada_entries.tsv
cat $STEP_1/comp_transitions.tsv $STEP_2/comp_transitions.tsv >> $FINAL/comp_transitions.tsv
cat $STEP_1/pada_transitions.tsv $STEP_2/pada_transitions.tsv >> $FINAL/pada_transitions.tsv
cp $STEP_1/aligned_dataset/* $FINAL/aligned_dataset/
cp $STEP_2/aligned_dataset/* $FINAL/aligned_dataset/
