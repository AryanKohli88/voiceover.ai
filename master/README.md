start with only one audio audio file in audios folder. 
audioTranslationfunctions folder needs only js and/or python files 
extraction_of_audios folder needs only js and/or python files

# Steps -
## extraction_of_audios
1. Use trimmer.js to trim audio file 
2. Use seperatevocals.js to get cleaner dialogues
3. put the newly generated vocals.wav file to audioTranslationfunctions/audio_to_translate path

## audioTranslationfunctions
4. get HF API key in audioTranslationfunctions/.env and run 
python .\seperatespeakers.py to seperate the 2 speakers.
5. get deepgram API key saved in audioTranslationfunctions/.env

```
pip install python-dotenv
pip install deepgram-sdk
```

5.  Run python .\generateSubs.py to generate subs
6. python .\translatesubs.py to translate subs
7. python .\genVoices.py to generate final voice
