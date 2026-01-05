EMCC ?= emcc
BUILD_DIR := build
SRC := main.c
OUTPUT_BASE := $(BUILD_DIR)/main
JS := $(OUTPUT_BASE).js
WASM := $(OUTPUT_BASE).wasm

.PHONY: all clean
all: $(JS)

$(JS): $(SRC)
	@mkdir -p $(BUILD_DIR)
	$(EMCC) $(SRC) -o $(JS) \
		-s EXPORTED_FUNCTIONS='["_say_hello"]' \
		-s EXTRA_EXPORTED_RUNTIME_METHODS='["cwrap"]' \
		-s NO_EXIT_RUNTIME=1

clean:
	rm -rf $(BUILD_DIR)
