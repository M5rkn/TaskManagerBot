from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from bot.keyboards import get_main_menu
from bot.states import TaskStates, EditTaskStates

router = Router()


@router.callback_query(F.data == "cancel")
@router.callback_query(F.data == "task_cancel")
async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    """Отмена текущей операции"""
    await state.clear()
    await callback.message.edit_text(
        "❌ <b>Операция отменена</b>",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(F.text.lower() == "отмена")
async def cancel_message_handler(message: Message, state: FSMContext):
    """Отмена текущей операции через сообщение"""
    await state.clear()
    await message.answer(
        "❌ <b>Операция отменена</b>",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )


@router.message(F.text.lower() == "пропустить")
async def skip_handler(message: Message, state: FSMContext):
    """Пропуск шага (обрабатывается в tasks.py)"""
    pass
