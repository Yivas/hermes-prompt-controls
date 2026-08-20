import { defineConfig } from "astro/config";
import starlight from "@astrojs/starlight";

export default defineConfig({
  site: "https://yivas.github.io",
  base: "/hermes-prompt-controls",
  integrations: [
    starlight({
      title: "Hermes Prompt Controls",
      description: "Explicit per-model system prompt controls for Hermes Agent.",
      customCss: ["./src/styles/custom.css"],
      editLink: {
        baseUrl: "https://github.com/Yivas/hermes-prompt-controls/edit/main/wiki/",
      },
      social: [
        {
          icon: "github",
          label: "GitHub",
          href: "https://github.com/Yivas/hermes-prompt-controls",
        },
      ],
      sidebar: [
        { label: "Overview", items: [{ label: "Home", slug: "" }] },
        {
          label: "Get started",
          items: [{ autogenerate: { directory: "getting-started" } }],
          collapsed: false,
        },
        {
          label: "Contract",
          items: [{ autogenerate: { directory: "contract" } }],
          collapsed: false,
        },
        {
          label: "Reference",
          items: [{ autogenerate: { directory: "reference" } }],
          collapsed: true,
        },
        {
          label: "Project",
          items: [{ autogenerate: { directory: "project" } }],
          collapsed: true,
        },
      ],
    }),
  ],
});
