const { ESLint } = require("eslint")

module.exports = [
  {
    extends: ["next/core-web-vitals"],
    rules: {
      "@typescript-eslint/no-unused-vars": "off",
      "react-hooks/exhaustive-deps": "off",
    },
  },
]
