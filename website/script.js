async function predictAlgorithm() {
    // 1. Capture user inputs matching HTML IDs
    const dataType = document.getElementById("dataType").value;
    const fileSize = parseFloat(document.getElementById("fileSize").value) || 0;
    const cpu = parseFloat(document.getElementById("cpu").value) || 0;
    const battery = parseFloat(document.getElementById("battery").value) || 0;

    // 2. Get UI result elements
    const predictionBox = document.getElementById("prediction");
    const predictionResult = document.getElementById("predictionResult");
    const predictionReason = document.getElementById("predictionReason");

    // 3. Show loading status and unhide the prediction box
    predictionBox.classList.remove("hidden");
    predictionResult.innerText = "Calculating...";
    predictionReason.innerText = "Evaluating system metrics with ML model...";

    // 4. Construct request payload for FastAPI
    const payload = {
        file_type: dataType,
        file_size: fileSize,
        cpu_usage: cpu,
        battery_level: battery
    };

    try {
        // 5. Send POST request to your local Uvicorn server
        const response = await fetch("http://127.0.0.1:8000/predict", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `Server returned status ${response.status}`);
}

        const data = await response.json();

        // 6. Update the HTML card with the ML model's prediction
        predictionResult.innerText = data.recommended_algorithm;
        predictionReason.innerText = `Optimal algorithm for a ${fileSize} KB ${dataType} file at ${cpu}% CPU and ${battery}% battery.`;

    } catch (error) {
        console.error("Prediction Request Failed:", error);
        predictionResult.innerText = "Connection Error";
        predictionReason.innerText = "Unable to reach FastAPI server. Ensure uvicorn is running on port 8000.";
    }
}