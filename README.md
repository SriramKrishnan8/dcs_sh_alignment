# dcs_sh_alignment

The Alignment of DCS' (Digital Corpus of Sanskrit) analyses with SH (Sanskrit Heritage Platform)

Digital Corpus of Sanskrit([DCS](http://www.sanskrit-linguistics.org/dcs/)) is a corpus of more than 650,000 annotated Sanskrit sentences taken from around 250 texts. Sanskrit Heritage Segmenter([SH](http://www.sanskrit.inria.fr)) produces all the possible segments of a given sentence along with all the possible lexical and morphological analyses of each of the segments.

The DCS sentences (available at the DCS repository ([DCS-data](https://github.com/OliverHellwig/sanskrit)) in CoNLL-U format) are extracted and converted to JSON format (using [dcs_interface](https://github.com/SriramKrishnan8/dcs_interface)). These sentences are run on the SH and all the segments with their analyses are extracted and are made available here: [sh_analyses](https://github.com/SriramKrishnan8/sh_analyses).

This work is inspired from [A Dataset for Sanskrit Word Segmentation](https://aclanthology.org/W17-2214/) (data available at [sws-dataset](https://zenodo.org/record/803508#.YRdZ43UzaXJ)).

## Pre-requisites

### Install the following

```
sudo apt install python3
sudo apt install python3-pip
pip3 install devtrans
```

### DCS Sentences and Data

* Download the *dcs_sentences.tsv* from [dcs_json](https://drive.google.com/drive/u/3/folders/1erKh47n_JJfVeczhrFoOZEXluDiJyD10) and store it in *./data/dcs/*.

* To use the existing DCS json in WX format: download *dcs_json_wx.zip* from [dcs_json](https://drive.google.com/drive/u/3/folders/1erKh47n_JJfVeczhrFoOZEXluDiJyD10) and unzip it into  *./data/dcs/*.

* To convert DCS data from IAST to WX, afresh: download *dcs_json_files.zip* from [dcs_json](https://drive.google.com/drive/u/3/folders/1erKh47n_JJfVeczhrFoOZEXluDiJyD10) and unzip it into  *./data/dcs/*. And then run the following:

```
cd code/
mkdir -p observations/alignment_2/dcs_conversion/
python3 convert_dcs_to_wx.py ../data/dcs/dcs_sentences.tsv ../data/dcs_json_files/ ../dcs_json_wx/ dcs_conversion/missed.tsv dcs_conversion/already.tsv
```

### SH Analysis

* To use the existing SH analyses: download *sh_files.zip* from [dcs_json](https://drive.google.com/drive/u/3/folders/1-agVobkxVYXw5eIVX2JQHUwzqsR-NTXk) and unzip the contents to *./data/sh/*.

* To generate the latest analyses, run the following

```
mkdir -p observations/alignment_2/she_extraction/
mv ../data/dcs/dcs_sentences.tsv ../data/dcs/dcs_sentences_iast.tsv 
transliterate -d iast -e wx -i ../data/dcs/dcs_sentences_iast.tsv -o ../data/dcs/dcs_sentences.tsv
sh extract_she_analysis.sh ../data/dcs/dcs_sentences.tsv ../data/sh/sh_files/ cgi_file ../data/dcs/dcs_json_wx observations/alignment_2/she_extraction/timed.tsv observations/alignment_2/she_extraction/merged.tsv observations/alignment_2/she_extraction/missed.tsv
```

(Note: the *./code/sktgraph* is a binary generated from the SH platform. It is necessary that certain data files are to be present in */var/www/html/SKT/*. In the current update, it is not feasible to generate unless the SH platform is already installed. In the next update, this will be fixed by keeping all the necessary binaries in the repository itself.)

All the details of the alignments, implementation results and the normalized dataset for word segmentation and morphological parsing are avaialable at: [ND-SWSMP](https://drive.google.com/drive/folders/1VmffgzbcTyg9cJ6o4eTOFYInfG07Jl-H?usp=drive_link)

## Alignment 1

The aligned dataset details are available at: [dcs_sh_alignment_1](https://drive.google.com/drive/folders/1r4IgONLVboMvzh9B5ZJKnrW0lqW25J53?usp=drive_link).

## Alignment 1 - Hackathon

The aligned dataset details are available at: [wsmp_dataset](https://drive.google.com/drive/folders/112sLHYZd6FlQN9pcVn-AsXd-F5ZFHNim?usp=drive_link).

## Alignment 2

The aligned dataset details are available at: [dcs_sh_alignment_2](https://drive.google.com/drive/folders/1dzlAxrwzSR-gtUWlA4VdK82rdjibNRE3?usp=drive_link).

To generate your own, follow the instructions in *./code/alignment_2.sh*.

## Alignment 3

The aligned dataset details are available at: [dcs_sh_alignment_3](https://drive.google.com/drive/folders/1XTPr8ndKQhBUXJEkE8wxfNaNL0XYpU2r?usp=sharing).

To generate your own, follow the instructions in *./code/alignment_3.sh*.

## Citation

The details of the paper (for Alignment 1 and Hackathon) are available at [DCS-SH-Alignment](https://aclanthology.org/2023.wsc-csdh.3/).

The details of the paper for Alignments 2 and 3 will be released soon.
