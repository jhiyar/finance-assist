import { Router } from 'express';
import { readDatabase } from '../db.js';
import { detectIntent } from '../utils/intent.js';

const router = Router();

function formatMinorUnitsToCurrency(minorUnits) {
  const amount = (minorUnits || 0) / 100;
  return new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP' }).format(amount);
}

router.post('/', async (req, res) => {
  try {
    const { message } = req.body || {};
    if (!message || typeof message !== 'string') {
      return res.status(400).json({ error: 'Invalid message' });
    }

    const db = await readDatabase();
    const intent = detectIntent(message);

    if (intent === 'get_balance') {
      const humanBalance = formatMinorUnitsToCurrency(db.balance);
      return res.json({ type: 'text', text: `Your balance is ${humanBalance}.` });
    }

    if (intent === 'get_transactions') {
      const lastFive = (db.transactions || []).slice(-5).reverse();
      const lines = lastFive.map(t => `${t.date} — ${t.description}: ${formatMinorUnitsToCurrency(t.amountMinor)}`);
      return res.json({ type: 'text', text: `Here are your last ${lastFive.length} transactions:\n` + lines.join('\n') });
    }

    if (intent === 'update_profile') {
      return res.json({
        type: 'action',
        actionType: 'open_widget',
        widget: 'profile_update',
        title: 'Update your profile information',
        fields: ['name', 'address', 'email']
      });
    }

    // Default help
    return res.json({
      type: 'text',
      text: 'I can help with: checking your balance, showing recent transactions, and updating your address. Try: "What\'s my balance?", "Show my last transactions", or "I want to change my address".'
    });
  } catch (error) {
    console.error('Chat error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

export default router;

