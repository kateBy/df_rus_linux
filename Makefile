TARGET = Edited_DF
PYTHON = python3

MAIN = main.py
CACHE_OBJS = trans.po
CACHE = cache.json
REBUILD_CACHE = rebuild_cache.py
MAIN_OBJS = $(CACHE) $(CACHE_OBJS) Dwarf_Fortress


.PHONY: all clean


all: $(MAIN_OBJS)
	$(PYTHON) $(MAIN)

$(CACHE): $(CACHE_OBJS)
	$(PYTHON) $(REBUILD_CACHE) 

clean:
	rm $(TARGET) $(CACHE) 
