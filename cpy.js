// Call main.py and write the output to a variable
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const mainPyPath = path.join(__dirname, 'test.py');
const pythonExecutable = 'python'; // Change this to 'python' if you're on Windows
const outputFilePath = path.join(__dirname, 'output.txt');

function runPythonScript(
    pythonExecutable = 'python',
    mainPyPath = path.join(__dirname, 'test.py'),
    outputFilePath = path.join(__dirname, 'output.txt')
) {
    return new Promise((resolve, reject) => {
        const pythonProcess = spawn(pythonExecutable, [mainPyPath]);

        let output = '';
            let errorOutput = '';

        pythonProcess.stdout.on('data', (data) => {
            output += data.toString();
        });

        pythonProcess.stderr.on('data', (data) => {
            errorOutput += data.toString();
        });

        pythonProcess.on('close', (code) => {
            if (code !== 0) {
                reject(new Error(`Python script exited with code ${code}: ${errorOutput}`));
            } else {
                fs.writeFileSync(outputFilePath, output);
                resolve(output);
            }
        });
    });
}

async function main() {
    try {
        const output = await runPythonScript();
        console.log('Python script output:', output);
    } catch (error) {
        console.error('Error running Python script:', error.message);
    }
}

main();