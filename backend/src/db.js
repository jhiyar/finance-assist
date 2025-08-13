import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const dataDirectory = path.resolve(__dirname, '../data');
const databaseFilePath = path.join(dataDirectory, 'db.json');

export async function readDatabase() {
  const rawContent = await fs.readFile(databaseFilePath, 'utf-8');
  return JSON.parse(rawContent);
}

export async function writeDatabase(databaseObject) {
  const content = JSON.stringify(databaseObject, null, 2);
  await fs.writeFile(databaseFilePath, content, 'utf-8');
}

export { databaseFilePath };

