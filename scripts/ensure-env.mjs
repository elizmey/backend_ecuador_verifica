import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { execFileSync } from "node:child_process";

const root = process.cwd();

const envTemplate = `ENV=development
DEBUG=true
SECRET_KEY=dev-only-change-me
CORS_ORIGINS=*
DATABASE_URL=sqlite:///./ecverifica.db
UPLOAD_DIR=uploads
AI_PROVIDER=mock
AI_ENABLED=true
WORKER_BACKEND=inline
PORT=8000
`;

const envPath = join(root, ".env");
if (!existsSync(envPath)) {
  writeFileSync(envPath, envTemplate, { encoding: "utf8" });
  console.log("[veriia] .env creado (SQLite + IA mock). Editalo si necesitas PostgreSQL u otro proveedor.");
} else {
  console.log("[veriia] .env ya existe.");
}

mkdirSync(join(root, "uploads"), { recursive: true });
mkdirSync(join(root, "logs"), { recursive: true });

try {
  execFileSync("py", ["-c", "import uvicorn, fastapi, sqlalchemy"], { stdio: "ignore" });
} catch {
  console.error("\n[veriia] Faltan dependencias de Python. Ejecuta:\n    pnpm install\n  o\n    pnpm run setup\n");
  process.exit(1);
}
