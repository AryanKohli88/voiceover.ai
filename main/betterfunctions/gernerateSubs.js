const AUDIO_FILE_PATH = "../separated/htdemucs/outputwav_002/speaker1.wav"; 

const { createClient } = require("@deepgram/sdk");
const fs = require("fs");
require("dotenv").config();

// Helper function to convert seconds to SRT timestamp format
function secondsToSrtTime(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  const ms = Math.round((seconds - Math.floor(seconds)) * 1000);
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')},${String(ms).padStart(3, '0')}`;
}

const transcribeFile = async () => {
  const deepgram = createClient(process.env.API_KEY);
  
  const { result, error } = await deepgram.listen.prerecorded.transcribeFile(
    fs.readFileSync(AUDIO_FILE_PATH),
    {
      model: "nova-3",
      smart_format: true,
      diarize: true
    }
  );

  if (error) throw error;

  let srtContent = "";
  let counter = 1;
  
  const paragraphs = result.results.channels[0].alternatives[0].paragraphs.paragraphs;
  
  paragraphs.forEach(paragraph => {
    paragraph.sentences.forEach(sentence => {
      // Convert timestamps
      const startTime = secondsToSrtTime(sentence.start);
      const endTime = secondsToSrtTime(sentence.end);
      
      // Build SRT block
      srtContent += `${counter}\n`;
      srtContent += `${startTime} --> ${endTime}\n`;
      srtContent += `${sentence.text}\n\n`;
      
      counter++;
    });
  });

  fs.writeFileSync("speaker1.srt", srtContent);
  console.log("SRT file generated successfully!");
};

transcribeFile();
