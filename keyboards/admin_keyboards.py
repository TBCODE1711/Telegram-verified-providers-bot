from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_admin_main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.button(text="➕ הוספת נותן שירות", callback_data="add_provider_btn")
    builder.button(text="🔍 חיפוש / עריכת נותן שירות", callback_data="search_provider_btn")
    builder.button(text="📝 אישור ביקורות ממתינות", callback_data="manage_pending_reviews_btn")
    
    builder.adjust(1)
    
    return builder.as_markup()


def get_edit_provider_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.button(text="ערוך שם תצוגה", callback_data="edit_display_name")
    builder.button(text="ערוך קטגוריה", callback_data="edit_category")
    builder.button(text="שינוי סטטוס פעיל/לא פעיל", callback_data="toggle_status")
    builder.button(text="חזרה לחיפוש", callback_data="search_provider_btn")
    builder.button(text="חזרה לתפריט הראשי", callback_data="return_to_main_menu")
    builder.adjust(1)
    
    return builder.as_markup()

def get_toggle_confirmation_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.button(text="Confirm", callback_data="confirm_toggle_btn")
    builder.button(text="Cancel", callback_data="not_confirm_toggle_btn")
    builder.adjust(1)
    
    return builder.as_markup()

def get_review_approval_keyboard(review_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.button(text="✅ אשר", callback_data=f"confirm_review_{review_id}")
    builder.button(text="❌ דחה", callback_data=f"reject_review_{review_id}")
    builder.adjust(2)
    
    return builder.as_markup()

def get_category_selection_keyboard(categories_list: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for category in categories_list:
        builder.button(text=category, callback_data=f"admin_category_{category}")
        
    builder.button(text="Cancel", callback_data="cancel_action")
    builder.adjust(1)
    return builder.as_markup()
