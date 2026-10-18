import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const webDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const projectDir = path.resolve(webDir, '..');
const isWindows = process.platform === 'win32';

function run(command, args, cwd, label) {
  const child = spawn(command, args, {
    cwd,
    stdio: 'inherit',
    shell: isWindows,
    env: process.env,
  });
  child.on('error', (error) => {
    console.error(`[${label}] Could not start: ${error.message}`);
    stopAll(1);
  });
  child.on('exit', (code) => {
    if (!stopping) {
      console.error(`[${label}] exited${code === null ? '' : ` with code ${code}`}`);
      stopAll(code ?? 1);
    }
  });
  children.push(child);
  return child;
}

const children = [];
let stopping = false;

function stopAll(exitCode = 0) {
  if (stopping) return;
  stopping = true;
  for (const child of children) {
    if (child.exitCode === null) child.kill('SIGTERM');
  }
  setTimeout(() => process.exit(exitCode), 500);
}

process.on('SIGINT', () => stopAll(0));
process.on('SIGTERM', () => stopAll(0));

console.log('Starting FastAPI at http://localhost:8000 and frontend at http://localhost:5173');
run('python3', ['-m', 'uvicorn', 'api.main:app', '--reload'], projectDir, 'api');
run('npm', ['run', 'dev'], webDir, 'frontend');
