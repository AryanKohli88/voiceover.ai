const { createClient } = require("@deepgram/sdk");
const fs = require("fs");
require("dotenv").config(); // Use a .env file to store your API key

const DEEPGRAM_API_KEY = process.env.API_KEY; //process.env.DEEPGRAM_API_KEY; // Store API key in .env file
const AUDIO_FILE_PATH = "../outputwav_002.wav"; // Path to your audio file


const transcribeFile = async () => {
  // STEP 1: Create a Deepgram client using the API key
  const deepgram = createClient(DEEPGRAM_API_KEY);

  // STEP 2: Call the transcribeFile method with the audio payload and options
  const { result, error } = await deepgram.listen.prerecorded.transcribeFile(
    // path to the audio file
    fs.readFileSync(AUDIO_FILE_PATH),
    // STEP 3: Configure Deepgram options for audio analysis
    {
      model: "nova-3",
      smart_format: true,
      diarize: true
    }
  );

  if (error) throw error;
  // STEP 4: Print the results
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
