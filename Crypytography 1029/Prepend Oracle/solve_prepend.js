const net = require('net');

const socket = net.createConnection({ host: '10.99.70.3', port: 40002 });
socket.setTimeout(15000);
socket.on('timeout', () => socket.destroy(new Error('Oracle timed out')));

let input = '';
function waitForData() {
  return new Promise((resolve, reject) => {
    const cleanup = () => {
      socket.off('data', onData);
      socket.off('error', onError);
      socket.off('end', onEnd);
    };
    const onData = (data) => { cleanup(); input += data.toString('utf8'); resolve(); };
    const onError = (error) => { cleanup(); reject(error); };
    const onEnd = () => { cleanup(); reject(new Error('Oracle closed connection')); };
    socket.once('data', onData);
    socket.once('error', onError);
    socket.once('end', onEnd);
  });
}

async function readUntil(marker) {
  while (!input.includes(marker)) await waitForData();
  const end = input.indexOf(marker) + marker.length;
  const result = input.slice(0, end - marker.length);
  input = input.slice(end);
  return result;
}

async function oracle(message) {
  socket.write(message.toString('hex') + '\n');
  await readUntil('cipher = ');
  const hex = (await readUntil('\n')).trim();
  await readUntil('message = ');
  return Buffer.from(hex, 'hex');
}

async function main() {
  await readUntil('message = ');
  const emptyCipher = await oracle(Buffer.alloc(0));
  const length = emptyCipher.length;
  console.log(`Ciphertext length: ${length} bytes`);

  if (process.argv.includes('--demo')) {
    const prefix = Buffer.alloc(length - 1, 0x41);
    const target = (await oracle(prefix)).subarray(0, length);
    const guessP = (await oracle(Buffer.concat([prefix, Buffer.from('P')]))).subarray(0, length);
    const guessX = (await oracle(Buffer.concat([prefix, Buffer.from('X')]))).subarray(0, length);
    console.log(`Empty cipher: ${emptyCipher.toString('hex')}`);
    console.log(`Target first ${length} bytes: ${target.toString('hex')}`);
    console.log(`Guess P first ${length} bytes: ${guessP.toString('hex')}`);
    console.log(`Guess X first ${length} bytes: ${guessX.toString('hex')}`);
    console.log(`P matches: ${guessP.equals(target)}; X matches: ${guessX.equals(target)}`);
    socket.end();
    return;
  }

  const preferred = Buffer.from('PH{}0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_!@#$%^&*()-=+[]:;,.?/ ');
  const guesses = [...new Set([0, ...preferred, ...Array.from({ length: 256 }, (_, i) => i)])];
  let recovered = Buffer.alloc(0);

  for (let position = length - 1; position >= 0; position--) {
    const prefix = Buffer.alloc(position, 0x41);
    const target = (await oracle(prefix)).subarray(0, length);
    let found = false;

    for (const guess of guesses) {
      const test = Buffer.concat([prefix, recovered, Buffer.from([guess])]);
      const result = (await oracle(test)).subarray(0, length);
      if (result.equals(target)) {
        recovered = Buffer.concat([recovered, Buffer.from([guess])]);
        console.log(`${recovered.length}/${length}: ${JSON.stringify(recovered.toString('utf8'))}`);
        found = true;
        break;
      }
    }
    if (!found) throw new Error(`No match for byte ${recovered.length}`);
  }

  console.log(`Recovered (hex): ${recovered.toString('hex')}`);
  console.log(`FLAG: ${recovered.toString('utf8').replace(/\0+$/, '').trimEnd()}`);
  socket.end();
}

main().catch((error) => { console.error(error); socket.destroy(); process.exitCode = 1; });
