# select a word information of the given level and sub-level
#   sub-level is the percentage rank ordered by frequency within the level
#   A1 780, A2 1567, B1 2806, B2 3904, C1 2318, C2 3633 Total 15008
#   sub-level column is not needed because it can be determined in advance by counting number of word within a level
#   if number of word in a sub-level is 100 then the sub-level is 3 then the query will be as follows
select * from words_bymeaning where level = 'B2' order by frequency limit 1, 300 + ABS(RANDOM() % 100)
