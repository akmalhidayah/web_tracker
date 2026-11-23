import { readFile, writeFile } from "node:fs/promises";
import { build } from "esbuild";

const output = "../monitoring/static/monitoring/app";

await build({
  entryPoints: ["src/monitoring.jsx"],
  outfile: `${output}/monitoring.js`,
  bundle: true,
  minify: true,
  jsx: "automatic",
  target: ["safari15", "chrome112", "firefox110"],
  loader: { ".png": "dataurl" },
  define: { "process.env.NODE_ENV": '"production"' },
});

const packages = ["react", "react-dom", "scheduler", "leaflet", "lucide-react", "@mapbox/vector-tile", "@mapbox/point-geometry", "pbf"];
const licenses = await Promise.all(
  packages.map(async (name) => {
    const file = name === "@mapbox/vector-tile" ? "LICENSE.txt" : "LICENSE";
    const license = await readFile(`node_modules/${name}/${file}`, "utf8");
    return `${name}\n${license.trim()}`;
  }),
);
await writeFile(`${output}/licenses.txt`, licenses.join("\n\n"));
