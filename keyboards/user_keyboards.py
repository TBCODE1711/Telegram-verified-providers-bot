from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_providers_keyboard(formatted_providers: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for display_name, callback_data in formatted_providers:
        builder.button(text=display_name, callback_data=callback_data)
        
    builder.button(text="חזרה", callback_data="/back_to_user_main")
    builder.adjust(1)
    return builder.as_markup()

def get_provider_actions_keyboard(provider_id: int, display_name: str, category: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.button(text="צור קשר", callback_data=f"talk_to_{provider_id}")
    builder.button(text="קרא ביקורות", callback_data=f"read_reviews_{provider_id}_{category}_{display_name}")
    builder.button(text="הוסף ביקורת", callback_data=f"add_review_{provider_id}_{category}_{display_name}")
    builder.button(text="חזרה", callback_data=category)
    builder.button(text="חזרה לתפריט הראשי", callback_data="/back_to_user_main")
    
    builder.adjust(1)
    return builder.as_markup()

def get_back_to_provider_actions_keyboard(
    provider_id: int,
    category: str,
    display_name: str,
    page: int = 0,
    total_pages: int = 1
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    nav_buttons = 0
    if page > 0:
        builder.button(text="➡️ הקודם", callback_data=f"reviews_page_{page - 1}")
        nav_buttons += 1
    if page < total_pages - 1:
        builder.button(text="הבא ⬅️", callback_data=f"reviews_page_{page + 1}")
        nav_buttons += 1

    builder.button(text="חזרה", callback_data=f"provider_{provider_id}_{category}_{display_name}")
    if nav_buttons > 0:
        builder.adjust(nav_buttons, 1)
    else:
        builder.adjust(1)
    return builder.as_markup()

def get_back_to_main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="חזרה לתפריט הראשי", callback_data="/back_to_user_main")
    builder.adjust(1)
    return builder.as_markup()

def get_category_selection_keyboard(categories_list: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for category in categories_list:
        builder.button(text=category, callback_data=category)
        
    builder.adjust(1)
    return builder.as_markup()
