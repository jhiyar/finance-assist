def detect_intent(user_message):
    """Detect user intent from message text."""
    if not user_message:
        return ''
    
    text = user_message.lower()
    
    # Balance queries
    if any(word in text for word in ['balance', 'money', 'funds', 'account balance']):
        return 'get_balance'
    
    # Transaction queries
    if any(word in text for word in ['transactions', 'history', 'payments', 'spending', 'expenses', 'deposits', 'withdrawals']):
        return 'get_transactions'
    
    # Profile update queries
    if any(word in text for word in ['change', 'update', 'modify']) and any(word in text for word in ['address', 'profile', 'name', 'email']):
        return 'update_profile'
    
    # Help queries
    if any(word in text for word in ['help', 'assist', 'support', 'how to']):
        return 'help'
    
    return ''


def format_minor_units_to_currency(minor_units):
    """Convert minor units (pennies) to formatted currency string."""
    amount = (minor_units or 0) / 100
    return f"£{amount:,.2f}"
