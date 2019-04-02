# q2 - choose a word that is hidden in a sentence of a given level
#
# select a word, example of the given level and sub-level as the answer and the question
select distinct(word) from words_bymeaning where level = 'B2' order by frequency limit 300 + ABS(RANDOM() % 10), 1;
select pos, example from words_bymeaning where level = 'B2' word = 'xxx';

# select 3 words that are the same or above level and the same pos with similar ending spell
select distinct(word) from words_bymeaning where (level = 'B2' or level = 'C1') and word like '%ly' and pos = 'ADVERB' and word != 'xxx' order by random() limit 3;
