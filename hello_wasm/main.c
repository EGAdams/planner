#include <stdio.h>
#include <emscripten/emscripten.h>

EMSCRIPTEN_KEEPALIVE
void say_hello(void) {
    printf("Hello, World from WebAssembly!\n");
    emscripten_run_script("console.log('Hello, World from WebAssembly!');");
}

int main(void) {
    printf("Hello, World (startup)\n");
    return 0;
}
