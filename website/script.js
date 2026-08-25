function predictAlgorithm() {

    const dataType =
        document.getElementById("dataType").value;

    const fileSize =
        Number(document.getElementById("fileSize").value);

    const cpu =
        Number(document.getElementById("cpu").value);

    const battery =
        Number(document.getElementById("battery").value);

    let algorithm;
    let reason;


    if (fileSize > 16384) {

        algorithm = "ChaCha20";

        reason =
            "PRESENT is excluded for files larger than 16 MB.";

    } else if (battery < 25) {

        algorithm = "ChaCha20";

        reason =
            "The battery level is low, so performance and CPU cost are prioritized.";

    } else if (cpu > 70) {

        algorithm = "ChaCha20";

        reason =
            "The CPU usage is high, so an efficient algorithm is preferred.";

    } else if (
        dataType === "text" &&
        fileSize < 100
    ) {

        algorithm = "AES-256";

        reason =
            "AES-256 provides a strong security level for this context.";

    } else {

        algorithm = "ChaCha20";

        reason =
            "ChaCha20 provides a good balance between security and performance.";

    }


    document.getElementById(
        "predictionResult"
    ).textContent = algorithm;

    document.getElementById(
        "predictionReason"
    ).textContent = reason;

    document.getElementById(
        "prediction"
    ).classList.remove("hidden");
}