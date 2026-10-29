/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        attendx: {
          primary: "#2864E8",
          hover: "#1F55C7",
          bg: "#F7F9FC",
          card: "#FFFFFF",
          text: "#202938",
          muted: "#728096",
          border: "#E5EAF1",
          navActive: "#EDF4FF",
        },
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
      },
      borderRadius: {
        card: "14px",
        btn: "9px",
      },
    },
  },
  plugins: [],
};

