/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/pages/**/*.{js,jsx}", "./src/components/**/*.{js,jsx}", "./src/context/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ember: "#E86A33",
        clay: "#F3E2D4",
        pine: "#0F4C5C",
        mist: "#F6FBFC",
        ink: "#10222B"
      },
      boxShadow: {
        glow: "0 24px 60px rgba(15, 76, 92, 0.18)"
      },
      keyframes: {
        rise: {
          "0%": { opacity: "0", transform: "translateY(18px)" },
          "100%": { opacity: "1", transform: "translateY(0)" }
        }
      },
      animation: {
        rise: "rise 0.6s ease-out both"
      }
    }
  },
  plugins: []
};
