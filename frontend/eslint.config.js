import js from "@eslint/js";
import globals from "globals";
import hooks from "eslint-plugin-react-hooks";
import refresh from "eslint-plugin-react-refresh";

export default [
  { ignores: ["dist/**", "node_modules/**", "coverage/**"] },
  {
    files: ["**/*.{js,jsx}"],
    ...js.configs.recommended,
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: globals.node,
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
    linterOptions: {
      noInlineConfig: true,
      reportUnusedDisableDirectives: "error",
    },
    rules: {
      ...js.configs.recommended.rules,
      complexity: ["error", 10],
      "max-lines-per-function": ["error", { max: 150 }],
      "max-params": ["error", 5],
    },
  },
  {
    files: ["src/**/*.{js,jsx}"],
    languageOptions: { globals: globals.browser },
  },
  {
    files: [
      "src/components/ui/**/*.{js,jsx}",
      "src/lib/**/*.js",
      "src/services/**/*.js",
    ],
    rules: {
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["**/features/**", "**/app/**", "**/layout/**"],
              message:
                "Camadas compartilhadas não devem depender das telas nem da aplicação.",
            },
          ],
        },
      ],
    },
  },
  {
    files: ["src/**/*.jsx"],
    plugins: { "react-refresh": refresh },
    rules: {
      "react-refresh/only-export-components": [
        "error",
        { allowConstantExport: true },
      ],
    },
  },
  {
    files: ["src/**/*.{js,jsx}"],
    plugins: { "react-hooks": hooks },
    rules: {
      "react-hooks/rules-of-hooks": "error",
      "react-hooks/exhaustive-deps": "error",
    },
  },
];
