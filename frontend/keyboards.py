from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def create_next_keyboard(user_id, next_index):
    """Create inline keyboard with Next button"""
    callback_data = f"next_{user_id}_{next_index}"
    
    keyboard = [[
        InlineKeyboardButton("Next ➡️", callback_data=callback_data)
    ]]
    
    return InlineKeyboardMarkup(keyboard)

def create_error_keyboard():
    """Create keyboard for error messages"""
    keyboard = [[
        InlineKeyboardButton("Try Again", callback_data="retry"),
        InlineKeyboardButton("New Search", callback_data="new_search")
    ]]
    
    return InlineKeyboardMarkup(keyboard)