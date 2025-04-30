const { exec } = require('child_process');
const path = require('path');

const file = '../audios/trimmed1/vlog_012'
const inputFile = path.resolve(`./${file}.wav`); // Ensure absolute path
const command = `demucs "${inputFile}"`;

exec(command, (error, stdout, stderr) => {
  if (error) {
    console.error(`Error running demucs: ${error.message}`);
    return;
  }

  if (stderr) {
    console.error(`stderr: ${stderr}`);
  }

  console.log(`stdout: ${stdout}`);
});
