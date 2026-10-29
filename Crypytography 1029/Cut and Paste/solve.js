const net = require('net');

const host = '10.99.70.3';
const port = 40001;
const user = 'A'.repeat(11) + ';money:666667;BB';
const socket = net.createConnection({ host, port });

let output = '';
let sentUser = false;
let sentToken = false;

socket.setTimeout(10000);
socket.on('data', (data) => {
  output += data.toString('utf8');

  if (!sentUser && output.includes('user = ')) {
    socket.write(user + '\n');
    sentUser = true;
  }

  const token = output.match(/token = ([0-9a-f]+)/);
  if (!sentToken && token && output.includes('token = ', token.index + token[0].length)) {
    // Keep the first two AES blocks. The second is ";money:666667;BB".
    socket.write(token[1].slice(0, 64) + '\n');
    sentToken = true;
  }
});
socket.on('end', () => process.stdout.write(output));
socket.on('timeout', () => socket.destroy(new Error('Connection timed out')));
socket.on('error', (error) => {
  console.error(error.message);
  process.exitCode = 1;
});
