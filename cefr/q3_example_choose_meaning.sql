# q3 - choose meaning of a given word in a sentence of a given level
#
# select a word with 2 or more meanings 
# there will be wrong choice of meaning with the selected word
select word, count(*), min(level) from words_bymeaning group by word having count(*) > 1 and min(level) = 'B2' and min(frequency) > 244491090 and min(frequency) < 342373303 order by random() limit 3;
select pos, meaning, examples from words_bymeaning where level = 'B2' word = 'xxx';

# select other meanings for the wrong choices other than the meaning of question word (the same level, pos)
select meaning from words_bymeaning where level = 'B2' and pos = 'ADVERB' and word != "xxx" order by random() limit 2;
