import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { execFileSync } from "node:child_process";

const root = process.cwd();

const envTemplate = `ENV=development
DEBUG=true
CORS_ORIGINS=*
AI_PROVIDER=mock
AI_ENABLED=true
PORT=3008
`;

const envPath = join(root, ".env");
if (!existsSync(envPath)) {
  writeFileSync(envPath, envTemplate, { encoding: "utf8" });
  console.log("[veriia] .env creado (IA mock, puerto 3008). Editalo si necesitas otro proveedor de IA.");
} else {
  console.log("[veriia] .env ya existe.");
}

mkdirSync(join(root, "logs"), { recursive: true });

try {
  execFileSync("py", ["-c", "import uvicorn, fastapi, sqlalchemy"], { stdio: "ignore" });
} catch {
  console.error("\n[veriia] Faltan dependencias de Python. Ejecuta:\n    pnpm install\n  o\n    pnpm run setup\n");
  process.exit(1);
}
