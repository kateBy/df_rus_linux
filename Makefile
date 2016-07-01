TARGET = Edited_DF
PYTHON = python3

MAIN_OBJS = cache.txt trans.po Dwarf_Fortress
MAIN = main.py
CACHE_OBJS = trans.po
CACHE = cache.txt
REBUILD_CACHE = rebuild_cache.py


.PHONY: all clean


all: $(TARGET)

$(TARGET): $(MAIN_OBJS)
	$(PYTHON) $(MAIN)

$(CACHE): $(CACHE_OBJS)
	$(PYTHON) $(REBUILD_CACHE) 

clean:
	rm $(TARGET) $(CACHE) 
