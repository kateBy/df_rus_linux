TARGET = Edited_DF64
PYTHON = python3

MAIN_OBJS = $(CACHE) $(CACHE_OBJS) Dwarf_Fortress64
MAIN = main.py
CACHE_OBJS = trans.po
CACHE = cache64.txt
REBUILD_CACHE = rebuild_cache.py


.PHONY: all clean


all: $(MAIN_OBJS)
	$(PYTHON) $(MAIN)

$(CACHE): $(CACHE_OBJS)
	$(PYTHON) $(REBUILD_CACHE) 

clean:
	rm $(TARGET) $(CACHE) 
