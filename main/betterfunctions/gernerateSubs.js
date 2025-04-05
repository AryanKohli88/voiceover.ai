const { createClient } = require("@deepgram/sdk");
const fs = require("fs");
require("dotenv").config();

const DEEPGRAM_API_KEY = process.env.API_KEY; 
const AUDIO_FILE_PATH = "../outputwav_002.wav"; 


const transcribeFile = async () => {
  const deepgram = createClient(DEEPGRAM_API_KEY);
  const { result, error } = await deepgram.listen.prerecorded.transcribeFile(
    fs.readFileSync(AUDIO_FILE_PATH),
    {
      model: "nova-3",
      smart_format: true,
      diarize: true
    }
  );

  if (error) throw error;
  if (!error) {
    let op = "Para 1 - \n";
    console.dir(result, { depth: null });

    let output = result.results.channels[0].alternatives[0].paragraphs.paragraphs;
    if (!output || !Array.isArray(output)) {
        throw new Error("No paragraphs found.");
      }
    let i = 1;
    output.forEach(paragraph => {
        i++;
        op += paragraph.sentences.map(sentence => sentence.text).join(" ") + "\n\nPara " + i + " - \n";
    });
    fs.writeFileSync("transcript.txt", op)
    }
};

transcribeFile();
