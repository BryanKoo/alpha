# q1 - choose meaning of a given word of a given level
#
# select a word, meaning of the given level and sub-level as the question and answer
select distinct(word) from words_bymeaning where level = 'B2' order by frequency limit 300 + ABS(RANDOM() % 10), 3;
# different sql can be used as follows
select distinct(word) from words_bymeaning where level = 'B2' and frequency > ?????? and frequency < ??????? order by random() limit 3;
# choose pos, meaning
select pos, meaning from words_bymeaning where level = 'B2' and word = 'xxx' order by random() limit 1;

# select other 3 meanings for the wrong choices other than the meanings of the question word (within the same level/pos)
select meaning from words_bymeaning where level = 'B2' and pos = 'ADVERB' and word != "xxx" order by random() limit 3;
