import subprocess as sp
import re
from devconvert import dev2slp, iast2slp, slp2dev, slp2iast, slp2tex, slp2wx, wx2slp, dev2wx

natva_permissing_letters = "aAiIuUqQLeEoOMkKgGfpPbBmyrvRh"
natva_inhibiting_letters = "cCjJFtTdDNwWxXnlsS"

second_solution_pairs_iast = [('t', 'h'), ('ḥ', 's'), ('k', 'h'), ('ṭ', 's')]
second_solution_pairs_wx = [('w', 'h'), ('H', 's'), ('k', 'h'), ('t', 's')]

def natva_inhibited(aft_r):
    index_n = aft_r.find("n")
    if (index_n == (len(aft_r) - 1)):
        return (True, index_n)
    if index_n == -1:
        return (False, index_n)
    bef_n = aft_r[:index_n]
    bef_n_status = [False]
    bef_n_status = [True for (i,v) in enumerate(bef_n) if (v in natva_inhibiting_letters)]
    status = True if (True in bef_n_status) else False
    return (status, index_n)

def natva_status(first, second, letter):
	if (letter in first):
		index_r = first.rfind(letter)
		aft_r = first[(index_r + 1):]
		(status, index) = natva_inhibited(aft_r)
		if status:
			return (first, second)
		if ("n" in second):
			(status, index) = natva_inhibited(second)
			if not status:
				second = second[:index] + "N" + second[(index + 1):]
	return (first, second)
	
def natva(first, second):
	(first, second) = natva_status(first, second, "r")
	(first, second) = natva_status(first, second, "R")
	(first, second) = natva_status(first, second, "q")
	(first, second) = natva_status(first, second, "Q")
	(first, second) = natva_status(first, second, "L")
	return (first, second)

def get_sandhied_form(first, second, natva_needed = True):
	if ((not (first == "")) and (not (second == ""))):
		if natva_needed:
			(first, second) = natva(first, second)
#		print(first + "--" + second)
		p = sp.Popen(['perl', 'sandhi/sandhi.pl', first, second], stdout=sp.PIPE)
		result = (p.communicate()[0]).decode('utf-8')
#		print(result)
		result_string = re.search(r':?(.*?),', result).group(1)
		result_list = result_string.split(':')
		return result_list
	else:
		if (first == ""):
			return [second]
		elif (second == ""):
			return [first]
		else:
			return []
			
def sandhi_join(first, second, pre_verb):
#	new_first = slp2wx.convert(iast2slp.convert(first))
#	new_second = slp2wx.convert(iast2slp.convert(second))
#	sandhied_word_list = get_sandhied_form(new_first, new_second, (not pre_verb))
	
	sandhied_word_list = get_sandhied_form(first, second, (not pre_verb))
#	print(sandhied_word_list)
	if (len(sandhied_word_list) == 0):
		return (first + second)
	else:
		sandhied_word = ""
#		print(first + ";" + second)
#		if ((not (first == "")) and (not (second == ""))):
#			print(first[-1] + ";" + second[0])
#		print(sandhied_word_list)
		if (first == "") or (second == ""):
			sandhied_word = sandhied_word_list[0]
		elif (first[-1],second[0]) in second_solution_pairs_wx:
			sandhied_word = sandhied_word_list[1]
		else:
			sandhied_word = sandhied_word_list[0]
		
#		return slp2iast.convert(wx2slp.convert(sandhied_word.strip()))
		return sandhied_word.strip()
