/* ============================================================
   PREDICTION API CONFIG
   Change API_BASE_URL to wherever your FastAPI server runs.
   Default matches `uvicorn main:app --reload` on your own machine.
   ============================================================ */

var API_BASE_URL = 'http://127.0.0.1:8000';
var PRESENT_SIZE_LIMIT_MB = 16;
var ENCRYPT_SIZE_LIMITS_MB = { 'AES-256': 25, 'ChaCha20': 15, 'PRESENT': 1 };

/* The model's encoder may return labels like "AES" or "PRESENT-80"
   depending on how it was trained. This maps whatever comes back
   to the option values used in the cipher <select>. */
function normalizeAlgoName(name) {
    if (!name) return null;
    var key = String(name).toLowerCase();
    if (key.indexOf('aes') !== -1) return 'AES-256';
    if (key.indexOf('chacha') !== -1) return 'ChaCha20';
    if (key.indexOf('present') !== -1) return 'PRESENT';
    return name;
}

/* ============================================================
   FILE / BYTE HELPERS
   ============================================================ */

var fileState = { file: null, bytes: null, sizeMb: 0, dataType: null, originalHashHex: null };
var cryptoState = { algorithm: null, result: null };

function detectDataType(name) {
    var ext = (name.split('.').pop() || '').toLowerCase();
    var map = {
        txt: 'Text', md: 'Text', log: 'Text',
        png: 'Image', jpg: 'Image', jpeg: 'Image', gif: 'Image', bmp: 'Image', webp: 'Image', svg: 'Image',
        mp4: 'Video', mov: 'Video', avi: 'Video', mkv: 'Video', webm: 'Video',
        mp3: 'Audio', wav: 'Audio', ogg: 'Audio', flac: 'Audio', aac: 'Audio', m4a: 'Audio',
        pdf: 'PDF', csv: 'CSV', json: 'JSON', xml: 'XML', doc: 'DOCX', docx: 'DOCX',
        zip: 'Archive', rar: 'Archive', '7z': 'Archive', tar: 'Archive', gz: 'Archive'
    };
    return map[ext] || 'Unknown';
}

function formatBytes(bytes) {
    if (bytes < 1024) return bytes + ' B';
    var units = ['KB', 'MB', 'GB'];
    var val = bytes, u = -1;
    do { val /= 1024; u++; } while (val >= 1024 && u < units.length - 1);
    return val.toFixed(val < 10 ? 2 : 1) + ' ' + units[u];
}

function bytesToHex(bytes, maxBytes) {
    var arr = maxBytes ? bytes.slice(0, maxBytes) : bytes;
    var out = '';
    for (var i = 0; i < arr.length; i++) out += arr[i].toString(16).padStart(2, '0');
    return out;
}

function bytesPreviewHex(bytes) {
    return bytesToHex(bytes, 24) + (bytes.length > 24 ? '\u2026' : '');
}

async function sha256Hex(buf) {
    var digest = await crypto.subtle.digest('SHA-256', buf);
    return bytesToHex(new Uint8Array(digest));
}

function downloadBytes(bytes, filename) {
    var blob = new Blob([bytes], { type: 'application/octet-stream' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(url); }, 2000);
}

function wait(ms) {
    return new Promise(function (resolve) { setTimeout(resolve, ms); });
}

/* ============================================================
   REAL ENCRYPTION IMPLEMENTATIONS
   Run entirely client-side. AES-256 uses the browser's native
   WebCrypto engine (AES-CTR). ChaCha20 and PRESENT-80 are plain,
   from-scratch JavaScript implementations of the published
   algorithms, since browsers do not expose them natively.
   ============================================================ */


async function encryptFile() {

    if (!fileState.file) {
        alert("Please upload a file first.");
        return;
    }

    var algorithm =
        document.getElementById("cipherChoice").value;

    if (!algorithm) {
        alert("Please select an algorithm.");
        return;
    }

    var encryptBtn =
        document.getElementById("encryptBtn");

    var cryptoStatus =
        document.getElementById("cryptoStatus");

    encryptBtn.disabled = true;
    encryptBtn.textContent = "Encrypting...";

    cryptoStatus.textContent =
        "Encrypting with " + algorithm + "...";

    try {

        var formData = new FormData();

        formData.append(
            "file",
            fileState.file,
            fileState.file.name
        );

        formData.append(
            "algorithm",
            algorithm
        );

        var response = await fetch(
            API_BASE_URL + "/encrypt",
            {
                method: "POST",
                body: formData
            }
        );

        if (!response.ok) {

            var errorData =
                await response.json().catch(
                    function () {
                        return null;
                    }
                );

            throw new Error(
                errorData && errorData.detail
                    ? errorData.detail
                    : "Encryption failed."
            );
        }

        var encryptedBlob =
            await response.blob();

        cryptoState.algorithm =
            algorithm;

        cryptoState.result =
            encryptedBlob;

        var downloadBtn =
            document.getElementById(
                "downloadEncryptedBtn"
            );

        if (downloadBtn) {
            downloadBtn.disabled = false;
        }

        var decryptBtn =
            document.getElementById(
                "decryptBtn"
            );

        if (decryptBtn) {
            decryptBtn.disabled = false;
        }

        cryptoStatus.textContent =
            "Encryption completed using " +
            algorithm +
            ".";

        console.log(
            "Encrypted using Python:",
            algorithm
        );

    } catch (error) {

        console.error(
            "Encryption error:",
            error
        );

        cryptoStatus.textContent =
            error.message ||
            "Encryption failed.";

    } finally {

        encryptBtn.disabled = false;
        encryptBtn.textContent = "Encrypt";
    }
}

async function decryptFile() {

    if (!cryptoState.result) {
        alert("Please encrypt the file first.");
        return;
    }

    if (!cryptoState.algorithm) {
        alert("No encryption algorithm selected.");
        return;
    }

    var decryptBtn =
        document.getElementById("decryptBtn");

    var cryptoStatus =
        document.getElementById("cryptoStatus");

    decryptBtn.disabled = true;
    decryptBtn.textContent = "Decrypting...";

    cryptoStatus.textContent =
        "Decrypting with " +
        cryptoState.algorithm +
        "...";

    try {

        var encryptedFile =
            new File(
                [cryptoState.result],
                fileState.file.name + ".enc",
                {
                    type: "application/octet-stream"
                }
            );

        var formData = new FormData();

        formData.append(
            "file",
            encryptedFile
        );

        formData.append(
            "algorithm",
            cryptoState.algorithm
        );

        var response = await fetch(
            API_BASE_URL + "/decrypt",
            {
                method: "POST",
                body: formData
            }
        );

        if (!response.ok) {

            var errorData =
                await response.json().catch(
                    function () {
                        return null;
                    }
                );

            throw new Error(
                errorData && errorData.detail
                    ? errorData.detail
                    : "Decryption failed."
            );
        }

        var decryptedBlob =
            await response.blob();

        cryptoState.decrypted =
            decryptedBlob;

        var downloadBtn =
            document.getElementById(
                "downloadDecryptedBtn"
            );

        if (downloadBtn) {
            downloadBtn.disabled = false;
        }

        cryptoStatus.textContent =
            "Decryption completed successfully.";

        console.log(
            "Decrypted using Python:",
            cryptoState.algorithm
        );

    } catch (error) {

        console.error(
            "Decryption error:",
            error
        );

        cryptoStatus.textContent =
            error.message ||
            "Decryption failed.";

    } finally {

        decryptBtn.disabled = false;
        decryptBtn.textContent = "Decrypt";
    }
}

function downloadDecryptedFile() {

    if (!cryptoState.decrypted) {
        alert("No decrypted file available.");
        return;
    }

    var url =
        URL.createObjectURL(
            cryptoState.decrypted
        );

    var a =
        document.createElement("a");

    a.href = url;

    a.download =
        fileState.file.name;

    document.body.appendChild(a);

    a.click();

    document.body.removeChild(a);

    URL.revokeObjectURL(url);
}
/* ============================================================
   PREDICT BUTTON — calls the real FastAPI /predict endpoint
   (called from the inline onclick in index.html)
   ============================================================ */

async function predictAlgorithm() {

    var dataType = document.getElementById('dataType').value;
    var fileSizeKb = parseFloat(document.getElementById('fileSize').value) || 0;
    var cpu = parseFloat(document.getElementById('cpu').value) || 0;
    var battery = parseFloat(document.getElementById('battery').value) || 0;

    var predictionEl = document.getElementById('prediction');
    var resultEl = document.getElementById('predictionResult');
    var reasonEl = document.getElementById('predictionReason');

    console.log("Sending to API:");
    console.log({
        file_type: dataType,
        file_size: fileSizeKb,
        cpu_usage: cpu,
        battery_level: battery
    });

    predictionEl.classList.remove('hidden');

    resultEl.textContent = '—';
    reasonEl.textContent = 'Contacting the ML model...';

    try {

        /* ==========================================
           SEND REQUEST TO FASTAPI
           ========================================== */

        var response = await fetch(
            'http://127.0.0.1:8000/predict',
            {
                method: 'POST',

                headers: {
                    'Content-Type': 'application/json'
                },

                body: JSON.stringify({
                    file_type: dataType,
                    file_size: fileSizeKb,
                    cpu_usage: cpu,
                    battery_level: battery
                })
            }
        );


        /* ==========================================
           HANDLE API ERROR
           ========================================== */

        if (!response.ok) {

            var errorData = await response.json().catch(function () {
                return null;
            });

            var errorMessage =
                errorData && errorData.detail
                    ? errorData.detail
                    : 'API error: ' + response.status;

            throw new Error(errorMessage);
        }


        /* ==========================================
           GET API RESPONSE
           ========================================== */

        var data = await response.json();

        console.log("FastAPI response:", data);


        /* ==========================================
           DISPLAY PREDICTION
           ========================================== */

        resultEl.textContent =
            data.recommended_algorithm;

        reasonEl.textContent =
            'Predicted by the trained ' +
            (data.model_used || 'ML') +
            ' model for a ' +
            dataType +
            ' file at ' +
            fileSizeKb +
            ' KB, ' +
            cpu +
            '% CPU and ' +
            battery +
            '% battery.';


        /* ==========================================
           UPDATE ENCRYPTION PANEL
           ========================================== */

        var cryptoPanel =
            document.getElementById('cryptoPanel');

        var cipherChoice =
            document.getElementById('cipherChoice');

        var decryptBtn =
            document.getElementById('decryptBtn');

        var cryptoStatus =
            document.getElementById('cryptoStatus');


        if (cryptoPanel && cipherChoice) {

            var normalized =
                normalizeAlgoName(
                    data.recommended_algorithm
                );

            console.log(
                "Returned algorithm:",
                data.recommended_algorithm
            );

            console.log(
                "Normalized algorithm:",
                normalized
            );


            /* Select predicted algorithm */

            var option = cipherChoice.querySelector(
                'option[value="' + normalized + '"]'
            );

            if (option) {
                cipherChoice.value = normalized;
            }


            /* PRESENT size limitation */

            var fileSizeMb =
                fileSizeKb / 1024;

            Array.prototype.forEach.call(
                cipherChoice.options,
                function (opt) {

                    if (opt.value === 'PRESENT') {

                        opt.disabled =
                            fileSizeMb >
                            PRESENT_SIZE_LIMIT_MB;
                    }
                }
            );


            cryptoPanel.classList.remove('hidden');

            if (cryptoStatus) {
                cryptoStatus.innerHTML = '';
            }

            if (decryptBtn) {
                decryptBtn.disabled = true;
            }

            cryptoState = {
                algorithm: null,
                result: null
            };
        }


    } catch (err) {

        console.error(
            'Prediction error:',
            err
        );

        resultEl.textContent = '—';

        reasonEl.textContent =
            err.message ||
            'Prediction failed.';

    }
}


window.predictAlgorithm = predictAlgorithm;

/* ============================================================
   FILE UPLOAD WIRING
   ============================================================ */

function wireFileUpload() {
    var fileUpload = document.getElementById('fileUpload');
    var uploadDrop = document.getElementById('uploadDrop');
    var uploadPromptText = document.getElementById('uploadPromptText');
    var fileInfo = document.getElementById('fileInfo');
    var fiName = document.getElementById('fiName');
    var fiType = document.getElementById('fiType');
    var fiSize = document.getElementById('fiSize');
    var dataTypeSelect = document.getElementById('dataType');
    var fileSizeInput = document.getElementById('fileSize');

    if (!fileUpload) return;

    async function handleFile(file) {
        fileState.file = file;
        var buf = await file.arrayBuffer();
        fileState.bytes = new Uint8Array(buf);
        fileState.sizeMb = file.size / (1024 * 1024);
        fileState.dataType = detectDataType(file.name);
        fileState.originalHashHex = await sha256Hex(buf);

        fiName.textContent = file.name;
        fiType.textContent = fileState.dataType;
        fiSize.textContent = formatBytes(file.size);
        fileInfo.style.display = 'block';
        uploadPromptText.textContent = 'Choose a different file, or drag it here';

        if (dataTypeSelect.querySelector('option[value="' + fileState.dataType + '"]')) {
            dataTypeSelect.value = fileState.dataType;
        } else {
            dataTypeSelect.value = 'Unknown';
        }
        fileSizeInput.value = Math.max(1, Math.round(file.size / 1024));

        document.getElementById('prediction').classList.add('hidden');
        var cryptoPanel = document.getElementById('cryptoPanel');
        if (cryptoPanel) cryptoPanel.classList.add('hidden');
        cryptoState = { algorithm: null, result: null };
    }

    fileUpload.addEventListener('change', function () {
        if (fileUpload.files && fileUpload.files[0]) handleFile(fileUpload.files[0]);
    });

    ['dragover', 'dragenter'].forEach(function (evt) {
        uploadDrop.addEventListener(evt, function (e) {
            e.preventDefault();
            uploadDrop.classList.add('drag-over');
        });
    });
    ['dragleave', 'drop'].forEach(function (evt) {
        uploadDrop.addEventListener(evt, function (e) {
            e.preventDefault();
            uploadDrop.classList.remove('drag-over');
        });
    });
    uploadDrop.addEventListener('drop', function (e) {
        if (e.dataTransfer.files && e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
    });
}

/* ============================================================
   ENCRYPT / DECRYPT WIRING
   ============================================================ */

function wireCrypto() {
    var cipherChoice = document.getElementById('cipherChoice');
    var encryptBtn = document.getElementById('encryptBtn');
    var decryptBtn = document.getElementById('decryptBtn');
    var cryptoStatus = document.getElementById('cryptoStatus');

    if (!encryptBtn) return;

    encryptBtn.addEventListener('click', async function () {
        if (!fileState.file || !fileState.bytes) {
            cryptoStatus.innerHTML = '<p class="crypto-note">Upload a real file above to enable encryption — the prediction works from typed-in values, but there is no real file data to encrypt yet.</p>';
            return;
        }

        var algo = cipherChoice.value;
        var limitMb = ENCRYPT_SIZE_LIMITS_MB[algo];
        if (fileState.sizeMb > limitMb) {
            cryptoStatus.innerHTML = '<p class="crypto-note">This file is larger than the ' + limitMb +
                ' MB in-browser demo limit for ' + algo + '. Live encryption is skipped here to keep the page responsive.</p>';
            return;
        }

        encryptBtn.disabled = true;
        cryptoStatus.innerHTML = '<p class="crypto-note">Encrypting with ' + algo + '\u2026</p>';
        await wait(30);

        var start = performance.now();
        var result;
        try {
            if (algo === 'AES-256') result = await aesEncryptBytes(fileState.bytes);
            else if (algo === 'ChaCha20') result = chachaEncryptBytes(fileState.bytes);
            else result = presentEncryptBytes(fileState.bytes);
        } catch (err) {
            cryptoStatus.innerHTML = '<p class="crypto-note">Encryption failed: ' + err.message + '</p>';
            encryptBtn.disabled = false;
            return;
        }
        var elapsed = (performance.now() - start).toFixed(1);
        cryptoState = { algorithm: algo, result: result };

        cryptoStatus.innerHTML =
            '<div class="crypto-result">' +
                '<div class="crypto-result-row"><span>Algorithm</span><b>' + algo + '</b></div>' +
                '<div class="crypto-result-row"><span>Time</span><b>' + elapsed + ' ms</b></div>' +
                '<div class="crypto-result-row"><span>Key (hex)</span><b>' + result.keyHex + '</b></div>' +
                '<div class="crypto-result-row"><span>Ciphertext size</span><b>' + formatBytes(result.ciphertext.length) + '</b></div>' +
                '<div class="byte-preview">Original:  ' + bytesPreviewHex(fileState.bytes) + '<br>Encrypted: ' + bytesPreviewHex(result.ciphertext) + '</div>' +
            '</div>' +
            '<div class="crypto-actions-row">' +
                '<button class="button secondary crypto-btn" id="downloadEncBtn" type="button">Download Encrypted File</button>' +
            '</div>' +
            '<p class="crypto-note">The key above lives only in this page\u2019s memory for this session — it is never stored or sent anywhere.</p>';

        document.getElementById('downloadEncBtn').addEventListener('click', function () {
            downloadBytes(result.ciphertext, fileState.file.name + '.enc');
        });

        decryptBtn.disabled = false;
        encryptBtn.disabled = false;
    });

    decryptBtn.addEventListener('click', async function () {
        if (!cryptoState.result) return;
        decryptBtn.disabled = true;
        var algo = cryptoState.algorithm;
        var result = cryptoState.result;

        var start = performance.now();
        var plain;
        try {
            if (algo === 'AES-256') plain = await aesDecryptBytes(result.ciphertext, result.keyObj, result.counter);
            else if (algo === 'ChaCha20') plain = chachaDecryptBytes(result.ciphertext, result.key, result.nonce);
            else plain = presentDecryptBytes(result.ciphertext, result.key80, result.nonceCounter);
        } catch (err) {
            cryptoStatus.innerHTML += '<p class="crypto-note">Decryption failed: ' + err.message + '</p>';
            decryptBtn.disabled = false;
            return;
        }
        var elapsed = (performance.now() - start).toFixed(1);
        var decryptedHash = await sha256Hex(plain.buffer);
        var matches = decryptedHash === fileState.originalHashHex;

        cryptoStatus.innerHTML +=
            '<div class="crypto-result">' +
                '<div class="crypto-result-row"><span>Decryption time</span><b>' + elapsed + ' ms</b></div>' +
                '<div class="verify-badge ' + (matches ? 'ok' : 'fail') + '">' +
                    (matches ? 'Verified \u2014 matches the original file exactly' : 'Mismatch \u2014 differs from the original') +
                '</div>' +
            '</div>' +
            '<div class="crypto-actions-row">' +
                '<button class="button secondary crypto-btn" id="downloadDecBtn" type="button">Download Decrypted File</button>' +
            '</div>';

        document.getElementById('downloadDecBtn').addEventListener('click', function () {
            downloadBytes(plain, fileState.file.name);
        });
    });
}

/* ============================================================
   NAVIGATION (fixed navbar + mobile menu + active link)
   ============================================================ */

document.addEventListener('DOMContentLoaded', function () {
    var navToggle = document.getElementById('navToggle');
    var navMobile = document.getElementById('navMobile');

    if (navToggle && navMobile) {
        navToggle.addEventListener('click', function () {
            var isOpen = navMobile.classList.toggle('open');
            navToggle.classList.toggle('open', isOpen);
            navToggle.setAttribute('aria-expanded', String(isOpen));
        });

        Array.prototype.forEach.call(navMobile.querySelectorAll('a'), function (link) {
            link.addEventListener('click', function () {
                navMobile.classList.remove('open');
                navToggle.classList.remove('open');
                navToggle.setAttribute('aria-expanded', 'false');
            });
        });
    }

    var navLinks = Array.prototype.slice.call(document.querySelectorAll('.nav-links a, .nav-mobile a'));
    var trackedIds = ['home', 'how-it-works', 'algorithms', 'results', 'demo'];
    var trackedSections = trackedIds
        .map(function (id) { return document.getElementById(id); })
        .filter(Boolean);

    function updateActiveLink() {
        var scrollPos = window.scrollY + 100;
        var current = trackedSections.length ? trackedSections[0].id : null;
        trackedSections.forEach(function (sec) {
            if (sec.offsetTop <= scrollPos) current = sec.id;
        });
        navLinks.forEach(function (link) {
            link.classList.toggle('active', link.getAttribute('href') === '#' + current);
        });
    }
    window.addEventListener('scroll', updateActiveLink, { passive: true });
    updateActiveLink();

    wireFileUpload();
    wireCrypto();
});