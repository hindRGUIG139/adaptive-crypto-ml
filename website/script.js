/* ============================================================
   FASTAPI CONFIGURATION
   ============================================================ */

var API_BASE_URL = 'http://127.0.0.1:8000';

var PRESENT_SIZE_LIMIT_MB = 16;

var ENCRYPT_SIZE_LIMITS_MB = {
    'AES-256': 25,
    'ChaCha20': 15,
    'PRESENT': 1
};

const themeToggle = document.getElementById("theme-toggle");
const themeIcon = document.getElementById("theme-icon");

const savedTheme = localStorage.getItem("theme");

if (savedTheme) {
    document.documentElement.setAttribute("data-theme", savedTheme);
}

function updateThemeIcon() {
    const currentTheme =
        document.documentElement.getAttribute("data-theme");

    if (currentTheme === "light") {
        themeIcon.textContent = "🌙";
    } else {
        themeIcon.textContent = "☀";
    }
}

updateThemeIcon();

themeToggle.addEventListener("click", () => {

    const currentTheme =
        document.documentElement.getAttribute("data-theme");

    const newTheme =
        currentTheme === "light" ? "dark" : "light";

    document.documentElement.setAttribute(
        "data-theme",
        newTheme
    );

    localStorage.setItem("theme", newTheme);

    updateThemeIcon();
});
/* ============================================================
   ALGORITHM NAME NORMALIZATION
   ============================================================

   The ML model may return:
       AES
       AES-256
       ChaCha20
       PRESENT
       PRESENT-80

   The HTML select uses:
       AES-256
       ChaCha20
       PRESENT

   This function converts the model's result to the HTML value.
   ============================================================ */

function normalizeAlgoName(name) {

    if (!name) {
        return null;
    }

    var key = String(name).toLowerCase();

    if (key.indexOf('aes') !== -1) {
        return 'AES-256';
    }

    if (key.indexOf('chacha') !== -1) {
        return 'ChaCha20';
    }

    if (key.indexOf('present') !== -1) {
        return 'PRESENT';
    }

    return name;
}


/* ============================================================
   FILE STATE
   ============================================================ */

var fileState = {
    file: null,
    bytes: null,
    sizeMb: 0,
    dataType: null,
    originalHashHex: null
};


/* ============================================================
   CRYPTO STATE
   ============================================================ */

var cryptoState = {
    algorithm: null,
    result: null,
    decrypted: null
};


/* ============================================================
   DATA TYPE DETECTION
   ============================================================ */

function detectDataType(name) {

    var ext = (
        name.split('.').pop() || ''
    ).toLowerCase();

    var map = {

        txt: 'Text',
        md: 'Text',
        log: 'Text',

        png: 'Image',
        jpg: 'Image',
        jpeg: 'Image',
        gif: 'Image',
        bmp: 'Image',
        webp: 'Image',
        svg: 'Image',

        mp4: 'Video',
        mov: 'Video',
        avi: 'Video',
        mkv: 'Video',
        webm: 'Video',

        mp3: 'Audio',
        wav: 'Audio',
        ogg: 'Audio',
        flac: 'Audio',
        aac: 'Audio',
        m4a: 'Audio',

        pdf: 'PDF',

        csv: 'CSV',

        json: 'JSON',

        xml: 'XML',

        doc: 'DOCX',
        docx: 'DOCX',

        zip: 'Archive',
        rar: 'Archive',
        '7z': 'Archive',
        tar: 'Archive',
        gz: 'Archive'
    };

    return map[ext] || 'Unknown';
}


/* ============================================================
   FORMAT BYTES
   ============================================================ */

function formatBytes(bytes) {

    if (bytes < 1024) {
        return bytes + ' B';
    }

    var units = ['KB', 'MB', 'GB'];

    var val = bytes;
    var u = -1;

    do {
        val /= 1024;
        u++;
    }
    while (
        val >= 1024 &&
        u < units.length - 1
    );

    return val.toFixed(
        val < 10 ? 2 : 1
    ) + ' ' + units[u];
}


/* ============================================================
   BYTES → HEX
   ============================================================ */

function bytesToHex(bytes, maxBytes) {

    var arr = maxBytes
        ? bytes.slice(0, maxBytes)
        : bytes;

    var out = '';

    for (
        var i = 0;
        i < arr.length;
        i++
    ) {

        out += arr[i]
            .toString(16)
            .padStart(2, '0');
    }

    return out;
}


/* ============================================================
   BYTE PREVIEW
   ============================================================ */

function bytesPreviewHex(bytes) {

    return bytesToHex(
        bytes,
        24
    ) + (
        bytes.length > 24
            ? '\u2026'
            : ''
    );
}


/* ============================================================
   SHA-256
   ============================================================

   This is NOT used for encryption.
   It is only used to verify that the decrypted file is exactly
   the same as the original file.
   ============================================================ */

async function sha256Hex(buf) {

    var digest =
        await crypto.subtle.digest(
            'SHA-256',
            buf
        );

    return bytesToHex(
        new Uint8Array(digest)
    );
}


/* ============================================================
   DOWNLOAD BLOB
   ============================================================ */

function downloadBlob(blob, filename) {

    var url =
        URL.createObjectURL(blob);

    var a =
        document.createElement('a');

    a.href = url;

    a.download = filename;

    document.body.appendChild(a);

    a.click();

    document.body.removeChild(a);

    setTimeout(
        function () {
            URL.revokeObjectURL(url);
        },
        2000
    );
}


/* ============================================================
   WAIT HELPER
   ============================================================ */

function wait(ms) {

    return new Promise(
        function (resolve) {
            setTimeout(resolve, ms);
        }
    );
}


/* ============================================================
   PREDICTION
   ============================================================

   Calls:
       POST /predict

   The actual ML prediction is performed by FastAPI/Python.
   ============================================================ */

async function predictAlgorithm() {

    var dataType =
        document.getElementById(
            'dataType'
        ).value;

    var fileSizeKb =
        parseFloat(
            document.getElementById(
                'fileSize'
            ).value
        ) || 0;

    var cpu =
        parseFloat(
            document.getElementById(
                'cpu'
            ).value
        ) || 0;

    var battery =
        parseFloat(
            document.getElementById(
                'battery'
            ).value
        ) || 0;


    var predictionEl =
        document.getElementById(
            'prediction'
        );

    var resultEl =
        document.getElementById(
            'predictionResult'
        );

    var reasonEl =
        document.getElementById(
            'predictionReason'
        );


    console.log(
        'Sending prediction request:'
    );

    console.log({
        file_type: dataType,
        file_size: fileSizeKb,
        cpu_usage: cpu,
        battery_level: battery
    });


    predictionEl.classList.remove(
        'hidden'
    );

    resultEl.textContent = '—';

    reasonEl.textContent =
        'Contacting the ML model...';


    try {

        var response =
            await fetch(
                API_BASE_URL + '/predict',
                {
                    method: 'POST',

                    headers: {
                        'Content-Type':
                            'application/json'
                    },

                    body: JSON.stringify({

                        file_type:
                            dataType,

                        file_size:
                            fileSizeKb,

                        cpu_usage:
                            cpu,

                        battery_level:
                            battery
                    })
                }
            );


        /* ----------------------------------------------------
           API ERROR
           ---------------------------------------------------- */

        if (!response.ok) {

            var errorData =
                await response.json()
                    .catch(
                        function () {
                            return null;
                        }
                    );


            var errorMessage =
                errorData &&
                errorData.detail

                    ? errorData.detail

                    : 'API error: ' +
                      response.status;


            throw new Error(
                errorMessage
            );
        }


        /* ----------------------------------------------------
           GET PREDICTION
           ---------------------------------------------------- */

        var data =
            await response.json();


        console.log(
            'FastAPI prediction:',
            data
        );


        /* ----------------------------------------------------
           DISPLAY PREDICTION
           ---------------------------------------------------- */

        resultEl.textContent =
            data.recommended_algorithm;


        reasonEl.textContent =
            'Predicted by the trained ' +
            (
                data.model_used ||
                'ML'
            ) +
            ' model for a ' +
            dataType +
            ' file at ' +
            fileSizeKb +
            ' KB, ' +
            cpu +
            '% CPU and ' +
            battery +
            '% battery.';


        /* ----------------------------------------------------
           ENCRYPTION PANEL
           ---------------------------------------------------- */

        var cryptoPanel =
            document.getElementById(
                'cryptoPanel'
            );

        var cipherChoice =
            document.getElementById(
                'cipherChoice'
            );

        var decryptBtn =
            document.getElementById(
                'decryptBtn'
            );

        var cryptoStatus =
            document.getElementById(
                'cryptoStatus'
            );


        if (
            cryptoPanel &&
            cipherChoice
        ) {

            var normalized =
                normalizeAlgoName(
                    data.recommended_algorithm
                );


            console.log(
                'Returned algorithm:',
                data.recommended_algorithm
            );

            console.log(
                'Normalized algorithm:',
                normalized
            );


            /* ------------------------------------------------
               SELECT PREDICTED ALGORITHM
               ------------------------------------------------ */

            var option =
                cipherChoice.querySelector(
                    'option[value="' +
                    normalized +
                    '"]'
                );


            if (option) {

                cipherChoice.value =
                    normalized;
            }


            /* ------------------------------------------------
               PRESENT SIZE LIMIT
               ------------------------------------------------ */

            var fileSizeMb =
                fileSizeKb / 1024;


            Array.prototype.forEach.call(
                cipherChoice.options,
                function (opt) {

                    if (
                        opt.value ===
                        'PRESENT'
                    ) {

                        opt.disabled =
                            fileSizeMb >
                            PRESENT_SIZE_LIMIT_MB;
                    }
                }
            );


            cryptoPanel.classList.remove(
                'hidden'
            );


            if (cryptoStatus) {

                cryptoStatus.innerHTML =
                    '<p class="crypto-note">' +
                    'Algorithm selected by ML: ' +
                    '<b>' +
                    normalized +
                    '</b>' +
                    '</p>';
            }


            /* ------------------------------------------------
               RESET CRYPTO STATE
               ------------------------------------------------ */

            cryptoState = {
                algorithm: null,
                result: null,
                decrypted: null
            };


            if (decryptBtn) {

                decryptBtn.disabled =
                    true;
            }
        }


    }
    catch (err) {

        console.error(
            'Prediction error:',
            err
        );


        resultEl.textContent =
            '—';


        reasonEl.textContent =
            err.message ||
            'Prediction failed.';
    }
}


window.predictAlgorithm =
    predictAlgorithm;


/* ============================================================
   FILE UPLOAD
   ============================================================ */

function wireFileUpload() {

    var fileUpload =
        document.getElementById(
            'fileUpload'
        );

    var uploadDrop =
        document.getElementById(
            'uploadDrop'
        );

    var uploadPromptText =
        document.getElementById(
            'uploadPromptText'
        );

    var fileInfo =
        document.getElementById(
            'fileInfo'
        );

    var fiName =
        document.getElementById(
            'fiName'
        );

    var fiType =
        document.getElementById(
            'fiType'
        );

    var fiSize =
        document.getElementById(
            'fiSize'
        );

    var dataTypeSelect =
        document.getElementById(
            'dataType'
        );

    var fileSizeInput =
        document.getElementById(
            'fileSize'
        );


    if (!fileUpload) {
        return;
    }


    /* ========================================================
       HANDLE FILE
       ======================================================== */

    async function handleFile(file) {

        fileState.file =
            file;


        var buf =
            await file.arrayBuffer();


        fileState.bytes =
            new Uint8Array(buf);


        fileState.sizeMb =
            file.size /
            (1024 * 1024);


        fileState.dataType =
            detectDataType(
                file.name
            );


        fileState.originalHashHex =
            await sha256Hex(buf);


        /* ----------------------------------------------------
           DISPLAY FILE INFORMATION
           ---------------------------------------------------- */

        fiName.textContent =
            file.name;

        fiType.textContent =
            fileState.dataType;

        fiSize.textContent =
            formatBytes(
                file.size
            );


        fileInfo.style.display =
            'block';


        uploadPromptText.textContent =
            'Choose a different file, or drag it here';


        /* ----------------------------------------------------
           SET DATA TYPE
           ---------------------------------------------------- */

        if (
            dataTypeSelect.querySelector(
                'option[value="' +
                fileState.dataType +
                '"]'
            )
        ) {

            dataTypeSelect.value =
                fileState.dataType;

        }
        else {

            dataTypeSelect.value =
                'Unknown';
        }


        /* ----------------------------------------------------
           SET FILE SIZE
           ---------------------------------------------------- */

        fileSizeInput.value =
            Math.max(
                1,
                Math.round(
                    file.size / 1024
                )
            );


        /* ----------------------------------------------------
           RESET PREDICTION
           ---------------------------------------------------- */

        document
            .getElementById(
                'prediction'
            )
            .classList.add(
                'hidden'
            );


        /* ----------------------------------------------------
           RESET CRYPTO PANEL
           ---------------------------------------------------- */

        var cryptoPanel =
            document.getElementById(
                'cryptoPanel'
            );


        if (cryptoPanel) {

            cryptoPanel.classList.add(
                'hidden'
            );
        }


        cryptoState = {
            algorithm: null,
            result: null,
            decrypted: null
        };


        console.log(
            'File loaded:',
            file.name
        );

        console.log(
            'Data type:',
            fileState.dataType
        );

        console.log(
            'Size:',
            formatBytes(file.size)
        );
    }


    /* ========================================================
       NORMAL FILE SELECTION
       ======================================================== */

    fileUpload.addEventListener(
        'change',
        function () {

            if (
                fileUpload.files &&
                fileUpload.files[0]
            ) {

                handleFile(
                    fileUpload.files[0]
                );
            }
        }
    );


    /* ========================================================
       DRAG OVER
       ======================================================== */

    [
        'dragover',
        'dragenter'
    ].forEach(
        function (evt) {

            uploadDrop.addEventListener(
                evt,
                function (e) {

                    e.preventDefault();

                    uploadDrop.classList.add(
                        'drag-over'
                    );
                }
            );
        }
    );


    /* ========================================================
       DRAG LEAVE / DROP
       ======================================================== */

    [
        'dragleave',
        'drop'
    ].forEach(
        function (evt) {

            uploadDrop.addEventListener(
                evt,
                function (e) {

                    e.preventDefault();

                    uploadDrop.classList.remove(
                        'drag-over'
                    );
                }
            );
        }
    );


    /* ========================================================
       DROP FILE
       ======================================================== */

    uploadDrop.addEventListener(
        'drop',
        function (e) {

            if (
                e.dataTransfer.files &&
                e.dataTransfer.files[0]
            ) {

                handleFile(
                    e.dataTransfer.files[0]
                );
            }
        }
    );
}


/* ============================================================
   ENCRYPT / DECRYPT
   ============================================================

   IMPORTANT:

   There is NO AES implementation here.
   There is NO ChaCha20 implementation here.
   There is NO PRESENT implementation here.

   The browser sends the file to FastAPI.

   FastAPI calls:

       aes.encrypt_file()
       chacha20.encrypt_file()
       present.encrypt_file()

   Therefore the actual encryption is performed by YOUR
   Python/C implementations.
   ============================================================ */

function wireCrypto() {

    var cipherChoice =
        document.getElementById(
            'cipherChoice'
        );

    var encryptBtn =
        document.getElementById(
            'encryptBtn'
        );

    var decryptBtn =
        document.getElementById(
            'decryptBtn'
        );

    var cryptoStatus =
        document.getElementById(
            'cryptoStatus'
        );


    if (!encryptBtn) {
        return;
    }


    /* ========================================================
       ENCRYPT BUTTON
       ======================================================== */

    encryptBtn.addEventListener(
        'click',
        async function () {

            /* ------------------------------------------------
               CHECK FILE
               ------------------------------------------------ */

            if (!fileState.file) {

                cryptoStatus.innerHTML =
                    '<p class="crypto-note">' +
                    'Please upload a file first.' +
                    '</p>';

                return;
            }


            /* ------------------------------------------------
               GET ALGORITHM
               ------------------------------------------------ */

            var algo =
                cipherChoice.value;


            if (!algo) {

                cryptoStatus.innerHTML =
                    '<p class="crypto-note">' +
                    'Please select an algorithm.' +
                    '</p>';

                return;
            }


            /* ------------------------------------------------
               SIZE CHECK
               ------------------------------------------------ */

            var limitMb =
                ENCRYPT_SIZE_LIMITS_MB[
                    algo
                ];


            if (
                limitMb &&
                fileState.sizeMb >
                limitMb
            ) {

                cryptoStatus.innerHTML =
                    '<p class="crypto-note">' +
                    'This file is larger than the ' +
                    limitMb +
                    ' MB demo limit for ' +
                    algo +
                    '.</p>';

                return;
            }


            /* ------------------------------------------------
               DISABLE BUTTON
               ------------------------------------------------ */

            encryptBtn.disabled =
                true;

            decryptBtn.disabled =
                true;


            cryptoStatus.innerHTML =
                '<p class="crypto-note">' +
                'Encrypting with ' +
                algo +
                ' using the Python backend\u2026' +
                '</p>';


            await wait(30);


            var start =
                performance.now();


            try {

                /* --------------------------------------------
                   CREATE FORM DATA
                   -------------------------------------------- */

                var formData =
                    new FormData();


                formData.append(
                    'file',
                    fileState.file,
                    fileState.file.name
                );


                formData.append(
                    'algorithm',
                    algo
                );


                /* --------------------------------------------
                   SEND TO FASTAPI
                   -------------------------------------------- */

                var response =
                    await fetch(
                        API_BASE_URL +
                        '/encrypt',
                        {
                            method: 'POST',

                            body:
                                formData
                        }
                    );


                /* --------------------------------------------
                   HANDLE ERROR
                   -------------------------------------------- */

                if (!response.ok) {

                    var errorData =
                        await response.json()
                            .catch(
                                function () {
                                    return null;
                                }
                            );


                    throw new Error(
                        errorData &&
                        errorData.detail

                            ? errorData.detail

                            : 'Encryption failed. HTTP ' +
                              response.status
                    );
                }


                /* --------------------------------------------
                   RECEIVE ENCRYPTED FILE
                   -------------------------------------------- */

                var encryptedBlob =
                    await response.blob();


                var elapsed =
                    (
                        performance.now() -
                        start
                    ).toFixed(1);


                /* --------------------------------------------
                   SAVE STATE
                   -------------------------------------------- */

                cryptoState.algorithm =
                    algo;

                cryptoState.result =
                    encryptedBlob;

                cryptoState.decrypted =
                    null;


                /* --------------------------------------------
                   DISPLAY RESULT
                   -------------------------------------------- */

                cryptoStatus.innerHTML =

                    '<div class="crypto-result">' +

                        '<div class="crypto-result-row">' +
                            '<span>Algorithm</span>' +
                            '<b>' +
                                algo +
                            '</b>' +
                        '</div>' +

                        '<div class="crypto-result-row">' +
                            '<span>Time</span>' +
                            '<b>' +
                                elapsed +
                                ' ms' +
                            '</b>' +
                        '</div>' +

                        '<div class="crypto-result-row">' +
                            '<span>Encryption</span>' +
                            '<b>Python backend</b>' +
                        '</div>' +

                        '<div class="crypto-result-row">' +
                            '<span>Encrypted size</span>' +
                            '<b>' +
                                formatBytes(
                                    encryptedBlob.size
                                ) +
                            '</b>' +
                        '</div>' +

                    '</div>' +

                    '<div class="crypto-actions-row">' +

                        '<button ' +
                            'class="button secondary crypto-btn" ' +
                            'id="downloadEncBtn" ' +
                            'type="button">' +
                            'Download Encrypted File' +
                        '</button>' +

                    '</div>' +

                    '<p class="crypto-note">' +
                        'The file was encrypted by your Python ' +
                        algo +
                        ' implementation.' +
                    '</p>';


                /* --------------------------------------------
                   DOWNLOAD BUTTON
                   -------------------------------------------- */

                document
                    .getElementById(
                        'downloadEncBtn'
                    )
                    .addEventListener(
                        'click',
                        function () {

                            downloadBlob(
                                encryptedBlob,
                                fileState.file.name +
                                '.enc'
                            );
                        }
                    );


                /* --------------------------------------------
                   ENABLE DECRYPT
                   -------------------------------------------- */

                decryptBtn.disabled =
                    false;


                console.log(
                    'Encryption successful.'
                );

                console.log(
                    'Algorithm:',
                    algo
                );

                console.log(
                    'Python backend:',
                    true
                );


            }
            catch (err) {

                console.error(
                    'Encryption error:',
                    err
                );


                cryptoStatus.innerHTML =
                    '<p class="crypto-note">' +
                    'Encryption failed: ' +
                    err.message +
                    '</p>';
            }


            finally {

                encryptBtn.disabled =
                    false;
            }
        }
    );


    /* ========================================================
       DECRYPT BUTTON
       ======================================================== */

    decryptBtn.addEventListener(
        'click',
        async function () {

            /* ------------------------------------------------
               CHECK ENCRYPTED FILE
               ------------------------------------------------ */

            if (
                !cryptoState.result
            ) {

                cryptoStatus.innerHTML +=
                    '<p class="crypto-note">' +
                    'Please encrypt the file first.' +
                    '</p>';

                return;
            }


            /* ------------------------------------------------
               CHECK ALGORITHM
               ------------------------------------------------ */

            if (
                !cryptoState.algorithm
            ) {

                cryptoStatus.innerHTML +=
                    '<p class="crypto-note">' +
                    'No algorithm selected.' +
                    '</p>';

                return;
            }


            var algo =
                cryptoState.algorithm;


            decryptBtn.disabled =
                true;

            encryptBtn.disabled =
                true;


            cryptoStatus.innerHTML +=
                '<p class="crypto-note">' +
                'Decrypting with ' +
                algo +
                ' using the Python backend\u2026' +
                '</p>';


            await wait(30);


            var start =
                performance.now();


            try {

                /* --------------------------------------------
                   CREATE FILE FROM ENCRYPTED BLOB
                   -------------------------------------------- */

                var encryptedFile =
                    new File(
                        [
                            cryptoState.result
                        ],

                        fileState.file.name +
                        '.enc',

                        {
                            type:
                                'application/octet-stream'
                        }
                    );


                /* --------------------------------------------
                   CREATE FORM DATA
                   -------------------------------------------- */

                var formData =
                    new FormData();


                formData.append(
                    'file',
                    encryptedFile,
                    encryptedFile.name
                );


                formData.append(
                    'algorithm',
                    algo
                );


                /* --------------------------------------------
                   SEND TO FASTAPI
                   -------------------------------------------- */

                var response =
                    await fetch(
                        API_BASE_URL +
                        '/decrypt',
                        {
                            method: 'POST',

                            body:
                                formData
                        }
                    );


                /* --------------------------------------------
                   HANDLE ERROR
                   -------------------------------------------- */

                if (!response.ok) {

                    var errorData =
                        await response.json()
                            .catch(
                                function () {
                                    return null;
                                }
                            );


                    throw new Error(
                        errorData &&
                        errorData.detail

                            ? errorData.detail

                            : 'Decryption failed. HTTP ' +
                              response.status
                    );
                }


                /* --------------------------------------------
                   RECEIVE DECRYPTED FILE
                   -------------------------------------------- */

                var decryptedBlob =
                    await response.blob();


                var elapsed =
                    (
                        performance.now() -
                        start
                    ).toFixed(1);


                cryptoState.decrypted =
                    decryptedBlob;


                /* --------------------------------------------
                   VERIFY AGAINST ORIGINAL
                   -------------------------------------------- */

                var decryptedBuffer =
                    await decryptedBlob.arrayBuffer();


                var decryptedHash =
                    await sha256Hex(
                        decryptedBuffer
                    );


                var matches =
                    decryptedHash ===
                    fileState.originalHashHex;


                /* --------------------------------------------
                   DISPLAY RESULT
                   -------------------------------------------- */

                cryptoStatus.innerHTML +=

                    '<div class="crypto-result">' +

                        '<div class="crypto-result-row">' +
                            '<span>Decryption time</span>' +
                            '<b>' +
                                elapsed +
                                ' ms' +
                            '</b>' +
                        '</div>' +

                        '<div class="crypto-result-row">' +
                            '<span>Decryption</span>' +
                            '<b>Python backend</b>' +
                        '</div>' +

                        '<div class="verify-badge ' +
                            (
                                matches
                                    ? 'ok'
                                    : 'fail'
                            ) +
                        '">' +

                            (
                                matches

                                    ? 'Verified — matches the original file exactly'

                                    : 'Mismatch — differs from the original'
                            ) +

                        '</div>' +

                    '</div>' +

                    '<div class="crypto-actions-row">' +

                        '<button ' +
                            'class="button secondary crypto-btn" ' +
                            'id="downloadDecBtn" ' +
                            'type="button">' +

                            'Download Decrypted File' +

                        '</button>' +

                    '</div>';


                /* --------------------------------------------
                   DOWNLOAD DECRYPTED FILE
                   -------------------------------------------- */

                document
                    .getElementById(
                        'downloadDecBtn'
                    )
                    .addEventListener(
                        'click',
                        function () {

                            downloadBlob(
                                decryptedBlob,
                                fileState.file.name
                            );
                        }
                    );


                console.log(
                    'Decryption successful.'
                );

                console.log(
                    'Algorithm:',
                    algo
                );

                console.log(
                    'Files match:',
                    matches
                );


            }
            catch (err) {

                console.error(
                    'Decryption error:',
                    err
                );


                cryptoStatus.innerHTML +=
                    '<p class="crypto-note">' +
                    'Decryption failed: ' +
                    err.message +
                    '</p>';
            }


            finally {

                decryptBtn.disabled =
                    false;

                encryptBtn.disabled =
                    false;
            }
        }
    );
}


/* ============================================================
   NAVIGATION
   ============================================================ */

document.addEventListener(
    'DOMContentLoaded',
    function () {

        /* ====================================================
           MOBILE NAVIGATION
           ==================================================== */

        var navToggle =
            document.getElementById(
                'navToggle'
            );

        var navMobile =
            document.getElementById(
                'navMobile'
            );


        if (
            navToggle &&
            navMobile
        ) {

            navToggle.addEventListener(
                'click',
                function () {

                    var isOpen =
                        navMobile.classList.toggle(
                            'open'
                        );

                    navToggle.classList.toggle(
                        'open',
                        isOpen
                    );

                    navToggle.setAttribute(
                        'aria-expanded',
                        String(isOpen)
                    );
                }
            );


            Array.prototype.forEach.call(
                navMobile.querySelectorAll(
                    'a'
                ),
                function (link) {

                    link.addEventListener(
                        'click',
                        function () {

                            navMobile.classList.remove(
                                'open'
                            );

                            navToggle.classList.remove(
                                'open'
                            );

                            navToggle.setAttribute(
                                'aria-expanded',
                                'false'
                            );
                        }
                    );
                }
            );
        }


        /* ====================================================
           ACTIVE NAVIGATION LINK
           ==================================================== */

        var navLinks =
            Array.prototype.slice.call(
                document.querySelectorAll(
                    '.nav-links a, .nav-mobile a'
                )
            );


        var trackedIds = [
            'home',
            'how-it-works',
            'algorithms',
            'results',
            'demo'
        ];


        var trackedSections =
            trackedIds
                .map(
                    function (id) {
                        return document.getElementById(
                            id
                        );
                    }
                )
                .filter(Boolean);


        function updateActiveLink() {

            var scrollPos =
                window.scrollY + 100;


            var current =
                trackedSections.length
                    ? trackedSections[0].id
                    : null;


            trackedSections.forEach(
                function (sec) {

                    if (
                        sec.offsetTop <=
                        scrollPos
                    ) {

                        current =
                            sec.id;
                    }
                }
            );


            navLinks.forEach(
                function (link) {

                    link.classList.toggle(
                        'active',

                        link.getAttribute(
                            'href'
                        ) ===
                        '#' + current
                    );
                }
            );
        }

        
        window.addEventListener(
            'scroll',
            updateActiveLink,
            {
                passive: true
            }
        );


        updateActiveLink();


        /* ====================================================
           INITIALIZE WEBSITE
           ==================================================== */

        wireFileUpload();

        wireCrypto();
    }
);