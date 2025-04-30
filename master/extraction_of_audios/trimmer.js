const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

function trim(fromFolder, toFolder, len) {
    if (!fs.existsSync(toFolder)) {
        fs.mkdirSync(toFolder, { recursive: true });
    }
    
    fs.readdir(fromFolder, (err, files) => {
        if (err) {
            console.error("Error reading fromFolder:", err);
            return;
        }
        
        files.forEach(file => {
            const inputPath = path.join(fromFolder, file);
            const outputBase = path.join(toFolder, path.parse(file).name);
            
            if (!fs.lstatSync(inputPath).isFile()) return;
            
            const command = `ffmpeg -i "${inputPath}" -f segment -segment_time ${len} -c:a pcm_s16le "${outputBase}_%03d.wav"`;
            
            exec(command, (error, stdout, stderr) => {
                if (error) {
                    console.error(`Error processing ${file}:`, error);
                    return;
                }
                console.log(`Trimmed: ${file}`);
            });
        });
    });
}

const FROM_FOLDER = "../audios";
const TO_FOLDER = "../audios/trimmed1";
const LENGTH = 100; // seconds

trim(FROM_FOLDER, TO_FOLDER, LENGTH);