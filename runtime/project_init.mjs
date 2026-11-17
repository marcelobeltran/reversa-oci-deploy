import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';
const pkg = path.join(execFileSync('/usr/bin/npm', ['root', '-g'], { encoding: 'utf8' }).trim(), 'reversa');
const version = JSON.parse(fs.readFileSync(path.join(pkg, 'package.json'), 'utf8')).version;
if (version !== '1.3.4') throw new Error('Se requiere Reversa 1.3.4 para este inicializador.');
const { Writer } = await import(pathToFileURL(path.join(pkg, 'lib/installer/writer.js')));
const { buildManifest, saveManifest } = await import(pathToFileURL(path.join(pkg, 'lib/installer/manifest.js')));
if (process.argv.includes('--check')) { console.log('Módulos oficiales de Reversa cargados.'); process.exit(0); }
const requested = process.argv.slice(2).find(arg => !arg.startsWith('--')) || process.cwd();
const root = fs.realpathSync('/home/opc/proyectos');
const project = fs.realpathSync(requested);
if (path.dirname(project) !== root || path.basename(project).startsWith('.')) throw new Error('Selecciona un proyecto bajo /home/opc/proyectos.');
const lock = path.join(project, '.reversa-init-lock');
fs.mkdirSync(lock, { mode: 0o700 });
try {
  const stateFile = path.join(project, '.reversa/state.json');
  if (process.argv.includes('--restart')) {
    const names = ['.reversa', '_reversa_sdd', '_reversa_docs'];
    for (const name of names) {
      const origin = path.join(project, name);
      if (fs.existsSync(origin) && fs.lstatSync(origin).isSymbolicLink()) throw new Error('No se archivarán enlaces.');
    }
    const archive = path.join(project, '.reversa-history', new Date().toISOString().replace(/[:.]/g, '-'));
    fs.mkdirSync(archive, { recursive: true, mode: 0o700 });
    for (const name of names) {
      const origin = path.join(project, name);
      if (fs.existsSync(origin)) fs.renameSync(origin, path.join(archive, name));
    }
    console.log('Intento anterior conservado en ' + archive);
  }
  if (fs.existsSync(stateFile)) {
    const state = JSON.parse(fs.readFileSync(stateFile, 'utf8'));
    if (!state.engines?.includes('opencode') || !state.agents?.includes('reversa')) throw new Error('Inicialización manual incompleta. El administrador debe reinicializar conservando el intento anterior.');
    console.log('Estado existente conservado.');
  } else {
    const agents = fs.readdirSync(path.join(pkg, 'agents'), { withFileTypes: true }).filter(d => d.isDirectory() && fs.existsSync(path.join(pkg, 'agents', d.name, 'SKILL.md'))).map(d => d.name).sort();
    const writer = new Writer(project);
    for (const agent of agents) await writer.installSkill(agent, '.agents/skills');
    if (!fs.existsSync(path.join(project, 'AGENTS.md'))) await writer.installEntryFile({ entryFile: 'AGENTS.md', entryTemplate: 'AGENTS.md' }, { outputFolder: '_reversa_sdd', forwardFolder: '_reversa_forward' });
    writer.createReversaDir({ project_name: path.basename(project), user_name: 'Equipo', chat_language: 'es', doc_language: 'Español', answer_mode: 'chat', output_folder: '_reversa_sdd', forward_folder: '_reversa_forward', engines: ['opencode'], agents, git_strategy: 'commit' }, version);
    writer.saveCreatedFiles();
    saveManifest(project, buildManifest(project, writer.manifestPaths));
    console.log(`Proyecto preparado con Reversa ${version}: ${agents.length} habilidades.`);
  }
} finally { fs.rmdirSync(lock); }
