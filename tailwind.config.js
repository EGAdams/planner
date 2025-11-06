/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./public/**/*.html",
    "./public/**/*.js",
    "./**/*.ts",
    "!./node_modules/**",
    "!./backend/**"
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
