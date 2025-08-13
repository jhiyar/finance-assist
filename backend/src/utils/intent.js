export function detectIntent(userMessage) {
  const text = (userMessage || '').toLowerCase();

  if (text.includes('balance')) {
    return 'get_balance';
  }

  if (text.includes('transactions') || text.includes('history')) {
    return 'get_transactions';
  }

  if (text.includes('change') && text.includes('address')) {
    return 'update_profile';
  }

  return 'help';
}

