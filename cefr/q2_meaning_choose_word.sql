# q2 - choose a word of a given meaning of a given level
#
# select a word, meaning of the given level and sub-level as the answer and the question
#   sub-level is the percentage rank ordered by frequency within the level (9 or 10 sub-levels for a level)
#   A1 780, A2 1567, B1 2806, B2 3904, C1 2318, C2 3633 Total 15008
#   sub-level column is not needed because it can be determined in advance by counting number of word within a level
#   if number of word in a sub-level is 300 then the sub-level is 2 then the query will be as follows
select distinct(word) from words_bymeaning where level = 'B2' order by frequency limit 300 + ABS(RANDOM() % 10), 1;
select pos, meaning from words_bymeaning where level = 'B2' and word = 'xxx';

# select 3 words that are the same or above level and the same pos with similar ending spell
select distinct(word) from words_bymeaning where (level = 'B2' or level = 'C1') and word like '%ly' and pos = 'ADVERB' and word != 'xxx' order by random() limit 3;
