# aupipe: HoldSpeak's baresip audio module (BSD-3-Clause, see aupipe.c).
#
#   make                         build ./aupipe.so against the installed baresip
#   make OUT=/some/dir           build into another folder
#   make BARESIP_PREFIX=~/opt    build against our own baresip build (Linux)
#
# The headers come from pkg-config (libre, libbaresip). With BARESIP_PREFIX
# the .pc files under that prefix win; on macOS Homebrew's are found as is.
# The module links nothing: baresip's own symbols resolve when it loads it.

OUT ?= .
CC ?= cc
UNAME := $(shell uname -s)

ifneq ($(BARESIP_PREFIX),)
PC_PATH := $(BARESIP_PREFIX)/lib/pkgconfig:$(BARESIP_PREFIX)/lib/x86_64-linux-gnu/pkgconfig:$(BARESIP_PREFIX)/lib/aarch64-linux-gnu/pkgconfig:$(PKG_CONFIG_PATH)
else
PC_PATH := $(PKG_CONFIG_PATH)
endif

# The path goes on the command itself: GNU make before 4.4 (Ubuntu 24.04 has
# 4.3) does not pass an exported variable to $(shell ...).
CFLAGS_RE := $(shell PKG_CONFIG_PATH="$(PC_PATH)" pkg-config --cflags libre libbaresip 2>/dev/null)
ifeq ($(CFLAGS_RE),)
ifeq ($(UNAME),Darwin)
CFLAGS_RE := -I/opt/homebrew/opt/libre/include/re -I/opt/homebrew/opt/baresip/include
endif
endif

CFLAGS ?= -O2
CFLAGS += -Wall -std=c11 -DHAVE_INTTYPES_H -DHAVE_STDBOOL_H

ifeq ($(UNAME),Darwin)
LDFLAGS_MOD := -bundle -undefined dynamic_lookup
else
CFLAGS += -fPIC -D_GNU_SOURCE
LDFLAGS_MOD := -shared
endif

$(OUT)/aupipe.so: aupipe.c
	@mkdir -p $(OUT)
	$(CC) $(CFLAGS) $(CFLAGS_RE) $(LDFLAGS_MOD) -o $@ $<

.PHONY: clean
clean:
	rm -f $(OUT)/aupipe.so
