import argparse
import asyncio
import getaudio
import getsubs
import translatesubs
import genVoices

async def main():
    parser = argparse.ArgumentParser(description="Video subtitle generator and translator")
    parser.add_argument("video_path", help="Path to the input video file")
    parser.add_argument("target_language", help="Target language for translation")
    args = parser.parse_args()

    audio_path = getaudio.extract_audio(args.video_path)
    subtitles = getsubs.generate_subtitles(audio_path)
    getsubs.write_srt(subtitles, "original_subtitles.srt")
    
    translated_subtitles = await translatesubs.translate_subtitles(subtitles, args.target_language)
    getsubs.write_srt(translated_subtitles, "translated_subtitles.srt")
    
    genVoices.generate_voice_overs(translated_subtitles, "translated_audio.wav")
    
    print("Process completed. Check the output files.")

if __name__ == "__main__":
    asyncio.run(main())
