const net = require('net');

const socket = net.createConnection({ host: '10.99.70.3', port: 40004 });
socket.setTimeout(20000);
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

let queries = 0;
async function oracle(iv, block) {
  const candidate = Buffer.concat([iv, block]);
  socket.write(candidate.toString('hex') + '\n');
  const result = await readUntil('\n');
  await readUntil('cipher = ');
  queries++;
  return result.includes('PADDING CORRECT!!!');
}

async function main() {
  await readUntil('flag = ');
  const original = Buffer.from((await readUntil('\n')).trim(), 'hex');
  await readUntil('cipher = ');
  if (original.length < 32 || original.length % 16 !== 0) {
    throw new Error('Invalid IV + ciphertext length');
  }

  const blocks = [];
  for (let i = 0; i < original.length; i += 16) {
    blocks.push(original.subarray(i, i + 16));
  }
  console.log(`Encrypted flag: ${original.toString('hex')}`);
  console.log(`Ciphertext blocks: ${blocks.length - 1}`);

  if (process.argv.includes('--demo')) {
    const previous = blocks[blocks.length - 2];
    const target = blocks[blocks.length - 1];
    for (const difference of [0, 1, 3]) {
      const craftedIV = Buffer.from(previous);
      craftedIV[15] ^= difference;
      const payload = Buffer.concat([craftedIV, target]);
      console.log(`cipher = ${payload.toString('hex')}`);
      console.log((await oracle(craftedIV, target)) ? 'PADDING CORRECT!!!' : 'PADDING ERROR!!!');
    }
    socket.end();
    return;
  }

  const preferred = Buffer.from('PH{}0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_!@#$%^&*()-=+[]:;,.?/ ');
  const guesses = [...new Set([...preferred, ...Array.from({ length: 16 }, (_, i) => i + 1), ...Array.from({ length: 256 }, (_, i) => i)])];
  const recoveredBlocks = [];

  for (let blockIndex = 1; blockIndex < blocks.length; blockIndex++) {
    const previous = blocks[blockIndex - 1];
    const target = blocks[blockIndex];
    const plaintext = Buffer.alloc(16);

    for (let index = 15; index >= 0; index--) {
      const padding = 16 - index;
      const craftedIV = Buffer.alloc(16);
      for (let j = index + 1; j < 16; j++) {
        craftedIV[j] = previous[j] ^ plaintext[j] ^ padding;
      }

      let found = false;
      for (const guess of guesses) {
        craftedIV[index] = previous[index] ^ guess ^ padding;
        if (!(await oracle(craftedIV, target))) continue;

        if (index === 15) {
          const check = Buffer.from(craftedIV);
          check[14] ^= 1;
          if (!(await oracle(check, target))) continue;
        }

        plaintext[index] = guess;
        found = true;
        console.log(`Block ${blockIndex}, byte ${index}: ${JSON.stringify(plaintext.toString('utf8'))} (${queries} queries)`);
        break;
      }
      if (!found) throw new Error(`No valid padding at block ${blockIndex}, byte ${index}`);
    }
    recoveredBlocks.push(plaintext);
  }

  const paddedFlag = Buffer.concat(recoveredBlocks);
  const padding = paddedFlag[paddedFlag.length - 1];
  if (padding < 1 || padding > 16 || !paddedFlag.subarray(-padding).every((byte) => byte === padding)) {
    throw new Error('Recovered bytes do not have valid PKCS#7 padding');
  }
  console.log(`Padded plaintext (hex): ${paddedFlag.toString('hex')}`);
  console.log(`FLAG: ${paddedFlag.subarray(0, -padding).toString('utf8')}`);
  console.log(`Total oracle queries: ${queries}`);
  socket.end();
}

main().catch((error) => { console.error(error); socket.destroy(); process.exitCode = 1; });
