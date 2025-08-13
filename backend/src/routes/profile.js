import { Router } from 'express';
import { readDatabase, writeDatabase } from '../db.js';

const router = Router();

router.get('/', async (req, res) => {
  try {
    const db = await readDatabase();
    return res.json(db.profile || {});
  } catch (error) {
    console.error('Profile GET error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
});

router.patch('/', async (req, res) => {
  try {
    const updates = req.body || {};
    const db = await readDatabase();
    const currentProfile = db.profile || {};
    const newProfile = { ...currentProfile, ...updates };
    const newDb = { ...db, profile: newProfile };
    await writeDatabase(newDb);
    return res.json(newProfile);
  } catch (error) {
    console.error('Profile PATCH error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
});

export default router;

