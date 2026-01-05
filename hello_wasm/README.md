# Hello WebAssembly

This minimal example compiles a C-based "Hello, World" program into WebAssembly using Emscripten. The resulting bundle prints the greeting both in the terminal (when executed via the generated JavaScript glue) and in the browser console.

## Prerequisites

Install the [Emscripten SDK](https://emscripten.org/docs/getting_started/downloads.html):

```bash
git clone https://github.com/emscripten-core/emsdk.git
cd emsdk
./emsdk install latest
./emsdk activate latest
source ./emsdk_env.sh
```

This will make `emcc` available on your `PATH`.

## Building

```bash
cd hello_wasm
make
```

The build artifacts (`main.js`, `main.wasm`, and supporting files) will be emitted under `hello_wasm/build`.

## Running in the Browser

Because browsers prohibit loading WebAssembly via the `file://` protocol, start a simple HTTP server from the repository root:

```bash
cd hello_wasm
python3 -m http.server 8000
```

Then open `http://localhost:8000/index.html` in your browser. The page itself shows a heading, and the console log will display "Hello, World from WebAssembly!" when the WebAssembly module initializes.

## Running via Node.js (Optional)

If you prefer to run the WebAssembly module from Node.js, first build as described above and then execute:

```bash
node build/main.js
```

This will run the compiled module in Node and should print the greeting to stdout.
