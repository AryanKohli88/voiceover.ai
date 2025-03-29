# Goals
# Translation Context should be retained ->
# 1. Proverbs
# 2. which word to pause after
# 3. I have to be able to translate properly, mostly AI will be used here.

import asyncio
from googletrans import Translator

async def translate_text(translator, text, target_language):
    translation = await translator.translate(text, dest=target_language)
    return translation.text

async def translate_subtitle(translator, subtitle, target_language):
    start, end, speaker, text = subtitle
    translated_text = await translate_text(translator, text, target_language)
    return (start, end, speaker, translated_text)

async def translate_subtitles(subtitles, target_language):
    translator = Translator()
    tasks = [translate_subtitle(translator, subtitle, target_language) for subtitle in subtitles]
    translated_subtitles = await asyncio.gather(*tasks)
    return translated_subtitles

def translate_subtitles_sync(subtitles, target_language):
    return asyncio.run(translate_subtitles(subtitles, target_language))
