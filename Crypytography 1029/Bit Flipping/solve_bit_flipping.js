const net = require('net');

const host = '10.99.70.3';
const port = 40003;
const original = Buffer.from('AAAAAAAAA');
const goal = Buffer.from('CTFGOGOGO');

const socket = net.createConnection({ host, port });
socket.setTimeout(10000);
let input = '';
let sent = false;

socket.on('data', (chunk) => {
  input += chunk.toString('utf8');

  if (!sent && input.includes('\n')) {
    const lineEnd = input.indexOf('\n');
    const received = input.slice(0, lineEnd).trim();
    const ciphertext = Buffer.from(received, 'base64');
    for (let i = 0; i < goal.length; i++) {
      ciphertext[i] ^= original[i] ^ goal[i];
    }
    const submitted = ciphertext.toString('base64');
    if (process.argv.includes('--demo')) {
      console.log(`Server Base64: ${received}`);
      console.log(`Submitted Base64: ${submitted}`);
    }
    socket.write(submitted + '\n');
    input = input.slice(lineEnd + 1);
    sent = true;
  }
});

socket.on('end', () => process.stdout.write(input));
socket.on('timeout', () => socket.destroy(new Error('Connection timed out')));
socket.on('error', (error) => {
  console.error(error.message);
  process.exitCode = 1;
});
