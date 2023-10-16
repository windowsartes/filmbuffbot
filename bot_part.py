import asyncio
import pathlib
from os.path import join


from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.utils.exceptions import MessageTextIsEmpty


from api_part_sync import SearchEngine
from database_part import CinemabotDatabase
from keyboards import create_links_keyboard, additional_keyboard


current_dir = pathlib.Path(__file__).parent.resolve()
with open(join(current_dir, join("secrets", "telegram_token.txt")), 'r') as token_file:
    token = token_file.readline()

bot = Bot(token=token, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

cinemabot_database = CinemabotDatabase(join(current_dir, "cinemabot.db"))
search_engine = SearchEngine()


# помощь и старт
def create_help_template(user_name: str) -> str:
    return f"Привет, {user_name}, это Cinemabot! С моей помощью ты можешь:\n " + \
            "1. 📝 Написать название фильма/сериала/аниме, тогда я верну тебе его описание, " + \
            "оценку и постер, а также скажу, где его можно посмотреть.\n" + \
            "2. 📈 Написать /stats, тогда я покажу, что и сколько раз лично ты искал с моей помощью.\n" + \
            "3. 📖 Написать /history, тогда я верну твою историю поиска.\n" + \
            "4. 🌟 Написать /help, тогда я покажу это сообщение снова.\n" + \
            "Также у меня есть удобные inline кнопочки с командами ✨."


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message) -> None:
    """
    Send help information to the user
    :param message:
    :return:
    """
    await message.reply(create_help_template(message.from_user.full_name), reply_markup=additional_keyboard)


@dp.callback_query_handler(text='/help')
async def send_help(callback: types.CallbackQuery) -> None:
    await callback.message.reply(create_help_template(callback.from_user.full_name), reply_markup=additional_keyboard)
    await callback.answer()


# личная статистика
@dp.message_handler(commands=['stats'])
async def send_stats_handler(message: types.Message) -> None:
    """
    Send personal search stats to the user, associated with '/stats' command
    :param message:
    :return:
    """
    try:
        search_result = await cinemabot_database.get_personal_statistics(message.from_user.id)
        bot_answer = "А вот и твоя статистика поиска:\n"
        for row in search_result:
            bot_answer += f"{row[0]} | {row[1]}\n"
        await message.reply(bot_answer)
        await message.answer("Чем я ещё могу тебе помочь?", reply_markup=additional_keyboard)
    except MessageTextIsEmpty:
        await message.reply("Извини, твоя персональная история поиска пуста.")
        await message.answer("Чем я ещё могу тебе помочь?", reply_markup=additional_keyboard)


@dp.callback_query_handler(text='/stats')
async def send_stats(callback: types.CallbackQuery) -> None:
    """
    Send personal search stats to the user, associated with 'Моя статистика' inline button
    :param callback:
    :return:
    """
    try:
        search_result = await cinemabot_database.get_personal_statistics(callback.from_user.id)
        bot_answer = "А вот и твоя статистика поиска:\n"
        for row in search_result:
            bot_answer += f"{row[0]} | {row[1]}\n"
        await callback.message.reply(bot_answer)
        await callback.message.answer("Чем я ещё могу тебе помочь?", reply_markup=additional_keyboard)
        await callback.answer()
    except MessageTextIsEmpty:
        await callback.message.reply("Извини, твоя персональная история поиска пуста.")
        await callback.message.answer("Чем я ещё могу тебе помочь?", reply_markup=additional_keyboard)
        await callback.answer()


# история поиска
async def create_message_history(chat_id: str) -> str:
    """
    Creates a valid history message.
    :return: a history in a valid format
    """
    search_result = await cinemabot_database.get_last_records(chat_id)
    if not search_result:
        return "Твоя история поиска пока пуста."
    answer = "Твоя история поиска:\n"
    for row in search_result:
        answer += f"{row[0]}\n"
    return answer


@dp.message_handler(commands=['history'])
async def send_history(message: types.Message) -> None:
    """
    Return a personal search history to the user, associated with '/history' command
    :param message:
    :return:
    """
    await message.reply(await create_message_history(message.from_user.id))
    await message.answer("Чем я ещё могу тебе помочь?", reply_markup=additional_keyboard)


@dp.callback_query_handler(text='/history')
async def send_history_handler(callback: types.CallbackQuery) -> None:
    """
    Return a personal search history to the user, associated with 'История поиска' inline button
    :param callback:
    :return:
    """
    await callback.message.answer(await create_message_history(callback.from_user.id))
    await callback.message.answer("Чем я ещё могу тебе помочь?", reply_markup=additional_keyboard)
    await callback.answer()


# обработка запроса
@dp.message_handler()
async def process_movie(message: types.Message) -> None:
    """
    Send poster, rating and show's description to the user. In the case of failure, return a sorry message
    :param message:
    :return:
    """

    # async
    non_blocking_io = asyncio.to_thread(search_engine.get_information_by_query, message.text)
    search_result = await asyncio.gather(non_blocking_io)
    # gather зачем-то оборачивает выход в лист
    search_result = search_result[0]  # type: ignore

    # sync
    # search_result = search_engine.get_information_by_query(message.text)
    if isinstance(search_result, tuple):
        await message.reply(search_result[1])  # type: ignore
    else:
        # постер, рейтинг и описание
        try:  # type: ignore
            description = search_result['description'].replace('\xa0', ' ')
            await bot.send_photo(message.from_user.id, search_result['poster']['url'])
            await message.answer(f"Название: {search_result['name']}\n"
                                 f"Рейтинг на Кинопоиске {search_result['rating']['kp']}\n" +
                                 f"Рейтинг на IMDB {search_result['rating']['imdb']}\n" +
                                 f"{description}")

            # официальные ссылки
            watch_links = search_result['watchability']['items']
            if watch_links is None:
                await message.answer("Извини, официальных ссылок у меня для тебя нет, " +
                                     "но я попробую что-нибудь придумать 😉.")
            else:
                names = [link['name'] for link in watch_links]
                links = [link['url'] for link in watch_links]
                await message.answer("А вот и официальные ссылки на просмотр, но это ещё не всё 😉.",
                                     reply_markup=create_links_keyboard(names, links))

            # добавление в б/д
            await cinemabot_database.insert_value(message.from_user.id, search_result['name'])

            # осуждаемые ссылки

            name = "Осуждаемая ссылка 😡"
            link = f"https://www.kinopoisk.gg/{search_engine.get_last_type()}/{search_engine.get_last_id()}/"
            await message.answer("Бесплатная ссылка на месте 🚀", reply_markup=create_links_keyboard([name], [link]))
            # names, links = search_engine.get_pirated_links(search_result['name'])
            # if len(names) == 0:
            #     await message.answer("Извини, бесплатных ссылок я не нашёл 😿.")
            # else:
            #     await message.answer("А вот и бесплатные ссылки!", reply_markup=create_links_keyboard(names, links))

            # кнопочки со статистикой, историей и т.д.
            await message.answer("Чем я ещё могу тебе помочь?", reply_markup=additional_keyboard)

        except AttributeError:
            await message.reply("Извини, я ничего не нашёл 😿.")
            await message.answer("Чем я ещё могу тебе помочь?", reply_markup=additional_keyboard)

if __name__ == '__main__':
    # executor.start_polling(dp)
    executor.start_polling(dp, skip_updates=True)
